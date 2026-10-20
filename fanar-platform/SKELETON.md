# Fanar — Phase 0 scaffold

A runnable skeleton of the Phase 0 "foundations & spine" from [`docs/04`](docs/04-build-plan-and-roadmap.md)
§Phase 0. The **core is stdlib-only and unit-tested now**; the web/DB/identity layers are thin
adapters over it (FastAPI, Postgres, Keycloak, Vault).

## Run it

```bash
# Core tests — no third-party deps needed:
cd fanar-platform
PYTHONPATH=src python -m unittest discover -s tests -t . -v      # 25 tests, all green

# Full app (needs deps): pip install -e ".[dev]" then
docker compose up -d                      # postgres + keycloak + vault for end-to-end
FANAR_DB_DSN=postgresql+psycopg://fanar:fanar@localhost:5432/fanar alembic upgrade head   # create tables (events + projections)
uvicorn fanar.api.app:app --reload        # GET /health, /api/v1/reference/...
python -m fanar.ibor.projection_runner    # keep read models in sync (outbox + LISTEN/NOTIFY)

# record a transaction (dev needs no IdP), then read the projected positions:
curl -s -XPOST localhost:8000/api/v1/ibor/commands/record-transaction -H 'content-type: application/json' \
  -d '{"fund":"3983","instrument":"BDT1","quantity":100,"effective_date":"2026-10-19"}'
curl -s localhost:8000/api/v1/ibor/positions
```

## Layout

```
fanar-platform/
├─ docs/                      # 00–05 specs (05 = grounded domain model + API contract)
├─ src/fanar/
│  ├─ config.py               # env-driven settings (no secrets in source)
│  ├─ domain/                 # events.py (immutable ledger facts) · models.py (entities from docs/05)
│  ├─ ibor/                   # event_store.py (in-memory) · pg_event_store.py (Postgres) · schema.py
│  │                          #   · mapping.py · projections.py · projection_runner.py · commands.py · factory.py
│  ├─ acl/                    # guard.py (read-only enforcement) · manar_client.py (doc-05 endpoint map)
│  ├─ reference/              # service.py (Local + Manar-backed reference-data service)
│  ├─ security/              # secrets.py (Vault/env) · auth.py (Keycloak JWT + RBAC)
│  └─ api/                    # app.py (FastAPI) · deps.py · routes_reference.py · routes_ibor.py
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

The API is also wired to the ledger: `POST /api/v1/ibor/commands/record-transaction` appends an
event (idempotent via `Idempotency-Key`, behind a maker/checker role check), and
`GET /api/v1/ibor/positions` · `GET /api/v1/ibor/events/{fund}` read it back. The store is chosen by
`ibor/factory` (in-memory under `FANAR_ENV=test`, Postgres otherwise). Command handling lives in the
stdlib `ibor/commands.py`, so it is unit-tested without a web server.

## Review findings addressed structurally

- **#2 plaintext secrets** → `security/secrets.py` (Vault/env provider; `.gitignore` blocks `.env`, keys).
- **#1/#4/#5 transport & tokens** → `security/auth.py` validates bearer JWT server-side; SPA/BFF does
  auth-code+PKCE and keeps tokens out of localStorage (documented contract).
- **"never book twice"** → `ibor/event_store.py` idempotency keys.
- **read-only-by-default to Manar** → `acl/guard.py` blocks `/command/` unless explicitly authorised.

## What's a stub (deliberately, for Phase 0 proper)

- Postgres event store, the projection runner (**outbox + LISTEN/NOTIFY**, checkpointed catch-up),
  and migrations `0001`/`0002` are implemented. Remaining Phase 0 wiring: live Keycloak/JWKS + BFF,
  Vault, and pointing the API + `ManarReferenceSource` at the live backends.
- Live Keycloak JWKS verification wiring and the BFF session-cookie layer.
- `VaultSecretsProvider` (hvac) and the Manar service-account token provider.
- `ManarReferenceSource` is mapped but not yet pointed at the live server (read-only when it is).

## Next (Phase 0 exit — docs/04)

1. Integration test of the command → ledger → projection path against a live Postgres
   (FastAPI TestClient + a disposable DB), then run the projection runner as a service.
2. Wire Keycloak (realm `fanar`, PKCE client) + JWKS verification + the BFF.
3. Vault dev secret + the Manar service-account token provider; flip `ManarReferenceSource` live (read-only).
4. CI: ruff + mypy + the test suite + SBOM/dependency scan.
5. A thin vertical slice: log in → read reference data from Manar via the ACL → record an audited event.
