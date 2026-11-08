"""Synthetic text -> shipped browser collector -> actual Python rule assessment."""

import html
import json
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from app.page_guard import Snapshot, assess_snapshot

ROOT = Path(__file__).resolve().parent.parent
NITRO = """FREE 3 MONTHS OF DISCORD NITRO! We are giving away 500 FREE Nitro subscriptions to celebrate our community milestone! Claim your reward before the offer expires!
1. Visit our official-looking rewards portal.
2. Connect your Discord account.
3. Verify your account to unlock your Nitro gift."""

CRYPTO = """EXCLUSIVE CRYPTO GIVEAWAY! We are celebrating our 100K community milestone!
Send 0.05 ETH to our verified giveaway wallet and receive 0.5 ETH instantly.
10X YOUR CRYPTO IN MINUTES! Only 20 participants can join. The giveaway closes in 10 minutes!
Participate here: https://ethereum-bonus.example/rewards"""


@pytest.fixture(scope="module")
def collector():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.route(
            "https://lab.example.test/**",
            lambda route: route.fulfill(
                body="<html><body></body></html>", content_type="text/html"
            ),
        )
        page.goto("https://lab.example.test/")
        page.add_script_tag(
            content=(ROOT / "extension/scanner.js").read_text(encoding="utf8")
        )
        yield page
        browser.close()


@pytest.mark.parametrize(
    "text,rule",
    [
        (CRYPTO, "crypto-multiplier"),
        (NITRO, "reward-account-lure"),
        (
            "Only 50 prizes left! Claim your free reward before this offer expires.",
            "reward-pressure",
        ),
        (
            "Download this cracked game with free cheats and run the installer.",
            "software-bait",
        ),
        ("Disable antivirus protection to install this crack.", "disable-security"),
        (
            "Copy this into PowerShell and press enter to fix the problem.",
            "disable-security",
        ),
        (
            "Your files are encrypted. Pay 100 dollars to recover your files.",
            "ransom-demand",
        ),
        ("Guaranteed profits. Deposit 300 dollars now.", "investment-lure"),
        (
            "My love, trust me. It is an emergency. Send money today.",
            "relationship-payment-pressure",
        ),
        (
            "Your device is infected. I am support. Grant remote access now.",
            "remote-support-pressure",
        ),
        (
            "I will release your private photos unless you pay 100 dollars.",
            "private-image-extortion",
        ),
        ("Send money or I will dox you.", "coercive-threat"),
        (
            "Keep this secret from your parents. Move to private chat and send your address.",
            "secrecy-isolation",
        ),
        (
            "I am an administrator. Send your verification code to support.",
            "authority-sensitive-request",
        ),
        (
            "I am your daughter and I am in trouble. Send money urgently.",
            "emergency-identity-pressure",
        ),
        ("Pay a 50 dollar fee to unlock your prize.", "upfront-release-fee"),
    ],
)
def test_visible_combined_indicators(collector, text, rule):
    collector.set_content(
        '<div id="message-content-synthetic" class="messageContent_fixture">'
        + "".join("<p>" + html.escape(line) + "</p>" for line in text.splitlines())
        + '<p><a href="https://discord-nitro-gift.example/claim">Open portal</a></p></div>'
    )
    body = collector.evaluate("()=>TDefenseSnapshot.collect('manual').snapshot")
    result = assess_snapshot(Snapshot.model_validate(body))
    assert any(rule in row["rules"] for row in result["warnings"]), (rule, body)
    assert any(
        row["kind"] == "link" and rule in row["social_signals"]
        for row in body["elements"]
    )
    assert text not in json.dumps(body)
    assert result["verdict"] == "warning"


@pytest.mark.parametrize(
    "text",
    [
        "Free month of service. Read the terms.",
        "Connect your account in settings.",
        "This article explains ransomware, deepfakes and grooming. No action is needed.",
        "Never pay to recover encrypted files. Do not disable antivirus or download cracks.",
        "We offer software documentation and security training.",
    ],
)
def test_benign_and_cautionary_context_is_not_automatically_flagged(collector, text):
    collector.set_content(
        "<article><p>"
        + html.escape(text)
        + '</p><a href="https://docs.example.test">Read notice</a></article>'
    )
    body = collector.evaluate("()=>TDefenseSnapshot.collect('manual').snapshot")
    assert assess_snapshot(Snapshot.model_validate(body))["warning_count"] == 0


def test_unknown_social_flags_and_private_text_are_rejected():
    from tests.test_page_guard import post, snapshot

    body = snapshot(
        [
            {
                "element_id": "td_1",
                "kind": "message",
                "social_signals": ["arbitrary-user-command"],
            }
        ]
    )
    assert post(body).status_code == 422

    body = snapshot(
        [
            {
                "element_id": "td_1",
                "kind": "message",
                "social_signals": ["reward-account-lure"],
                "raw_text": NITRO,
            }
        ]
    )
    assert post(body).status_code == 422


def test_promotional_email_is_local_spam_caution_not_proven_fraud(collector):
    collector.set_content("""<section data-message-id="synthetic"><div class="a3s">
    <h2>Stop Overpaying for GLP-1 Medications</h2><p>Transparent pricing. Real results. Programs starting at $99.</p>
    <a href="https://offer.example/one">Get Started</a><a href="https://offer.example/two">Get Started</a><a href="https://offer.example/three">Get Started</a>
    <p>No Hidden Fees. Programs from $99/month.</p></div></section>""")
    body = collector.evaluate("()=>TDefenseSnapshot.collect('manual').snapshot")
    result = assess_snapshot(Snapshot.model_validate(body))
    assert result["warnings"] and all(
        row["category"] == "possible_spam" for row in result["warnings"]
    )
    assert all("promotional-email" in row["rules"] for row in result["warnings"])


def test_image_only_email_discloses_unread_content(collector):
    collector.set_content(
        """<div class="a3s"><a href="https://offer.example/promotion"><img src="data:image/png,synthetic" width="350" height="500"></a></div>"""
    )
    body = collector.evaluate("()=>TDefenseSnapshot.collect('manual').snapshot")
    result = assess_snapshot(Snapshot.model_validate(body))
    assert any("image-heavy-email" in row["rules"] for row in result["warnings"])
    assert any(
        "has not been read" in fact
        for row in result["warnings"]
        for fact in row["evidence"]
    )


def test_trusted_form_fingerprint_changes_with_associated_controls(collector):
    collector.set_content(
        """<form id="f" action="https://lab.example.test/save"><input type="text" name="field"><button>Save</button></form><input id="external" form="f" type="text"><button id="outside" form="f">Submit</button>"""
    )
    original = collector.evaluate(
        "async()=> (await TDefenseSnapshot.identity(document.querySelector('form'))).fingerprint"
    )
    for script in [
        "document.getElementById('external').placeholder='password'",
        "document.getElementById('external').type='password'",
        "document.getElementById('outside').setAttribute('formaction','http://other.example.test/submit')",
        "document.getElementById('external').disabled=true",
    ]:
        collector.evaluate(script)
        changed = collector.evaluate(
            "async()=> (await TDefenseSnapshot.identity(document.querySelector('form'))).fingerprint"
        )
        assert changed != original
        original = changed
    collector.evaluate(
        "document.getElementById('external').value='PRIVATE-TYPED-SECRET'"
    )
    assert (
        collector.evaluate(
            "async()=> (await TDefenseSnapshot.identity(document.querySelector('form'))).fingerprint"
        )
        == original
    )
