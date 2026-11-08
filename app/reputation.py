"""Opt-in VirusTotal domain enrichment. Never submits URLs, files or page content."""

import asyncio
import ipaddress
import os
import re
import time
from collections import OrderedDict, deque
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit

import httpx

API_ROOT = "https://www.virustotal.com/api/v3/domains/"
ROOT = Path(__file__).resolve().parent.parent


def api_key() -> str:
    """Only this named key is read; no shell execution or general dotenv loader."""
    if "VIRUSTOTAL_API_KEY" in os.environ:
        return os.environ["VIRUSTOTAL_API_KEY"].strip()
    try:
        for line in (ROOT / ".env").read_text(encoding="utf8").splitlines():
            name, separator, value = line.strip().partition("=")
            if separator and name.strip() == "VIRUSTOTAL_API_KEY":
                return value.strip().strip("\"'")
    except OSError:
        pass
    return ""


def public_domain(origin: str | None) -> str | None:
    if not origin:
        return None
    try:
        domain = (
            urlsplit(origin).hostname.encode("idna").decode("ascii").lower().rstrip(".")
        )
        try:
            ipaddress.ip_address(domain)
            return None
        except ValueError:
            pass
        if len(domain) > 253 or "." not in domain:
            return None
        if not all(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part)
            for part in domain.split(".")
        ):
            return None
        reserved = (
            "localhost",
            "local",
            "internal",
            "corp",
            "home",
            "lan",
            "test",
            "invalid",
            "example",
            "onion",
            "arpa",
            "example.com",
            "example.net",
            "example.org",
        )
        if any(domain == name or domain.endswith("." + name) for name in reserved):
            return None
        return domain
    except (ValueError, AttributeError, UnicodeError):
        return None


def outcome(domain: str | None, status: str, **extra) -> dict:
    return {"domain": domain, "provider": "VirusTotal", "status": status, **extra}


