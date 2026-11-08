"""Small host policy commands, safe through Windows PowerShell 5.1 native argv."""

import argparse
import ipaddress
import sys

from vm_kit.policy import public_ipv4, target_origin


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["origin", "route-overlaps", "public-ip"])
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()
    if args.action == "origin":
        print(target_origin(sys.stdin.read().strip()))
    elif args.action == "route-overlaps":
        print(
            ipaddress.ip_network(args.value, strict=False).overlaps(
                ipaddress.ip_network("192.168.253.0/30")
            )
        )
    else:
        address = ipaddress.ip_address(sys.stdin.read().strip())
        if not public_ipv4(address):
            raise ValueError("Public IPv4 address is required")
        print(address)


if __name__ == "__main__":
    main()
