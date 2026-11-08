"""Conservative local-demo URL policy shared by replay and future live adapter."""

from urllib.parse import urlsplit


def allowed_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        return (
            parsed.scheme == "http"
            and parsed.netloc in {"localhost:8000", "127.0.0.1:8000"}
            and parsed.path.startswith("/mock/")
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and not any(part in {".", ".."} for part in parsed.path.split("/"))
            and not any(char in url for char in ("\\", "%", "\n", "\r", "\t"))
        )
    except (ValueError, TypeError):
        return False