class DomainReputation:
    def __init__(self):
        self.lock = Lock()
        self.cache = OrderedDict()
        self.pending = set()
        self.minute = deque()
        self.day = None
        self.daily_count = 0
        self.backoff_until = 0.0

    async def lookup(self, domain: str, key: str, client: httpx.AsyncClient) -> dict:
        now = time.monotonic()
        today = datetime.now(UTC).date()
        with self.lock:
            cached = self.cache.get(domain)
            if cached and cached[0] > now:
                self.cache.move_to_end(domain)
                return {**cached[1], "cached": True}
            if domain in self.pending:
                return outcome(domain, "pending")
            if today != self.day:
                self.day, self.daily_count = today, 0
            while self.minute and self.minute[0] <= now - 60:
                self.minute.popleft()
            if (
                now < self.backoff_until
                or len(self.minute) >= 4
                or self.daily_count >= 500
            ):
                return outcome(domain, "rate_limited")
            self.minute.append(now)
            self.daily_count += 1
            self.pending.add(domain)
        ttl = 60
        try:
            response = await client.get(API_ROOT + domain, headers={"x-apikey": key})
            if response.status_code == 429:
                with self.lock:
                    self.backoff_until = time.monotonic() + 60
                result = outcome(domain, "rate_limited")
            elif response.status_code == 404:
                result, ttl = outcome(domain, "unknown"), 900
            elif response.status_code != 200:
                result = outcome(domain, "unavailable")
            else:
                data = response.json()["data"]
                if (
                    data.get("type") != "domain"
                    or data.get("id", "").lower().rstrip(".") != domain
                ):
                    raise ValueError("Unexpected domain report")
                attrs = data["attributes"]
                stats = attrs["last_analysis_stats"]
                counts = {
                    name: stats.get(name, 0)
                    for name in (
                        "malicious",
                        "suspicious",
                        "harmless",
                        "undetected",
                        "timeout",
                    )
                }
                if any(
                    type(value) is not int or value < 0 or value > 100000
                    for value in counts.values()
                ):
                    raise ValueError("Invalid engine counts")
                stamp = attrs.get("last_analysis_date")
                if type(stamp) is not int or stamp <= 0 or stamp > time.time() + 300:
                    raise ValueError("Missing report date")
                stale = time.time() - stamp > 7 * 86400
                status = (
                    "malicious"
                    if counts["malicious"]
                    else "suspicious"
                    if counts["suspicious"]
                    else "stale"
                    if stale
                    else "no_reported_detections"
                    if counts["harmless"] + counts["undetected"]
                    else "unknown"
                )
                result = outcome(
                    domain,
                    status,
                    counts=counts,
                    analyzed_at=datetime.fromtimestamp(stamp, UTC).isoformat(),
                    stale=stale,
                    cached=False,
                )
                ttl = 900
        except (httpx.HTTPError, ValueError, KeyError, TypeError, OverflowError):
            result = outcome(domain, "unavailable")
        finally:
            with self.lock:
                self.pending.discard(domain)
        with self.lock:
            self.cache[domain] = (time.monotonic() + ttl, result)
            self.cache.move_to_end(domain)
            while len(self.cache) > 512:
                self.cache.popitem(last=False)
        return result

    async def enrich(self, snapshot, result: dict, enabled: bool) -> dict:
        if not enabled:
            result["reputation"] = {
                "enabled": False,
                "status": "disabled",
                "domains": [],
            }
            return result
        key = api_key()
        if not key:
            result["status"] = "partial"
            if not result["warning_count"]:
                result["verdict"] = "inconclusive"
            result["reputation"] = {
                "enabled": True,
                "status": "not_configured",
                "domains": [],
            }
            return result
        # Collector prioritizes the hovered link and rendered email before navigation chrome.
        links = [row.target_origin for row in snapshot.elements if row.kind == "link"]
        # Always include the page hostname near the front, even on a busy inbox.
        origins = links[:1] + [snapshot.page_origin] + links[1:]
        domains = list(
            dict.fromkeys(filter(None, (public_domain(value) for value in origins)))
        )
        # Bound work even on busy inboxes. Unqueried domains remain explicitly unchecked.
        async with httpx.AsyncClient(
            timeout=3.0, follow_redirects=False, trust_env=False
        ) as client:
            reports = await asyncio.gather(
                *(self.lookup(domain, key, client) for domain in domains[:16])
            )
        if len(domains) > 16:
            reports.extend(outcome(domain, "not_checked") for domain in domains[16:])
        by_domain = {row["domain"]: row for row in reports}
        existing = {row["element_id"]: row for row in result["warnings"]}
        for item in snapshot.elements:
            report = by_domain.get(public_domain(item.target_origin))
            if (
                item.kind not in {"link", "page"}
                or not report
                or report["status"] not in {"malicious", "suspicious"}
            ):
                continue
            label = report["status"]
            counts = report["counts"]
            evidence = f"VirusTotal reports {counts['malicious']} malicious and {counts['suspicious']} suspicious detections for {report['domain']}."
            evidence += (
                " The report is over seven days old."
                if report["stale"]
                else " Domain reputation does not verify this exact URL."
            )
            warning = existing.get(item.element_id)
            if warning:
                warning["rules"].append("virustotal-" + label)
                warning["evidence"] = [evidence, *warning["evidence"]][:3]
                warning["severity"] = (
                    "high" if label == "malicious" else warning["severity"]
                )
            else:
                warning = {
                    "element_id": item.element_id,
                    "severity": "high" if label == "malicious" else "medium",
                    "rules": ["virustotal-" + label],
                    "title": "This destination has reported threat detections",
                    "evidence": [evidence],
                    "next_step": "Do not follow this link. Verify through a trusted app or address.",
                }
                result["warnings"].append(warning)
                existing[item.element_id] = warning
        result["warning_count"] = len(result["warnings"])
        if result["warning_count"]:
            result["verdict"] = "warning"
        incomplete = not reports or any(
            row["status"] not in {"malicious", "suspicious", "no_reported_detections"}
            for row in reports
        )
        if incomplete and not result["warning_count"]:
            result["verdict"] = "inconclusive"
        if incomplete:
            result["status"] = "partial"
        result["reputation"] = {
            "enabled": True,
            "status": "no_public_domains"
            if not reports
            else "partial"
            if incomplete
            else "checked",
            "domains": reports,
        }
        return result


REPUTATION = DomainReputation()
