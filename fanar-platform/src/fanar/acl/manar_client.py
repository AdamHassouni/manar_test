"""Manar adapter — reads through the real Manar API during the strangler phase.

Grounded in the confirmed endpoint map (docs/05 §3, manar-analysis/04). `httpx` is imported lazily
so the stdlib core and its tests never require it. Every call passes through `guard.enforce`, so a
`command` (write) is refused unless the client is explicitly not read-only AND the call is
authorised — which must be audited upstream.

Auth: a vaulted service account's bearer JWT (never credentials in source); tenant-scoped. The `?HS=`
flag Manar expects is passed through verbatim by callers.
"""
from __future__ import annotations

from typing import Any, Callable

from fanar.acl.guard import enforce

# Fanar operation -> (HTTP method, Manar resource path under /api/). Confirmed by live capture.
MANAR_ENDPOINTS: dict[str, tuple[str, str]] = {
    "nav.history":                 ("GET",  "portfolio-management/query/validation-souscription-rachat/dateVL"),
    "treasury.repo_list":          ("POST", "portfolio-management/query/repo/list"),
    "ibor.cash_positions":         ("GET",  "portfolio-management/query/workspace/position-espece"),
    "reference.instruments":       ("POST", "administration/query/list/titres"),
    "reference.posting_rules":     ("POST", "administration/query/list/postes"),
    "reference.counterparties":    ("POST", "administration/query/list/tiers"),
    "reference.authorized_tiers":  ("POST", "administration/query/list/authorizedTiers"),
    "reference.codification":      ("GET",  "administration/query/list/getByClasse"),
    "market.curve_types":          ("POST", "administration/query/list/coubreTauxByType"),
    "workflow.has_workflow":       ("POST", "administration/query/param-workflow/hasWorkflow"),
    "jobs.list":                   ("POST", "administration/query/jobs"),
    # WRITE — gated; present for the eventual authorised booking path, never auto-exercised.
    "treasury.book_repo":          ("POST", "portfolio-management/command/repo"),
}


class ManarClient:
    """Thin, guarded HTTP adapter. `token_provider()` returns a fresh bearer token."""

    def __init__(
        self,
        base_url: str,
        token_provider: Callable[[], str],
        *,
        read_only: bool = True,
        tenant: str = "entity1",
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token_provider
        self.read_only = read_only
        self.tenant = tenant
        self.timeout = timeout

    # ---- public API ----
    def query(self, operation: str, *, params: dict | None = None, body: Any = None) -> Any:
        method, path = self._resolve(operation)
        if "/query/" not in f"/{path}/":
            raise ValueError(f"'{operation}' is not a read operation")
        return self._send(method, path, params=params, body=body)

    def command(self, operation: str, *, body: Any, authorized: bool = False) -> Any:
        if self.read_only:
            raise PermissionError("ManarClient is read-only; construct with read_only=False to book")
        method, path = self._resolve(operation)
        return self._send(method, path, body=body, authorized_write=authorized)

    # ---- internals ----
    def _resolve(self, operation: str) -> tuple[str, str]:
        if operation not in MANAR_ENDPOINTS:
            raise KeyError(f"unknown Manar operation: {operation}")
        return MANAR_ENDPOINTS[operation]

    def _send(
        self, method: str, path: str, *, params: dict | None = None, body: Any = None,
        authorized_write: bool = False,
    ) -> Any:
        url = f"{self.base_url}/api/{path.lstrip('/')}"
        enforce(method, url, authorized_write=authorized_write)   # structural read-only guard
        import httpx  # lazy: keeps the core dependency-free

        headers = {"Authorization": f"Bearer {self._token()}", "Accept": "application/json"}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.request(method, url, params=params, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json() if resp.content else None
