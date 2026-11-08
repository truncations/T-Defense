"""Real-page structural assessment. Never fetches URLs or accepts page/form text."""

import json
import re
import secrets
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Literal
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from app.link_hosts import brand_lookalike
from app.reputation import REPUTATION, api_key
from app.social_rules import SOCIAL_RULES, SPAM_SIGNALS

router = APIRouter()
PAIR_KEY = secrets.token_urlsafe(32)
LOCK = Lock()
STATS = {"processed_scans": 0, "warning_findings": 0, "last_scan_at": None}
CLIENT_ID = re.compile(r"[a-p]{32}")
APPROVAL_FILE = (
    Path(__file__).resolve().parent.parent / "work" / "approved_extensions.json"
)
PENDING_CLIENTS = {}
SESSION_KEYS = {}


def approved_clients():
    try:
        rows = json.loads(APPROVAL_FILE.read_text())
        return [
            row for row in rows if isinstance(row, str) and CLIENT_ID.fullmatch(row)
        ][:32]
    except (OSError, ValueError, TypeError):
        return []


LOCAL_HOSTS = {"localhost:8000", "127.0.0.1:8000"}


def origin_only(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Only HTTP(S) origins are accepted")
    if any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError("Invalid origin")
    _ = parsed.port
    return parsed.scheme + "://" + parsed.netloc.lower()


class Signal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    element_id: str = Field(pattern=r"^td_[0-9]+$", max_length=32)
    kind: Literal["form", "link", "message", "page"]
    target_origin: str | None = Field(default=None, max_length=300)
    displayed_origin: str | None = Field(default=None, max_length=300)
    sensitive_fields: list[
        Literal["password", "payment", "otp", "identity", "gift_card"]
    ] = Field(default_factory=list, max_length=5)
    urgency: bool = False
    sensitive_request: bool = False
    gift_code_request: bool = False
    has_link: bool = False
    email_context: bool = False
    account_action: bool = False
    wrapped_destination: bool = False
    social_signals: list[
        Literal[
            "mail-spam-folder",
            "crypto-multiplier",
            "promotional-email",
            "image-heavy-email",
            "reward-account-lure",
            "reward-pressure",
            "software-bait",
            "disable-security",
            "ransom-demand",
            "investment-lure",
            "relationship-payment-pressure",
            "remote-support-pressure",
            "private-image-extortion",
            "coercive-threat",
            "secrecy-isolation",
            "authority-sensitive-request",
            "emergency-identity-pressure",
            "upfront-release-fee",
        ]
    ] = Field(default_factory=list, max_length=18)
    download: bool = False
    file_kind: Literal[
        "exe",
        "msi",
        "scr",
        "bat",
        "cmd",
        "ps1",
        "js",
        "vbs",
        "jar",
        "apk",
        "dmg",
        "iso",
        "zip",
        "other",
    ] = "other"
    target_scheme: Literal["http", "https", "data", "blob", "javascript", "other"] = (
        "other"
    )

    @field_validator("target_origin", "displayed_origin")
    @classmethod
    def validate_origin(cls, value):
        return origin_only(value)


class Coverage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    elements_seen: int = Field(ge=0, le=100000)
    elements_scanned: int = Field(ge=0, le=200)
    truncated: bool = False
    trusted_skipped: int = Field(default=0, ge=0, le=200)
    frames_unchecked: int = Field(default=0, ge=0, le=10000)


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    page_origin: str = Field(max_length=300)
    reason: Literal[
        "initial", "mutation", "periodic", "manual", "interaction", "visible"
    ]
    elements: list[Signal] = Field(max_length=200)
    coverage: Coverage

    @field_validator("page_origin")
    @classmethod
    def validate_origin(cls, value):
        return origin_only(value)

    @model_validator(mode="after")
    def unique_and_complete(self):
        if len({row.element_id for row in self.elements}) != len(self.elements):
            raise ValueError("Duplicate element IDs")
        if (
            self.coverage.elements_scanned != len(self.elements)
            or self.coverage.elements_seen < self.coverage.elements_scanned
        ):
            raise ValueError("Inconsistent coverage")
        return self


def assess_snapshot(snapshot: Snapshot) -> dict:
    warnings = []
    for item in snapshot.elements:
        facts = []
        rules = []
        severity = "low"
        social_title = None
        social_step = None
        social_level = -1

        def add(rule, fact, level, rules=rules, facts=facts):
            nonlocal severity
            rules.append(rule)
            facts.append(fact)
            if {"low": 0, "medium": 1, "high": 2}[level] > {
                "low": 0,
                "medium": 1,
                "high": 2,
            }[severity]:
                severity = level

        if item.kind == "form" and item.sensitive_fields:
            if snapshot.page_origin.startswith("http:") or (
                item.target_origin or ""
            ).startswith("http:"):
                add(
                    "unencrypted-sensitive-form",
                    "This form requests sensitive information over an unencrypted connection.",
                    "high",
                )
            if item.target_origin and item.target_origin != snapshot.page_origin:
                add(
                    "different-form-origin",
                    "This form sends information to a different site address. Verify that destination.",
                    "medium",
                )
        if item.kind == "link" and brand_lookalike(item.target_origin):
            add(
                "brand-lookalike-host",
                "The destination uses a PayPal-like hostname outside the recognized PayPal domains. It may be unrelated or misleading; this is not proof of fraud. Verify the address independently before following it.",
                "medium",
            )
        if item.displayed_origin and item.target_origin:
            shown = urlsplit(item.displayed_origin).hostname.removeprefix("www.")
            target = urlsplit(item.target_origin).hostname.removeprefix("www.")
            if shown != target:
                add(
                    "misleading-link-address",
                    "The link's displayed website differs from its actual destination.",
                    "medium",
                )
        if item.urgency and item.sensitive_request:
            add(
                "pressure-and-secrets",
                "This content uses pressure while requesting a password, payment detail, or code.",
                "high",
            )
        elif item.urgency and item.has_link and item.kind == "message":
            add(
                "pressure-and-link",
                "A newly observed message uses urgency and includes a link. Pause before following it.",
                "low",
            )
        if item.gift_code_request:
            add(
                "gift-card-code-request",
                "This content asks for gift-card codes or PINs. Verify the request independently.",
                "high",
            )
        if item.email_context and item.account_action and item.has_link:
            add(
                "email-account-action",
                "This email asks you to act on an account through a link. Verify the destination independently; legitimate emails can do this too.",
                "low",
            )
        if item.download:
            if item.file_kind != "other":
                add(
                    "download-" + item.file_kind,
                    "This link may download a "
                    + item.file_kind.upper()
                    + " file. Its contents have not been scanned.",
                    "medium" if item.file_kind != "zip" else "low",
                )
            else:
                add(
                    "unscanned-attachment",
                    "This link offers an attachment. T-Defense has not scanned its contents.",
                    "low",
                )
        if item.target_scheme == "data":
            add(
                "embedded-document-link",
                "This link contains embedded content instead of a normal website address.",
                "medium",
            )
        for signal in dict.fromkeys(item.social_signals):
            level, title, fact, step, requires_link = SOCIAL_RULES[signal]
            if requires_link and not item.has_link:
                continue
            add(signal, fact, level)
            if {"low": 0, "medium": 1, "high": 2}[level] > social_level:
                social_title, social_step = title, step
                social_level = {"low": 0, "medium": 1, "high": 2}[level]
        if rules:
            warnings.append(
                {
                    "element_id": item.element_id,
                    "severity": severity,
                    "category": "possible_spam"
                    if set(rules) <= SPAM_SIGNALS
                    else "security_risk",
                    "rules": rules,
                    "title": social_title
                    or (
                        "Pause before sharing information"
                        if item.kind == "form"
                        else "Check this message or link"
                    ),
                    "evidence": facts[-3:] if social_title else facts[:3],
                    "next_step": social_step
                    or "Keep attachments closed and do not enter passwords, card details, or codes until you verify independently.",
                }
            )
    partial = snapshot.coverage.truncated or snapshot.coverage.frames_unchecked > 0
    stamp = datetime.now(UTC).isoformat(timespec="seconds")
    return {
        "scan_id": "pg_" + secrets.token_urlsafe(10),
        "scanned_at": stamp,
        "engine": "live structural rules — provided classifier not integrated",
        "warning_count": len(warnings),
        "warnings": warnings,
        "status": "partial" if partial else "checked",
        "verdict": "warning" if warnings else "inconclusive" if partial else "no_signs",
        "coverage": snapshot.coverage.model_dump(),
        "unknowns": [
            "These rules can miss phishing and can flag legitimate requests.",
            "Form values, typed text, passwords and message contents are not sent to the backend.",
            "Closed shadow trees and embedded frames are not inspected; attachments are not opened or scanned.",
        ],
    }


def local_host(request: Request):
    if request.headers.get("host", "").lower() not in LOCAL_HOSTS:
        raise HTTPException(403, "Use the loopback backend address on port8000.")


def authorize(request: Request):
    local_host(request)
    key = request.headers.get("x-tdefense-key", "")
    client = request.headers.get("x-tdefense-client", "")
    origin = request.headers.get("origin", "")
    with LOCK:
        valid_session = (
            client in approved_clients()
            and client in SESSION_KEYS
            and secrets.compare_digest(key, SESSION_KEYS[client])
        )
        valid_key = secrets.compare_digest(key, PAIR_KEY) or valid_session
    if (
        not CLIENT_ID.fullmatch(client)
        or (origin and origin != "chrome-extension://" + client)
        or not valid_key
    ):
        raise HTTPException(
            403, "Pair the extension with the current local backend session."
        )


@router.get("/api/extension/pairing")
def pairing(request: Request):
    local_host(request)
    if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(403, "Pair only from this computer.")
    if request.headers.get("sec-fetch-site") not in {None, "same-origin", "none"}:
        raise HTTPException(403, "Open the local setup page directly.")
    origin = request.headers.get("origin")
    if origin and origin not in {"http://localhost:8000", "http://127.0.0.1:8000"}:
        raise HTTPException(403, "Open the local setup page directly.")
    return JSONResponse(
        {"pairing_code": PAIR_KEY},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


def setup_authorize(request: Request):
    pairing(request)
    if not secrets.compare_digest(
        request.headers.get("x-tdefense-setup", ""), PAIR_KEY
    ):
        raise HTTPException(403, "Open local setup to approve this installation.")


@router.post("/api/extension/auto-pair")
def auto_pair(request: Request):
    local_host(request)
    client = request.headers.get("x-tdefense-client", "")
    if (
        request.client is None
        or request.client.host not in {"127.0.0.1", "::1"}
        or not CLIENT_ID.fullmatch(client)
        or request.headers.get("origin") != "chrome-extension://" + client
    ):
        raise HTTPException(403, "Use the genuine extension on this computer.")
    with LOCK:
        if client not in approved_clients():
            if len(PENDING_CLIENTS) >= 32 and client not in PENDING_CLIENTS:
                raise HTTPException(429, "Too many pending installation requests.")
            PENDING_CLIENTS[client] = True
            return JSONResponse(
                {"approval_required": True}, headers={"Cache-Control": "no-store"}
            )
        key = SESSION_KEYS.setdefault(client, secrets.token_urlsafe(32))
    return JSONResponse({"pairing_code": key}, headers={"Cache-Control": "no-store"})


@router.get("/api/extension/installations")
def installations(request: Request):
    setup_authorize(request)
    with LOCK:
        return JSONResponse(
            {"pending": list(PENDING_CLIENTS), "approved": approved_clients()},
            headers={"Cache-Control": "no-store"},
        )


class InstallationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str = Field(pattern=r"^[a-p]{32}$")
    approve: bool


@router.post("/api/extension/installations")
def decide_installation(decision: InstallationDecision, request: Request):
    setup_authorize(request)
    with LOCK:
        approved = approved_clients()
        if decision.approve:
            if decision.client_id not in PENDING_CLIENTS:
                raise HTTPException(409, "Request pairing from this extension first.")
            if decision.client_id not in approved:
                if len(approved) >= 32:
                    raise HTTPException(
                        409, "Revoke an installation before approving another."
                    )
                approved.append(decision.client_id)
        else:
            approved = [row for row in approved if row != decision.client_id]
            SESSION_KEYS.pop(decision.client_id, None)
        APPROVAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary = APPROVAL_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(approved))
        temporary.replace(APPROVAL_FILE)
        PENDING_CLIENTS.pop(decision.client_id, None)
    return {"ok": True}


@router.post("/api/extension/connect")
def connect(request: Request):
    authorize(request)
    return {
        "connected": True,
        "engine": "live structural rules",
        "stores_page_content": False,
    }


@router.get("/api/extension/stats")
def stats(request: Request):
    local_host(request)
    with LOCK:
        return dict(STATS)


@router.get("/api/extension/config")
def extension_config(request: Request):
    local_host(request)
    return JSONResponse(
        {"virustotal_configured": bool(api_key())},
        headers={"Cache-Control": "no-store"},
    )


@router.post("/api/page/assess")
async def assess_page(request: Request):
    authorize(request)
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 131072:
            raise HTTPException(413, "Page signal snapshot is too large.")
        chunks.append(chunk)
    try:
        snapshot = Snapshot.model_validate_json(b"".join(chunks))
    except ValidationError as error:
        raise HTTPException(
            422,
            "Invalid structural signal snapshot; page text and form values are not accepted.",
        ) from error
    result = assess_snapshot(snapshot)
    result = await REPUTATION.enrich(
        snapshot, result, request.headers.get("x-tdefense-reputation") == "enabled"
    )
    # Reject an installation revoked during optional reputation work.
    authorize(request)
    with LOCK:
        STATS["processed_scans"] += 1
        STATS["warning_findings"] += result["warning_count"]
        STATS["last_scan_at"] = result["scanned_at"]
    return JSONResponse(result, headers={"Cache-Control": "no-store"})


@router.get("/api/extension/download")
def download_extension(request: Request):
    local_host(request)
    directory = Path(__file__).resolve().parent.parent / "extension"
    names = [
        "manifest.json",
        "bootstrap.js",
        "trust.js",
        "scanner.js",
        "background.js",
        "content.js",
        "popup.html",
        "popup.css",
        "popup.js",
        "README.md",
    ]
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as bundle:
        for name in names:
            path = directory / name
            if not path.is_file():
                raise HTTPException(503, "Extension bundle is still being prepared.")
            bundle.writestr(name, path.read_bytes())
    return Response(
        buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="T-Defense-extension.zip"',
            "Cache-Control": "no-store",
        },
    )
