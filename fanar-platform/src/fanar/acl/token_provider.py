"""Manar service-account token provider for the ACL.

Obtains a bearer token for Manar's API — Keycloak password grant on realm `manar`, client
`manar-frontend` (matching Manar's own frontend, per manar-analysis) — using credentials from the
secrets provider, and caches it until shortly before expiry. Pass an instance as
`ManarClient(token_provider=...)`.

The HTTP fetch is injectable, so the caching/expiry logic is unit-tested without a server, and no
credential value is ever logged.
"""
from __future__ import annotations

import time
from typing import Callable

from fanar.security.secrets import SecretsProvider


class ManarTokenProvider:
    def __init__(
        self,
        *,
        token_url: str,
        client_id: str,
        secrets: SecretsProvider,
        username_secret: str = "manar_username",
        password_secret: str = "manar_password",
        leeway_seconds: float = 30.0,
        clock: Callable[[], float] = time.time,
        fetch: Callable[[dict], dict] | None = None,
    ) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._secrets = secrets
        self._username_secret = username_secret
        self._password_secret = password_secret
        self._leeway = leeway_seconds
        self._clock = clock
        self._fetch = fetch or self._http_fetch
        self._token: str | None = None
        self._expires_at = 0.0

    def __call__(self) -> str:
        now = self._clock()
        if self._token and now < self._expires_at - self._leeway:
            return self._token
        data = self._fetch({
            "grant_type": "password",
            "client_id": self._client_id,
            "username": self._secrets.get(self._username_secret),
            "password": self._secrets.get(self._password_secret),
        })
        self._token = data["access_token"]
        self._expires_at = now + float(data.get("expires_in", 60))
        return self._token

    def _http_fetch(self, form: dict) -> dict:
        import httpx  # lazy

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(self._token_url, data=form)
        resp.raise_for_status()
        return resp.json()
