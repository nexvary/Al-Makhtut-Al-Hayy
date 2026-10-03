from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


class UnsafeSourceUrl(ValueError):
    pass


def validate_public_http_url(url: str) -> str:
    """Reject obvious SSRF targets before a remote source is queued.

    DNS resolution/rebinding protection belongs in the fetch proxy as a second layer.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeSourceUrl("Only http/https sources are allowed")
    if not parsed.hostname:
        raise UnsafeSourceUrl("Source URL has no hostname")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise UnsafeSourceUrl("Local hosts are not allowed")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return url

    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise UnsafeSourceUrl("Non-public IP addresses are not allowed")
    return url
