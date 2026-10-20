"""Read-only guard for all Manar interaction (stdlib, unit-tested).

Mirrors Sterling's `_guard` (tools/manar/session.py) and the browser write-guard used during the
reverse-engineering: reads pass (GET/HEAD, or any `/query/` path — Manar uses POST for filtered
reads too), auth/session flows pass, and anything that would change Manar state (`/command/`, other
writes) is **blocked** unless an explicit, audited booking authorisation is supplied.

This makes "read-only by default" a structural guarantee, not a convention.
"""
from __future__ import annotations

import re

_QUERY = re.compile(r"/query/", re.IGNORECASE)
_AUTH = re.compile(r"(login|auth|openid-connect/token|sendotp|verify)", re.IGNORECASE)
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class ReadOnlyViolation(RuntimeError):
    """A state-changing Manar call was attempted without authorisation."""


def is_read(method: str, url: str) -> bool:
    """True if (method, url) is a safe read or an auth/session call."""
    m = (method or "GET").upper()
    if m not in _WRITE_METHODS:
        return True
    url = url or ""
    if _QUERY.search(url):
        return True
    if _AUTH.search(url):
        return True
    return False


def enforce(method: str, url: str, *, authorized_write: bool = False) -> None:
    """Raise ReadOnlyViolation for an unauthorised write; return None otherwise."""
    if authorized_write or is_read(method, url):
        return
    raise ReadOnlyViolation(f"blocked write to Manar: {method} {url}")
