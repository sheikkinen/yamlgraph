"""Input-boundary helpers for the LAN recon skill (FR-945, REQ-YG-635).

Everything here operates on caller-provided strings BEFORE any network
call, credential use, or file write. Each helper raises a typed
`ReconError` subclass rather than returning a magic value; see
`errors.py` for the exception hierarchy.
"""

import ipaddress
import os
import re
import socket

from .errors import (
    MissingComputerNameError,
    MissingCredentialError,
    QualifiedUserError,
    UnresolvableTargetError,
    UnsafeSlugError,
    UnsafeTargetError,
)

# Windows computer-name rules: 1-15 chars, alphanumeric + hyphen, not
# all-numeric. Matches the DNS-label -> COMPUTERNAME derivation.
_COMPUTERNAME_RE = re.compile(r"^[A-Za-z0-9-]{1,15}$")
_ALL_DIGITS_RE = re.compile(r"^\d+$")

# Safe-slug for output filenames.
_SLUG_KEEP = re.compile(r"[^a-z0-9._-]+")


def load_credentials() -> tuple[str, str]:
    """Read LAN_RECON_USER / LAN_RECON_PASS from env. Refuse if missing.

    Bare local-account names only in v1; qualified/domain-shaped values
    are refused so recon owns the qualification (as ``<COMPUTERNAME>\\<user>``).
    """
    user = os.environ.get("LAN_RECON_USER", "")
    passwd = os.environ.get("LAN_RECON_PASS", "")
    if not user:
        raise MissingCredentialError(
            "LAN_RECON_USER not set. Add it to .env or export before running."
        )
    if not passwd:
        raise MissingCredentialError(
            "LAN_RECON_PASS not set. Add it to .env or export before running."
        )
    if any(sep in user for sep in ("\\", "/", "@")):
        raise QualifiedUserError(
            f"LAN_RECON_USER={user!r} looks qualified (contains \\, /, or @). "
            "v1 supports only bare local-account names; recon qualifies as "
            "<COMPUTERNAME>\\<user> internally."
        )
    return user, passwd


def validate_target_shape(target: str) -> None:
    """Cheap syntactic guard that runs BEFORE DNS resolution and slug derivation.

    Blocks path separators, null bytes, empty, and traversal tokens so
    an unsafe argument cannot reach ``getaddrinfo`` (which raises
    confusing IDNA errors) or the safe-slug logic (which then can't
    tell it apart from a legitimate name).
    """
    if not target or target in {".", ".."}:
        raise UnsafeSlugError(f"target {target!r} is empty or path traversal.")
    if any(ch in target for ch in ("/", "\\", "\x00")):
        raise UnsafeSlugError(f"target {target!r} contains path separator or null.")


def select_computer_name(target: str, override: str | None) -> str:
    """Return the selected Windows COMPUTERNAME.

    IP literal target -> requires --computer-name.
    DNS name -> derive from leftmost label if it matches Windows rules;
    otherwise require --computer-name.
    """
    if override:
        if not _COMPUTERNAME_RE.match(override):
            raise MissingComputerNameError(
                f"--computer-name={override!r} is not a valid Windows computer name "
                "(1-15 alphanumeric + hyphen)."
            )
        return override.upper()

    try:
        ipaddress.ip_address(target)
    except ValueError:
        pass
    else:
        raise MissingComputerNameError(
            f"target {target!r} is an IP literal; pass --computer-name <NAME>."
        )

    label = target.split(".", 1)[0]
    if not _COMPUTERNAME_RE.match(label) or _ALL_DIGITS_RE.match(label):
        raise MissingComputerNameError(
            f"cannot derive Windows COMPUTERNAME from {target!r}; "
            "pass --computer-name <NAME>."
        )
    return label.upper()


def resolve_target(target: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Resolve target to a single pinned address. Refuse non-LAN addresses.

    Accepts only RFC1918 / CGN 100.64.0.0/10 / IPv4 link-local /
    IPv6 ULA / IPv6 link-local. Rejects loopback, multicast, unspecified,
    and everything else.
    """
    try:
        addr = ipaddress.ip_address(target)
    except ValueError:
        try:
            infos = socket.getaddrinfo(target, None, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            raise UnresolvableTargetError(f"cannot resolve {target!r}: {exc}") from exc
        if not infos:
            raise UnresolvableTargetError(
                f"cannot resolve {target!r}: no addresses"
            ) from None
        addr_str = next(
            (a[4][0] for a in infos if a[0] == socket.AF_INET),
            infos[0][4][0],
        )
        try:
            addr = ipaddress.ip_address(addr_str)
        except ValueError as exc:
            raise UnresolvableTargetError(
                f"resolved {target!r} to non-IP {addr_str!r}: {exc}"
            ) from exc

    if addr.is_loopback:
        raise UnsafeTargetError(f"{target!r} resolves to loopback {addr}; refused.")
    if addr.is_multicast:
        raise UnsafeTargetError(f"{target!r} resolves to multicast {addr}; refused.")
    if addr.is_unspecified:
        raise UnsafeTargetError(f"{target!r} resolves to unspecified {addr}; refused.")
    if not (addr.is_private or addr.is_link_local):
        raise UnsafeTargetError(
            f"{target!r} resolves to non-LAN address {addr}; "
            "recon only probes RFC1918 / CGN / link-local / ULA / IPv6-link-local."
        )
    return addr


def safe_slug(
    target: str,
    resolved: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> str:
    """Produce a safe filename slug that cannot escape tmp/lan/.

    Uses the DNS target lowercased when it is a hostname, else the
    address with ``:`` -> ``_``. All other non-alphanumeric-except-.-_-
    collapse to ``_``; path separators and traversal tokens are refused
    upstream by ``validate_target_shape``.
    """
    try:
        ipaddress.ip_address(target)
        base = str(resolved).replace(":", "_")
    except ValueError:
        base = target.lower()

    if not base or base in {".", ".."}:
        raise UnsafeSlugError(f"target {target!r} yields unsafe slug {base!r}.")
    if any(ch in base for ch in ("/", "\\", "\x00")):
        raise UnsafeSlugError(f"target {target!r} contains path separator/null.")

    slug = _SLUG_KEEP.sub("_", base)
    slug = slug.strip("._-")
    if not slug:
        raise UnsafeSlugError(f"target {target!r} slugs to empty.")
    if len(slug) > 100:
        slug = slug[:100]
    return slug


def redact(message: str, password: str) -> str:
    """Scrub a password token from an error / log string."""
    if password and password in message:
        return message.replace(password, "<REDACTED>")
    return message
