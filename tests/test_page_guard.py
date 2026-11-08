from io import BytesIO
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from app.main import app

CLIENT = TestClient(app, base_url="http://localhost:8000", client=("127.0.0.1", 50000))
HEADERS = {
    "X-TDefense-Client": "a" * 32,
    "Origin": "chrome-extension://" + "a" * 32,
}


def snapshot(elements=None, page_origin="https://example.test"):
    elements = elements or []
    return {
        "page_origin": page_origin,
        "reason": "manual",
        "elements": elements,
        "coverage": {
            "elements_seen": len(elements),
            "elements_scanned": len(elements),
            "truncated": False,
            "frames_unchecked": 0,
        },
    }


def post(body, headers=None):
    return CLIENT.post(
        "/api/page/assess", json=body, headers=HEADERS if headers is None else headers
    )


def test_normal_https_login_is_not_automatically_phishing():
    row = {
        "element_id": "td_1",
        "kind": "form",
        "sensitive_fields": ["password"],
        "target_origin": "https://example.test",
    }
    data = post(snapshot([row])).json()
    assert (
        data["warning_count"] == 0 and data["verdict"] == "no_signs" and data["scan_id"]
    )


@pytest.mark.parametrize(
    "row,origin,rule",
    [
        (
            {
                "element_id": "td_1",
                "kind": "form",
                "sensitive_fields": ["password"],
                "target_origin": "http://example.test",
            },
            "http://example.test",
            "unencrypted-sensitive-form",
        ),
        (
            {
                "element_id": "td_1",
                "kind": "form",
                "sensitive_fields": ["payment"],
                "target_origin": "https://different.test",
            },
            "https://example.test",
            "different-form-origin",
        ),
        (
            {
                "element_id": "td_1",
                "kind": "message",
                "urgency": True,
                "sensitive_request": True,
                "has_link": True,
            },
            "https://example.test",
            "pressure-and-secrets",
        ),
        (
            {
                "element_id": "td_1",
                "kind": "link",
                "displayed_origin": "https://legitimate.test",
                "target_origin": "https://different.test",
            },
            "https://example.test",
            "misleading-link-address",
        ),
        (
            {
                "element_id": "td_1",
                "kind": "link",
                "download": True,
                "file_kind": "exe",
            },
            "https://example.test",
            "download-exe",
        ),
    ],
)
def test_actual_backend_rules(row, origin, rule):
    data = post(snapshot([row], origin)).json()
    assert data["warning_count"] == 1 and rule in data["warnings"][0]["rules"]


def test_authentication_and_origin_are_required():
    assert post(snapshot(), headers={}).status_code == 403
    assert (
        post(snapshot(), headers={**HEADERS, "Origin": "https://evil.test"}).status_code
        == 403
    )
    assert (
        post(
            snapshot(), headers={**HEADERS, "Host": "rebinding.example:8000"}
        ).status_code
        == 403
    )


@pytest.mark.parametrize("private", ["password_value", "raw_text", "html", "cookie"])
def test_private_content_fields_are_rejected(private):
    body = snapshot()
    body[private] = "PRIVATE-SENTINEL-DO-NOT-ECHO"
    response = post(body)
    assert response.status_code == 422
    assert "PRIVATE-SENTINEL" not in response.text


def test_full_paths_query_strings_and_duplicate_ids_are_rejected():
    assert (
        post(
            snapshot(page_origin="https://example.test/account?private=secret")
        ).status_code
        == 422
    )
    row = {"element_id": "td_1", "kind": "link"}
    assert post(snapshot([row, row])).status_code == 422


def test_partial_coverage_is_not_a_clean_page_claim():
    body = snapshot()
    body["coverage"]["frames_unchecked"] = 1
    assert post(body).json()["verdict"] == "inconclusive"


@pytest.mark.parametrize(
    "override",
    [
        {"Origin": "https://evil.test"},
        {"Origin": "chrome-extension://" + "c" * 32},
        {"Host": "evil.test:8000"},
        {"Origin": ""},
        {"X-TDefense-Client": "not-an-extension"},
    ],
)
def test_service_connects_automatically_only_for_the_extension(override):
    assert CLIENT.post("/api/extension/connect", headers=HEADERS).status_code == 200
    bad = {**HEADERS, **override}
    assert CLIENT.post("/api/extension/connect", headers=bad).status_code == 403
    assert post(snapshot(), bad).status_code == 403


def test_pairing_endpoints_are_gone():
    assert CLIENT.get("/api/extension/pairing").status_code in {404, 405}
    assert CLIENT.post("/api/extension/auto-pair", headers=HEADERS).status_code in {
        404,
        405,
    }


def test_payload_limit_and_no_browser_investigation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Real-page assessment must never launch or fetch destinations"
        )

    monkeypatch.setattr("app.investigator.investigate", forbidden)
    assert post(snapshot()).status_code == 200
    assert (
        CLIENT.post(
            "/api/page/assess", content=b"x" * 131073, headers=HEADERS
        ).status_code
        == 413
    )


def test_extension_bundle_contains_only_fixed_public_files():
    response = CLIENT.get("/api/extension/download")
    assert response.status_code == 200
    with ZipFile(BytesIO(response.content)) as bundle:
        assert "manifest.json" in bundle.namelist() and not any(
            name.startswith(".env") for name in bundle.namelist()
        )


def test_provider_configuration_exposes_only_readiness(monkeypatch):
    monkeypatch.setenv("VIRUSTOTAL_API_KEY", "PRIVATE-CONFIG-KEY-SENTINEL")
    response = CLIENT.get("/api/extension/config")
    assert response.json() == {"virustotal_configured": True}
    assert response.headers["cache-control"] == "no-store"
    assert "PRIVATE-CONFIG" not in response.text
    assert (
        CLIENT.get(
            "/api/extension/config", headers={"Host": "evil.test:8000"}
        ).status_code
        == 403
    )
