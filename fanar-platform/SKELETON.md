# Fanar — Phase 0 scaffold

A runnable skeleton of the Phase 0 "foundations & spine" from [`docs/04`](docs/04-build-plan-and-roadmap.md)
§Phase 0. The **core is stdlib-only and unit-tested now**; the web/DB/identity layers are thin
adapters over it (FastAPI, Postgres, Keycloak, Vault).

## Run it

```bash
# Core tests — no third-party deps needed:
cd fanar-platform
PYTHONPATH=src python -m unittest discover -s tests -t . -v      # 18 tests, all green

# Full app (needs deps): pip install -e ".[dev]" then
docker compose up -d                      # postgres + keycloak + vault for end-to-end
FANAR_DB_DSN=postgresql+psycopg://fanar:fanar@localhost:5432/fanar alembic upgrade head   # create the events table
uvicorn fanar.api.app:app --reload        # GET /health, /api/v1/reference/...
```

## Layout

```
fanar-platform/
├─ docs/                      # 00–05 specs (05 = grounded domain model + API contract)
├─ src/fanar/
│  ├─ config.py               # env-driven settings (no secrets in source)
│  ├─ domain/                 # events.py (immutable ledger facts) · models.py (entities from docs/05)
│  ├─ ibor/                   # event_store.py (in-memory) · pg_event_store.py (Postgres) · schema.py
│  │                          #   · mapping.py · projections.py (positions/NAV) · factory.py
│  ├─ acl/                    # guard.py (read-only enforcement) · manar_client.py (doc-05 endpoint map)
│  ├─ reference/              # service.py (Local + Manar-backed reference-data service)
│  ├─ security/              # secrets.py (Vault/env) · auth.py (Keycloak JWT + RBAC)
│  └─ api/                    # app.py (FastAPI) · routes_reference.py
├─ migrations/                # Alembic: 0001 creates the append-only events table (+ no-mutate trigger)
├─ tests/                     # stdlib unittest — core is provable offline
├─ alembic.ini · pyproject.toml · Dockerfile · docker-compose.yml · .env.example
```

## The four requested pieces → where they are

| Requested | Implemented in | Proven by |
|---|---|---|
| **Repo structure + infra** | `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `src/` layout | imports clean |
| **Reference-data service + ACL adapter (grounded in 05)** | `reference/service.py` (`Local` + `Manar` sources), `acl/manar_client.py` (`MANAR_ENDPOINTS` from docs/05 §3), `acl/guard.py` | `test_reference.py`, `test_acl_guard.py` |
| **Security baseline** | `security/secrets.py` (no plaintext secrets), `security/auth.py` (Keycloak JWT + RBAC) | `test_auth.py` |
| **IBOR event-store spike** | `ibor/event_store.py` (in-memory) + `ibor/pg_event_store.py` (Postgres, same interface) + `ibor/projections.py`, with the `migrations/0001` events table (append-only, bitemporal, idempotent) | `test_event_store.py`, `test_projections.py`, `test_mapping.py` |

## Review findings addressed structurally

- **#2 plaintext secrets** → `security/secrets.py` (Vault/env provider; `.gitignore` blocks `.env`, keys).
- **#1/#4/#5 transport & tokens** → `security/auth.py` validates bearer JWT server-side; SPA/BFF does
  auth-code+PKCE and keeps tokens out of localStorage (documented contract).
- **"never book twice"** → `ibor/event_store.py` idempotency keys.
- **read-only-by-default to Manar** → `acl/guard.py` blocks `/command/` unless explicitly authorised.

## What's a stub (deliberately, for Phase 0 proper)

- Postgres event store + the `0001` migration are implemented (`alembic upgrade head`); the
  transactional **outbox + LISTEN/NOTIFY** fan-out to projections is the remaining piece.
- Live Keycloak JWKS verification wiring and the BFF session-cookie layer.
- `VaultSecretsProvider` (hvac) and the Manar service-account token provider.
- `ManarReferenceSource` is mapped but not yet pointed at the live server (read-only when it is).

## Next (Phase 0 exit — docs/04)

1. Projection runner off the event log (outbox + LISTEN/NOTIFY); wire the API to the Postgres store
   through `ibor/factory.build_event_store`.
2. Wire Keycloak (realm `fanar`, PKCE client) + JWKS verification + the BFF.
3. Vault dev secret + the Manar service-account token provider; flip `ManarReferenceSource` live (read-only).
4. CI: ruff + mypy + the test suite + SBOM/dependency scan.
5. A thin vertical slice: log in → read reference data from Manar via the ACL → record an audited event.
