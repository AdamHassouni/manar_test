"""Runtime settings from environment (stdlib only — no secret values live here).

Secrets (DB password, Manar credentials) are resolved through `fanar.security.secrets`, not read
as plain env in production. This object only holds non-secret wiring.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str = "dev"
    tenant: str = "entity1"
    db_dsn: str = "postgresql+asyncpg://fanar:fanar@localhost:5432/fanar"
    oidc_issuer: str = ""
    oidc_audience: str = "fanar-api"
    oidc_jwks_url: str = ""
    secrets_backend: str = "env"            # "env" | "vault"
    vault_addr: str = ""
    manar_base_url: str = "http://192.168.1.104"
    manar_read_only: bool = True

    @staticmethod
    def from_env(environ: dict[str, str] | None = None) -> "Settings":
        e = environ if environ is not None else os.environ
        def b(key: str, default: bool) -> bool:
            return e.get(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}
        return Settings(
            env=e.get("FANAR_ENV", "dev"),
            tenant=e.get("FANAR_TENANT", "entity1"),
            db_dsn=e.get("FANAR_DB_DSN", Settings.db_dsn),
            oidc_issuer=e.get("FANAR_OIDC_ISSUER", ""),
            oidc_audience=e.get("FANAR_OIDC_AUDIENCE", "fanar-api"),
            oidc_jwks_url=e.get("FANAR_OIDC_JWKS_URL", ""),
            secrets_backend=e.get("FANAR_SECRETS_BACKEND", "env"),
            vault_addr=e.get("FANAR_VAULT_ADDR", ""),
            manar_base_url=e.get("FANAR_MANAR_BASE_URL", "http://192.168.1.104"),
            manar_read_only=b("FANAR_MANAR_READ_ONLY", True),
        )
