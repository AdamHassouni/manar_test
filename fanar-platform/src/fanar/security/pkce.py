"""PKCE helpers (RFC 7636) and random tokens — pure stdlib, unit-tested.

Used by the BFF to run authorization-code + PKCE against Keycloak; the browser never sees tokens.
"""
from __future__ import annotations

import base64
import hashlib
import secrets


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def generate_verifier(n_bytes: int = 64) -> str:
    """A high-entropy code_verifier (43–128 chars after base64url)."""
    return _b64url(secrets.token_bytes(n_bytes))


def challenge_for(verifier: str) -> str:
    """The S256 code_challenge for a verifier (deterministic)."""
    return _b64url(hashlib.sha256(verifier.encode("ascii")).digest())


def generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for an S256 PKCE exchange."""
    verifier = generate_verifier()
    return verifier, challenge_for(verifier)


def random_token(n_bytes: int = 32) -> str:
    """An unguessable opaque token (state, session id)."""
    return _b64url(secrets.token_bytes(n_bytes))
