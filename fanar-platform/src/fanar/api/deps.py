"""FastAPI dependencies — settings, event store, reference data, BFF session/OIDC, and the principal.

Principal resolution order: (1) the BFF **session cookie** (browser clients — tokens stay
server-side); (2) a **bearer JWT** validated against the realm JWKS (service/automation clients);
(3) a dev principal when no IdP is configured, so the API is exercisable offline.

Reference data comes from the local seed by default, or live from Manar (read-only, via the ACL)
when `FANAR_REFERENCE_SOURCE=manar`.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Header, HTTPException, Request

from fanar.acl.manar_client import ManarClient
from fanar.acl.token_provider import ManarTokenProvider
from fanar.config import Settings
from fanar.ibor.event_store import EventStore
from fanar.ibor.factory import build_event_store
from fanar.reference.service import LocalReferenceSource, ManarReferenceSource, ReferenceService
from fanar.security.auth import JwtVerifier, Principal
from fanar.security.oidc import OidcClient
from fanar.security.secrets import SecretsProvider, build_provider
from fanar.security.sessions import InMemorySessionStore, SessionStore


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


@lru_cache
def get_event_store() -> EventStore:
    return build_event_store(get_settings())


@lru_cache
def get_secrets_provider() -> SecretsProvider:
    s = get_settings()
    return build_provider(s.secrets_backend, vault_addr=s.vault_addr)


@lru_cache
def get_reference_service() -> ReferenceService:
    s = get_settings()
    if s.reference_source == "manar":
        token_url = f"{s.manar_base_url.rstrip('/')}/realms/manar/protocol/openid-connect/token"
        token_provider = ManarTokenProvider(
            token_url=token_url, client_id=s.manar_client_id, secrets=get_secrets_provider()
        )
        manar = ManarClient(s.manar_base_url, token_provider, read_only=True, tenant=s.tenant)
        return ReferenceService(ManarReferenceSource(manar))
    return ReferenceService(LocalReferenceSource())


@lru_cache
def get_session_store() -> SessionStore:
    return InMemorySessionStore()


@lru_cache
def get_oidc_client() -> OidcClient:
    s = get_settings()
    return OidcClient(s.oidc_issuer, s.oidc_client_id, s.oidc_redirect_uri)


@lru_cache
def get_verifier() -> JwtVerifier:
    s = get_settings()
    return JwtVerifier(s.oidc_jwks_url, s.oidc_issuer, s.oidc_audience)


def _principal_from_session(data: dict) -> Principal:
    p = data["principal"]
    return Principal(subject=p["subject"], username=p["username"], tenant=p["tenant"],
                     roles=frozenset(p.get("roles", [])))


def require_principal(request: Request, authorization: str | None = Header(default=None)) -> Principal:
    settings = get_settings()

    # 1) BFF session cookie — tokens never leave the server.
    sid = request.cookies.get(settings.session_cookie_name)
    if sid:
        session = get_session_store().get(sid)
        if session and "principal" in session.data:
            return _principal_from_session(session.data)

    # 2) Bearer JWT (service/automation clients).
    if settings.oidc_jwks_url:
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
            try:
                return get_verifier().verify(token)
            except Exception as exc:  # noqa: BLE001 - any verification failure is 401
                raise HTTPException(status_code=401, detail="invalid token") from exc
        raise HTTPException(status_code=401, detail="not authenticated")

    # 3) Local dev with no IdP configured.
    return Principal(subject="dev", username="dev", tenant=settings.tenant,
                     roles=frozenset({"front", "back"}))
