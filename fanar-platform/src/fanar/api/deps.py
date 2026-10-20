"""FastAPI dependencies — settings, the event store, and the authenticated principal.

The event store is a process singleton from `ibor.factory` (in-memory under `FANAR_ENV=test`,
Postgres otherwise). Auth validates a Keycloak bearer JWT when an issuer/JWKS is configured; with no
IdP configured (local dev) it yields a dev principal with maker/checker roles so the endpoints are
exercisable offline.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Header, HTTPException

from fanar.config import Settings
from fanar.ibor.event_store import EventStore
from fanar.ibor.factory import build_event_store
from fanar.security.auth import Principal, verify_bearer


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


@lru_cache
def get_event_store() -> EventStore:
    return build_event_store(get_settings())


def require_principal(authorization: str | None = Header(default=None)) -> Principal:
    settings = get_settings()
    if settings.oidc_jwks_url:                      # production: real JWT required
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="missing bearer token")
        token = authorization.split(" ", 1)[1]
        try:
            return verify_bearer(
                token,
                jwks_url=settings.oidc_jwks_url,
                issuer=settings.oidc_issuer,
                audience=settings.oidc_audience,
            )
        except Exception as exc:                    # noqa: BLE001 - any verification failure is 401
            raise HTTPException(status_code=401, detail="invalid token") from exc
    # Local dev with no IdP configured.
    return Principal(subject="dev", username="dev", tenant=settings.tenant,
                     roles=frozenset({"front", "back"}))
