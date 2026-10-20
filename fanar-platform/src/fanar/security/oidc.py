"""OIDC client for the BFF (Keycloak). The authorize-URL builder is pure; the token exchange uses
httpx (imported lazily) so this module imports cleanly without it.

Endpoints are derived from the realm issuer (Keycloak convention).
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class OidcEndpoints:
    issuer: str

    @property
    def authorize(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/auth"

    @property
    def token(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/token"

    @property
    def logout(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/logout"


class OidcClient:
    def __init__(self, issuer: str, client_id: str, redirect_uri: str,
                 client_secret: str | None = None) -> None:
        self.ep = OidcEndpoints(issuer.rstrip("/"))
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.client_secret = client_secret

    def authorization_url(self, *, state: str, code_challenge: str,
                          scope: str = "openid profile email") -> str:
        """Build the Keycloak authorize URL for an auth-code + PKCE (S256) flow. Pure."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{self.ep.authorize}?{urlencode(params)}"

    def exchange_code(self, *, code: str, code_verifier: str) -> dict:
        """Exchange an authorization code for tokens at the Keycloak token endpoint."""
        import httpx  # lazy

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(self.ep.token, data=data)
        resp.raise_for_status()
        return resp.json()
