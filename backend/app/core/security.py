"""Security utilities and SSRF defense for repository URLs."""

import ipaddress
import re
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https", "git", "ssh"}

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def is_safe_repository_url(url: str) -> tuple[bool, str]:
    """Validates that a Git repository URL does not target internal subnets or local resources (SSRF defense)."""
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    url = url.strip()

    # Regex check for typical git/https URLs
    if not (url.startswith("https://") or url.startswith("http://") or url.startswith("git@")):
        return False, "URL must use https:// or git@"

    if url.startswith("git@"):
        # SSH git URL like git@github.com:user/repo.git
        match = re.match(r"^git@([a-zA-Z0-9.-]+):([\w.-]+)/([\w.-]+)(\.git)?$", url)
        if not match:
            return False, "Invalid SSH git URL format"
        hostname = match.group(1)
    else:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return False, f"Unsupported scheme: {parsed.scheme}"
        hostname = parsed.hostname
        if not hostname:
            return False, "URL does not contain a valid hostname"

    # Reject localhost / loopback directly
    if hostname.lower() in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        return False, "Access to localhost/loopback addresses is forbidden"

    # Resolve hostname to check if it points to private IP space
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            for blocked in BLOCKED_NETWORKS:
                if ip_obj in blocked:
                    return False, f"Host resolves to prohibited internal address: {ip_str}"
    except (socket.gaierror, ValueError):
        # In isolated testing environments or offline mode, allow github.com or gitlab.com
        if hostname.lower() in {"github.com", "gitlab.com", "bitbucket.org"}:
            return True, "Valid domain"
        return False, f"Failed to resolve hostname: {hostname}"

    return True, "URL is safe"
