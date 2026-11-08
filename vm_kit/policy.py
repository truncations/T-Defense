"""Public IPv4 egress policy; DNS answers are validated and numeric IPs are pinned."""

import ipaddress
import re
import socket
from urllib.parse import urlsplit


class PolicyError(ValueError):
    pass


def public_ipv4(address):
    return (
        address.version == 4
        and address.is_global
        and not any(
            (
                address.is_multicast,
                address.is_reserved,
                address.is_unspecified,
                address.is_loopback,
                address.is_link_local,
                address.is_private,
            )
        )
    )


def hostname(value):
    if (
        not isinstance(value, str)
        or len(value) > 253
        or any(c in value for c in "\\/@%?#\r\n\t ")
    ):
        raise PolicyError("Invalid hostname")
    try:
        name = value.encode("idna").decode("ascii").lower().rstrip(".")
    except UnicodeError as error:
        raise PolicyError("Invalid hostname") from error
    try:
        address = ipaddress.ip_address(name)
    except ValueError:
        if "." not in name or name.endswith(
            (
                ".local",
                ".localhost",
                ".internal",
                ".lan",
                ".home",
                ".test",
                ".example",
                ".invalid",
            )
        ):
            raise PolicyError("Only public website names are supported")
        if not all(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in name.split(".")
        ):
            raise PolicyError("Invalid hostname")
    else:
        if not public_ipv4(address):
            raise PolicyError("Only public IPv4 destinations are supported")
    return name


def target_origin(value):
    if (
        not isinstance(value, str)
        or len(value) > 2048
        or any(c in value for c in "\\\r\n\t")
    ):
        raise PolicyError("Invalid website origin")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise PolicyError("Invalid website origin") from error
    if (
        parsed.scheme not in ("http", "https")
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise PolicyError(
            "Use a public http(s) origin only, without path/query/login details"
        )
    host = hostname(parsed.hostname)
    expected = 443 if parsed.scheme == "https" else 80
    if port not in (None, expected):
        raise PolicyError("Only standard website ports are supported")
    return f"{parsed.scheme}://{host}"


class PublicPolicy:
    def __init__(self, denied=()):
        self.denied = tuple(
            ipaddress.ip_network(value, strict=False) for value in denied
        )

    def resolve(self, host, port):
        host = hostname(host)
        if port not in (80, 443):
            raise PolicyError("Port is not allowed")
        try:
            addresses = {
                row[4][0]
                for row in socket.getaddrinfo(
                    host, port, socket.AF_INET, socket.SOCK_STREAM
                )
            }
        except OSError as error:
            raise PolicyError("Public DNS lookup failed") from error
        if not addresses:
            raise PolicyError("No public IPv4 address")
        for value in addresses:
            ip = ipaddress.ip_address(value)
            if not public_ipv4(ip) or any(
                ip in network for network in self.denied if network.version == 4
            ):
                raise PolicyError("Destination is not permitted")
        return sorted(addresses)

    def connect(self, host, port):
        # Never resolve the hostname again at socket-connect time (DNS rebinding).
        for address in self.resolve(host, port):
            try:
                return socket.create_connection((address, port), timeout=5)
            except OSError:
                continue
        raise PolicyError("Public connection failed")
