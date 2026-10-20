# Fanar — Phase 0 scaffold

A runnable skeleton of the Phase 0 "foundations & spine" from [`docs/04`](docs/04-build-plan-and-roadmap.md)
§Phase 0. The **core is stdlib-only and unit-tested now**; the web/DB/identity layers are thin
adapters over it (FastAPI, Postgres, Keycloak, Vault).

**Phase 1 has begun** — market-data curve modelling (**NSS + Kalman**, `marketdata/`) and the **NAV
engine** (`nav/`, with QuantLib bond pricing off the NSS curve). These add `numpy`/`scipy`/`QuantLib`.

## Run it

```bash
# Tests — the non-quant core is stdlib-only; Phase-1 quant tests need numpy/scipy/QuantLib:
cd fanar-platform
pip install -e ".[dev]"                                          # once (quant deps + tooling)
python -m pytest -q                                             # 49 tests, all green

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
│  ├─ acl/                    # guard.py (read-only) · manar_client.py (doc-05 map) · token_provider.py
│  ├─ reference/              # service.py (Local + Manar-backed reference-data service)
│  ├─ security/              # secrets.py · auth.py (JWT + RBAC) · pkce.py · sessions.py · oidc.py (BFF)
│  ├─ audit/                 # log.py (in-memory) · pg_audit_log.py · schema.py · factory.py
│  ├─ services/              # transactions.py (booking use case: login → reference → ledger → audit)
│  ├─ marketdata/            # nss.py (NSS curve) · kalman.py · fit.py — BAM curve modelling (Phase 1)
│  ├─ nav/                   # engine.py (NAV/VL + dual-calc) · pricing.py (QuantLib) — Phase 1
│  └─ api/                    # app.py · deps.py · routes_auth.py (BFF) · routes_reference.py · routes_ibor.py
├─ migrations/                # Alembic: 0001 events · 0002 projections+notify · 0003 audit (append-only)
├─ tests/                     # stdlib unittest — core is provable offline
├─ alembic.ini · pyproject.toml · Dockerfile · docker-compose.yml · .env.example
```

## CI

`.github/workflows/ci.yml` (GitHub Actions) runs on push to `main` and every PR, from the
`fanar-platform/` working directory:
- **lint-type-test**: `ruff check` (blocking) · `ruff format --check` + `mypy` (advisory in Phase 0)
  · `pytest`.
- **security**: `pip-audit --strict` (dependency vulnerability scan) + a **CycloneDX SBOM** uploaded
  as a build artifact.

Locally: `pip install -e ".[dev]"` then `ruff check src tests`, `mypy src/fanar`, `pytest -q`,
`pip-audit`.

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

The command runs through the **vertical slice** `services/transactions.book_transaction`: it
authorizes the principal (BFF session or bearer JWT), validates the fund against reference data
(live Manar via the ACL when `FANAR_REFERENCE_SOURCE=manar`), appends the event, and records an
**audit entry** — read back at `GET /api/v1/ibor/audit`. The whole slice is unit-tested offline
(`test_vertical_slice.py`).

## Review findings addressed structurally

- **#2 plaintext secrets** → `security/secrets.py` (Vault KV v2 / env provider) + `acl/token_provider.py`
  (Manar service-account token from secrets, cached); `.gitignore` blocks `.env` and keys.
- **#1/#4/#5 transport & tokens** → the **BFF** (`api/routes_auth.py` + `security/{pkce,sessions,oidc}.py`)
  runs auth-code + PKCE and keeps tokens **server-side** behind an httpOnly/secure/same-site session
  cookie; the API validates a bearer JWT via cached JWKS (`security/auth.JwtVerifier`). Tokens never
  reach the browser.
- **"never book twice"** → `ibor/event_store.py` idempotency keys.
- **read-only-by-default to Manar** → `acl/guard.py` blocks `/command/` unless explicitly authorised.
- **supported deps (SBOM + patch cadence)** → CI runs `pip-audit` and generates a CycloneDX SBOM on
  every push/PR (`.github/workflows/ci.yml`).
- **auditability** → `audit/` records who/what/when for every booking (append-only, migration `0003`,
  read at `GET /api/v1/ibor/audit`).

## What's a stub (deliberately, for Phase 0 proper)

- Postgres event store, the projection runner (**outbox + LISTEN/NOTIFY**, checkpointed catch-up),
  and migrations `0001`/`0002` are implemented. Remaining Phase 0 wiring: Vault, and pointing the
  API + `ManarReferenceSource` at the live backends.
- A running Keycloak realm (`fanar`, a public PKCE client) and a shared session store (Redis) to run
  the BFF end-to-end; the flow, PKCE, session store and JWKS verifier are implemented and unit-tested.
- `VaultSecretsProvider` (hvac, KV v2) and the Manar token provider are implemented; they need a
  running Vault + the Manar service account to exercise live.
- `ManarReferenceSource` goes live read-only with `FANAR_REFERENCE_SOURCE=manar` (reads reference
  data from Manar through the ACL).

## Next (Phase 0 exit — docs/04)

1. Integration test of the command → ledger → projection path against a live Postgres
   (FastAPI TestClient + a disposable DB), then run the projection runner as a service.
2. Provision the Keycloak `fanar` realm + PKCE client and a shared session store (Redis) for the BFF.
3. Stand up Vault (dev secret) + the Manar service account, then run with
   `FANAR_REFERENCE_SOURCE=manar` to read live reference data read-only through the ACL.
4. Tighten CI: make `ruff format --check` and `mypy` blocking once the baseline is clean (advisory now).
5. Drive the booking vertical slice (`services/transactions.py`) against live infra (Postgres +
   Keycloak + Manar) and add a FastAPI TestClient integration test.
