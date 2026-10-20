"""Identity & RBAC — Keycloak bearer-JWT validation (review findings #1, #4, #5).

The backend only ever validates a **bearer JWT** (the SPA/BFF performs authorization-code + PKCE and
keeps tokens in httpOnly cookies, never localStorage). Roles come from `realm_access.roles`, exactly
as Manar's own frontend reads them — but validated server-side on every request.

The RBAC logic (`Principal`, `require`) is stdlib and unit-tested. JWT **signature** verification
(JWKS) uses `pyjwt`, imported lazily, so the core stays dependency-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class AuthError(RuntimeError):
    pass


@dataclass(frozen=True)
class Principal:
    subject: str
    username: str
    tenant: str
    roles: frozenset[str] = field(default_factory=frozenset)

    def has_any(self, *needed: str) -> bool:
        return bool(self.roles.intersection(needed))

    def require(self, *needed: str) -> None:
        if not self.has_any(*needed):
            raise AuthError(f"missing role; need one of {needed}")


def principal_from_claims(claims: dict) -> Principal:
    """Map a decoded JWT claim set to a Principal (realm_access.roles → roles)."""
    realm = claims.get("realm_access") or {}
    roles = frozenset(realm.get("roles") or [])
    return Principal(
        subject=claims.get("sub", ""),
        username=claims.get("preferred_username") or claims.get("email") or "",
        tenant=claims.get("tenant") or claims.get("tenant_id") or "",
        roles=roles,
    )


def verify_bearer(token: str, *, jwks_url: str, issuer: str, audience: str) -> Principal:
    """Verify signature + iss/aud/exp against the realm JWKS, then build a Principal.

    Lazy-imports pyjwt so importing this module (e.g. for `Principal`) needs no third-party deps.
    """
    import jwt  # pyjwt  (lazy)
    from jwt import PyJWKClient

    signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key
    claims = jwt.decode(token, signing_key, algorithms=["RS256"], audience=audience, issuer=issuer)
    return principal_from_claims(claims)
