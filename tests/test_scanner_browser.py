"""Exercise the shipped collector on synthetic HTTPS HTML, without real sites."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.page_guard import Snapshot, assess_snapshot

ROOT = Path(__file__).resolve().parent.parent


def test_submitter_overrides_external_fields_and_shadow_coverage():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.route(
            "https://lumora.example.test/**",
            lambda route: route.fulfill(
                content_type="text/html",
                body="""<!doctype html><html><body>
            <form id="login" action="/login"><button formaction="http://other.example.test/submit">Confirm</button></form>
            <input form="login" type="password" value="PRIVATE-TYPED-SENTINEL">
            <a href="/normal">Normal link</a></body></html>""",
            ),
        )
        page.goto("https://lumora.example.test/")
        page.add_script_tag(
            content=(ROOT / "extension/scanner.js").read_text(encoding="utf8")
        )
        snapshot = page.evaluate("() => TDefenseSnapshot.collect('manual').snapshot")
        form = next(item for item in snapshot["elements"] if item["kind"] == "form")
        assert form["sensitive_fields"] == ["password"]
        assert form["target_origin"] == "http://other.example.test"
        assert "PRIVATE-TYPED-SENTINEL" not in json.dumps(snapshot)
        result = assess_snapshot(Snapshot.model_validate(snapshot))
        assert "unencrypted-sensitive-form" in result["warnings"][0]["rules"]
        assert "different-form-origin" in result["warnings"][0]["rules"]
        page.evaluate("""() => {for(let i=0;i<14;i++){
          const host=document.createElement('div');document.body.append(host);
          const shadow=host.attachShadow({mode:'open'});
          if(i===0)shadow.append(document.createElement('iframe'));
        }}""")
        coverage = page.evaluate(
            "() => TDefenseSnapshot.collect('manual').snapshot.coverage"
        )
        assert coverage["truncated"] is True
        assert coverage["frames_unchecked"] == 1
        browser.close()
