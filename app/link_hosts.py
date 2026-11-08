"""Small, explicit hostname cues, not a reputation or safety certification."""

import re
from urllib.parse import urlsplit

# Exact domains and their subdomains only. Do not exempt unrelated risks.
PAYPAL_DOMAINS = ("paypal.com", "paypal.me", "paypalobjects.com")
PAYPAL_LABEL = re.compile(r"^paypal(?:-|$)")


def brand_lookalike(origin: str | None) -> bool:
    if not origin:
        return False
    host = (urlsplit(origin).hostname or "").lower().rstrip(".")
    if any(host == domain or host.endswith("." + domain) for domain in PAYPAL_DOMAINS):
        return False
    # Match whole brand labels or brand-prefixed labels, not mentions in paths,
    # listing text, arbitrary substrings, or an unfamiliar TLD on its own.
    return any(PAYPAL_LABEL.match(label) for label in host.split("."))