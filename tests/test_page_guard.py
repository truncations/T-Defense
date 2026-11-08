from io import BytesIO
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from app import page_guard
from app.main import app

CLIENT = TestClient(app, base_url="http://localhost:8000", client=("127.0.0.1", 50000))
HEADERS = {
    "X-TDefense-Key": page_guard.PAIR_KEY,
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


def test_pairing_is_loopback_same_origin_and_not_cached():
    response = CLIENT.get(
        "/api/extension/pairing", headers={"Sec-Fetch-Site": "same-origin"}
    )
    assert (
        response.status_code == 200 and response.headers["cache-control"] == "no-store"
    )
    assert response.json()["pairing_code"] == page_guard.PAIR_KEY
    assert (
        CLIENT.get(
            "/api/extension/pairing", headers={"Sec-Fetch-Site": "cross-site"}
        ).status_code
        == 403
    )
    assert (
        CLIENT.get(
            "/api/extension/pairing", headers={"Host": "evil.test:8000"}
        ).status_code
        == 403
    )


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
        assert all(
            page_guard.PAIR_KEY.encode() not in bundle.read(name)
            for name in bundle.namelist()
        )
