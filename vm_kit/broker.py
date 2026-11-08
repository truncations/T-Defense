"""Authenticated, bounded egress broker. No TLS interception, page parsing or logs."""

import base64
import hmac
import json
import select
import socketserver
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

from vm_kit.explanations import validate_report
from vm_kit.policy import PolicyError, PublicPolicy, hostname

MAX_HEADERS = 16384
MAX_STREAM = 16 * 1024 * 1024


class Broker(socketserver.ThreadingTCPServer):
    allow_reuse_address = False
    daemon_threads = True

    def __init__(
        self, address, token, denied=(), lifetime=120, result_path=None, start_path=None
    ):
        self.result_path = Path(result_path) if result_path else None
        self.start_path = Path(start_path) if start_path else None
        self.result_lock = threading.Lock()
        self.token = token
        self.policy = PublicPolicy(denied)
        self.deadline = time.monotonic() + lifetime
        self.budget_lock = threading.Lock()
        self.remaining = 64 * 1024 * 1024
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(address, Handler)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        pass  # Never write untrusted URLs, headers, tokens or page bytes to logs.


class Handler(socketserver.StreamRequestHandler):
    def response(self, code):
        challenge = (
            'Proxy-Authenticate: Basic realm="T-Defense"\r\n'
            if code.startswith("407")
            else ""
        )
        self.wfile.write(
            f"HTTP/1.1 {code}\r\n{challenge}Content-Length: 0\r\nConnection: close\r\n\r\n".encode(
                "ascii"
            )
        )
        self.wfile.flush()

    def handle(self):
        self.connection.settimeout(5)
        try:
            self.inspect()
        except (OSError, ValueError, UnicodeError, PolicyError):
            try:
                self.response("403 Forbidden")
            except OSError:
                pass

    def inspect(self):
        line = self.rfile.readline(4097)
        if len(line) > 4096 or not line.endswith(b"\r\n"):
            raise PolicyError("Request line too long")
        method, target, version = line.decode("ascii").strip().split(" ")
        if any(ord(c) < 33 or ord(c) == 127 for c in target):
            raise PolicyError("Invalid target")
        if version not in ("HTTP/1.0", "HTTP/1.1"):
            raise PolicyError("Unsupported protocol")
        headers = {}
        size = len(line)
        for _ in range(80):
            if time.monotonic() >= self.server.deadline:
                raise PolicyError("Session expired")
            line = self.rfile.readline(4097)
            size += len(line)
            if len(line) > 4096 or size > MAX_HEADERS or not line.endswith(b"\r\n"):
                raise PolicyError("Header limit")
            if line == b"\r\n":
                break
            key, separator, value = line.decode("ascii").partition(":")
            if (
                not separator
                or key.lower() in headers
                or not key.replace("-", "").isalnum()
            ):
                raise PolicyError("Invalid or duplicate header")
            headers[key.lower()] = value.strip()
        else:
            raise PolicyError("Header count limit")
        expected = (
            "Basic "
            + base64.b64encode(("tdefense:" + self.server.token).encode()).decode()
        )
        if not hmac.compare_digest(headers.get("proxy-authorization", ""), expected):
            self.response("407 Proxy Authentication Required")
            return
        if time.monotonic() >= self.server.deadline:
            raise PolicyError("Session expired")
        if target == "/__tdefense_ready" and method == "GET":
            ready = bool(self.server.start_path and self.server.start_path.is_file())
            data = json.dumps({"ready": ready}).encode()
            self.wfile.write(
                f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(data)}\r\nConnection: close\r\n\r\n".encode()
                + data
            )
            self.wfile.flush()
        elif target == "/__tdefense_result" and method == "POST":
            if (
                "transfer-encoding" in headers
                or not headers.get("content-length", "").isascii()
                or not headers.get("content-length", "").isdigit()
            ):
                raise PolicyError("A bounded content length is required")
            length = int(headers["content-length"])
            if (
                not 1 <= length <= 65536
                or not self.server.result_path
                or not self.server.start_path
                or not self.server.start_path.is_file()
            ):
                raise PolicyError("Result not accepted")
            data = self.rfile.read(length)
            if len(data) != length:
                raise PolicyError("Incomplete result")
            report = validate_report(json.loads(data))
            with self.server.result_lock:
                if self.server.result_path.exists():
                    raise PolicyError("A result was already accepted")
                temporary = self.server.result_path.with_suffix(".part")
                with temporary.open("x", encoding="utf8") as output:
                    output.write(json.dumps(report))
                temporary.replace(self.server.result_path)
            self.response("201 Created")
        elif not self.server.start_path or not self.server.start_path.is_file():
            raise PolicyError("Host has not released egress")
        elif method == "CONNECT":
            host, separator, port = target.rpartition(":")
            if not separator or port != "443":
                raise PolicyError("Only HTTPS tunnels are allowed")
            host = hostname(host)
            upstream = self.server.policy.connect(host, 443)
            with upstream:
                self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                self.wfile.flush()
                self.relay(upstream)
        elif method in ("GET", "HEAD"):
            parsed = urlsplit(target)
            if (
                parsed.scheme != "http"
                or parsed.username
                or parsed.password
                or parsed.fragment
                or parsed.port not in (None, 80)
            ):
                raise PolicyError("Invalid plain HTTP request")
            host = hostname(parsed.hostname)
            upstream = self.server.policy.connect(host, 80)
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            forwarded = (
                f"{method} {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n"
            )
            for key in (
                "accept",
                "accept-language",
                "accept-encoding",
                "user-agent",
                "range",
            ):
                if key in headers:
                    forwarded += key + ": " + headers[key] + "\r\n"
            if (
                headers.get("content-length", "0") != "0"
                or "transfer-encoding" in headers
            ):
                raise PolicyError("Request bodies are not allowed")
            with upstream:
                upstream.sendall((forwarded + "\r\n").encode("ascii"))
                self.relay(upstream, response_only=True)
        else:
            raise PolicyError("HTTP method is not supported")

    def relay(self, upstream, response_only=False):
        # No TLS decoding: the VM/browser parses public-site content, not the host.
        deadline = min(self.server.deadline, time.monotonic() + 60)
        sockets = [upstream] if response_only else [self.connection, upstream]
        count = 0
        while time.monotonic() < deadline and count < MAX_STREAM:
            ready, _, _ = select.select(
                sockets, [], [], min(1, max(0, deadline - time.monotonic()))
            )
            for source in ready:
                data = source.recv(min(65536, MAX_STREAM - count))
                if not data:
                    return
                count += len(data)
                with self.server.budget_lock:
                    if len(data) > self.server.remaining:
                        return
                    self.server.remaining -= len(data)
                destination = self.connection if source is upstream else upstream
                destination.sendall(data)


def main():
    config = json.loads(sys.stdin.readline(8192))
    token = config["token"]
    if not isinstance(token, str) or len(token) < 32:
        raise ValueError("Invalid session token")
    address = config["bind"]
    # Binding is explicit; never listen on all physical interfaces.
    if address in ("0.0.0.0", "127.0.0.1", "::"):
        raise ValueError("Use the dedicated virtual-switch IPv4 address")
    with Broker(
        (address, 18080),
        token,
        config["denied"],
        lifetime=120,
        result_path=config["result_path"],
        start_path=config["start_path"],
    ) as broker:
        timer = threading.Timer(120, broker.shutdown)
        timer.daemon = True
        timer.start()
        broker.serve_forever(poll_interval=0.25)


if __name__ == "__main__":
    main()
