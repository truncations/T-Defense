import asyncio
import time

import httpx
import pytest

from app import page_guard, reputation
from tests.test_page_guard import CLIENT, HEADERS, snapshot


def report(domain, malicious=2, suspicious=1, stamp=None):
    return {
        "data": {
            "type": "domain",
            "id": domain,
            "attributes": {
                "last_analysis_date": int(time.time()) if stamp is None else stamp,
                "last_analysis_stats": {
                    "malicious": malicious,
                    "suspicious": suspicious,
                    "harmless": 40,
                    "undetected": 20,
                },
            },
        }
    }


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:8000",
        "https://account.test",
        "https://example.com",
        "https://127.0.0.1",
        "https://[::1]",
        "https://router.local",
        "https://printer.internal",
        "https://x.onion",
    ],
)
def test_private_reserved_and_ip_destinations_never_leave(origin):
    assert reputation.public_domain(origin) is None


def test_domain_normalization():
    assert (
        reputation.public_domain("https://WWW.Public-Sample.COM:443")
        == "www.public-sample.com"
    )
    assert reputation.public_domain("https://bad-label-.com") is None


def test_provider_cache_budgets_and_fixed_destination():
    seen = []

    def handler(request):
        seen.append(request)
        assert request.url.host == "www.virustotal.com"
        assert (
            request.method == "GET" and not request.url.query and request.content == b""
        )
        assert request.headers["x-apikey"] == "fake-unit-key"
        return httpx.Response(200, json=report(request.url.path.split("/")[-1]))

    async def exercise():
        service = reputation.DomainReputation()
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            first = await service.lookup("public-sample.com", "fake-unit-key", client)
            again = await service.lookup("public-sample.com", "fake-unit-key", client)
            assert first["status"] == "malicious" and again["cached"] is True
            for i in range(3):
                await service.lookup(f"sample-{i}.com", "fake-unit-key", client)
            assert (await service.lookup("fifth-sample.com", "fake-unit-key", client))[
                "status"
            ] == "rate_limited"
        assert len(seen) == 4

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "status,payload,expected",
    [
        (404, {}, "unknown"),
        (429, {}, "rate_limited"),
        (403, {}, "unavailable"),
        (200, {}, "unavailable"),
        (200, report("different-sample.com"), "unavailable"),
        (200, report("public-sample.com", 0, 0), "no_reported_detections"),
        (200, report("public-sample.com", 0, 0, int(time.time()) - 9 * 86400), "stale"),
    ],
)
def test_honest_provider_outcomes(status, payload, expected):
    async def exercise():
        service = reputation.DomainReputation()
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(status, json=payload)
            )
        ) as client:
            result = await service.lookup("public-sample.com", "fake-unit-key", client)
            assert result["status"] == expected and "fake-unit-key" not in str(result)

    asyncio.run(exercise())


def test_disabled_and_missing_key_make_no_provider_requests(monkeypatch):
    monkeypatch.setattr(reputation, "api_key", lambda: "")
    calls = []

    async def forbidden(*args):
        calls.append(args)
        raise AssertionError("Provider must not be contacted")

    monkeypatch.setattr(reputation.REPUTATION, "lookup", forbidden)
    assert (
        CLIENT.post("/api/page/assess", headers=HEADERS, json=snapshot()).json()[
            "reputation"
        ]["status"]
        == "disabled"
    )
    result = CLIENT.post(
        "/api/page/assess",
        headers={**HEADERS, "X-TDefense-Reputation": "enabled"},
        json=snapshot(),
    ).json()
    assert result["reputation"]["status"] == "not_configured" and not calls
    assert result["verdict"] == "inconclusive" and result["status"] == "partial"


def test_all_timeouts_are_not_a_negative_detection_report():
    payload = report("public-sample.com", 0, 0)
    payload["data"]["attributes"]["last_analysis_stats"] = {"timeout": 40}

    async def exercise():
        service = reputation.DomainReputation()
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=payload)
            )
        ) as client:
            assert (await service.lookup("public-sample.com", "fake-unit-key", client))[
                "status"
            ] == "unknown"

    asyncio.run(exercise())


def test_reputation_merges_link_and_current_page_findings(monkeypatch):
    monkeypatch.setattr(reputation, "api_key", lambda: "fake-unit-key")
    service = reputation.DomainReputation()

    async def fake_lookup(domain, key, client):
        return reputation.outcome(
            domain,
            "malicious",
            counts={"malicious": 3, "suspicious": 1},
            stale=False,
            analyzed_at="2026-11-07T00:00:00+00:00",
        )

    monkeypatch.setattr(service, "lookup", fake_lookup)
    body = snapshot(
        [
            {
                "element_id": "td_1",
                "kind": "link",
                "target_origin": "https://public-sample.com",
            },
            {
                "element_id": "td_2",
                "kind": "page",
                "target_origin": "https://public-page.com",
            },
        ],
        "https://public-page.com",
    )
    data = asyncio.run(
        service.enrich(
            page_guard.Snapshot.model_validate(body),
            page_guard.assess_snapshot(page_guard.Snapshot.model_validate(body)),
            True,
        )
    )
    assert data["warning_count"] == 2 and data["verdict"] == "warning"
    assert all(
        "virustotal-malicious" in warning["rules"] for warning in data["warnings"]
    )


def test_daily_cap_and_capped_cache():
    async def exercise():
        service = reputation.DomainReputation()
        from datetime import UTC, datetime

        service.day = datetime.now(UTC).date()
        service.daily_count = 500
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: pytest.fail("Daily budget must stop requests")
            )
        ) as client:
            assert (await service.lookup("public-sample.com", "fake-unit-key", client))[
                "status"
            ] == "rate_limited"

    asyncio.run(exercise())


def test_page_hostname_is_not_crowded_out_by_many_links(monkeypatch):
    monkeypatch.setattr(reputation, "api_key", lambda: "fake-unit-key")
    service = reputation.DomainReputation()
    requested = []

    async def lookup(domain, key, client):
        requested.append(domain)
        return reputation.outcome(domain, "unknown")

    monkeypatch.setattr(service, "lookup", lookup)
    body = snapshot(
        [
            {
                "element_id": f"td_{i}",
                "kind": "link",
                "target_origin": f"https://public-link-{i}.com",
            }
            for i in range(20)
        ],
        "https://public-page.com",
    )
    model = page_guard.Snapshot.model_validate(body)
    asyncio.run(service.enrich(model, page_guard.assess_snapshot(model), True))
    assert requested[:2] == ["public-link-0.com", "public-page.com"]
    assert len(requested) == 16
