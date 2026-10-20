# Fanar — 03 · Architecture, security & non-functional requirements

---

### 1. Architectural style

**Modular monolith first, service-extractable later.** At Sterling's scale, a well-partitioned
modular monolith (clear module boundaries, one deployable) beats premature microservices. Design
module seams (the §1 M-list) so any module can be split into its own service when load or team
structure demands it. Enfusion/Limina prove a single coherent model at this scale; don't
distribute until you must.

**Event-sourced core (IBOR).** The transaction ledger is append-only; positions, cash and NAV are
**projections** rebuilt from events. Benefits: perfect audit, time-travel, bitemporal
restatement, and the "never book twice" guarantee via idempotency keys. Use event sourcing for the
*money ledger*; use ordinary CRUD for reference data and config (don't over-apply it).

**CQRS, cleanly.** Commands (validated, authorised, maker-checker) write events; queries read
projections with `as_of` / `knowledge_date`. This is Manar's `query`/`command` split done
properly.

**Anti-corruption layer** isolates all Manar interaction in one adapter (see `02` §3). Strangler
progress = ACL paths deleted.

```
         ┌─────────────────────────── Fanar ───────────────────────────┐
  Users ─┤  Web UI (SPA)   Control plane UI                              │
         │        │                │                                     │
         │     BFF / API gateway (auth, PKCE, sessions, rate-limit)      │
         │        │                                                      │
         │  ┌─────────── application modules (modular monolith) ──────┐  │
         │  │ ref-data · market-data · IBOR · NAV · treasury · OMS ·  │  │
         │  │ reporting · recon · risk · admin · control-plane        │  │
         │  └─────────────────────────────────────────────────────────┘  │
         │        │              │                 │                     │
         │   Event store     Projections       Scheduler/workers         │
         │   (ledger)        (read models)                               │
         └────────┼──────────────┼─────────────────┼─────────────────────┘
                  │              │                 │
         Postgres │   Object store (exports)   Vault (secrets)   Keycloak (OIDC)
                  │
      ┌───────────┴─────────────┐
      │  ACL adapters           │  → Manar API (strangler) · Maroclear · dépositaire bank
      │                         │  → BAM · LSEG/Refinitiv · Gmail/SMTP
      └─────────────────────────┘
```

### 2. Technology stack (recommended, with rationale)

| Layer | Recommendation | Why |
|---|---|---|
| **Primary language (domain/services)** | **Python 3.12+** | Sterling's team already writes it; the automation, quant (NSS/Kalman), pandas/Excel and Playwright code ports directly; fastest path to productivity. FastAPI for the API. |
| Alt. for performance-critical core | Kotlin/JVM or Go, *only if* a hot path demands it | Don't adopt day one; keep the stack small. |
| **Numerics / pricing** | **QuantLib** (+ NumPy/pandas; keep the NSS+Kalman code) | Tested fixed-income pricing, curves, day-counts, schedules — retire the Excel pricer. |
| **Datastore** | **PostgreSQL** (event store + projections; `jsonb` for flexible payloads) | One dependable engine; transactional; bitemporal-friendly; range types for validity. Add **TimescaleDB** extension for price/curve time-series if volume warrants. |
| **Event/stream** | Start with a Postgres-backed outbox + LISTEN/NOTIFY; adopt **Kafka/Redpanda** only at scale | Avoid operational burden early; the seam is the same. |
| **Object storage** | S3-compatible (MinIO on-prem, or cloud) | Exports, reports, evidence; keep the file-share drops via a gateway during transition. |
| **Identity** | **Keycloak** | Already in house; auth-code + PKCE + MFA; RBAC + groups; service accounts for automation. |
| **Secrets** | **HashiCorp Vault** (or cloud KMS/secret manager) | Directly closes the plain-text-password finding. |
| **Frontend** | **Angular (current LTS)** or React — pick one, keep it supported | Team knows Angular (Manar is Angular); the rule is *supported version + patch cadence*, never EOL. |
| **BFF** | Thin backend-for-frontend holding the session | Tokens live in httpOnly/secure cookies, **never `localStorage`** (review finding #4). |
| **Scheduling/workers** | A real job runner (e.g. APScheduler→Celery/RQ, or Temporal for complex sagas) | Server-side, HA; replaces per-workstation Task Scheduler. |
| **Observability** | OpenTelemetry → Prometheus/Grafana + structured logs | Money paths must be observable. |
| **Infra** | Docker + Compose on a hardened host to start; Kubernetes only if/when needed | Right-sized; cloud or on-prem per the data-residency decision. |
| **CI/CD** | Git + pipeline with tests, SAST, dependency/SBOM scan, signed releases | Supported, patched, provable. |

> **Stack principle:** smallest set of dependable technologies the team can operate; Python-centric
> to reuse Sterling's existing skills and code; no component without a patch/support story.

### 3. Security design — every review finding closed by construction

The infrastructure review raised six issues. Fanar answers each **by design**, and this matrix is
the acceptance test.

| # | Review finding | Fanar design answer | Verify |
|---|---|---|---|
| 1 | **Unencrypted access** (HTTP, no redirect, :443 absent) | TLS everywhere: internal DNS name + trusted cert; HTTPS for UI, API, identity; HTTP→HTTPS redirect + HSTS *after* TLS is real; mTLS for service↔ACL where feasible. | TLS scan; no plaintext auth; OWASP TLS checklist [S2]. |
| 2 | **Plain-text automation passwords** (3+ files, broad ACLs) | No secret on disk in clear. **Vault**; short-lived service tokens; automation uses OIDC service accounts, not shared human creds; least-privilege; **separate read-only from write identities**; rotation + audited access. | No secret in repo/FS; vault audit log; secret-scanning in CI. |
| 3 | **EOL Angular 14** | Current-LTS frontend; **SBOM** + automated dependency scanning; documented patch cadence; no single-package prod upgrades — validated releases only. | SBOM present; no EOL deps; CI dependency gate. |
| 4 | **Password grant + tokens in `localStorage`** | **Authorization-code + PKCE**; **MFA** enforced; short-lived access tokens + rotating refresh; **BFF session in httpOnly/secure/same-site cookies**; server-side authorization on every command. | No password grant; no token in browser storage; authz tests. |
| 5 | **Identity URL inconsistency** (:8060 advertised, times out) | Single canonical HTTPS issuer; aligned discovery/issuer/proxy; no mixed host:port advertised to clients. | OIDC discovery matches reachable issuer; token validation tests. |
| 6 | **Session/workstation & file-share dependencies** | Server-side scheduler (no logged-on interactive session); SMB signing + encryption, least-privilege shares, or replace share with object storage + API; no workstation as a dependency. | Jobs run headless/server-side; share perms reviewed; encryption verified. |

**Additional security baseline (not in the review but required for a financial system):**
- **RBAC + segregation of duties**; **maker-checker** on every state-changing money operation.
- **Immutable audit log** (append-only, tamper-evident) of every command, approval and booking.
- **Idempotency keys** on all commands (no double-booking, platform-guaranteed).
- **Input validation & output encoding**; parameterised queries; no secrets in URLs/logs
  (a Privacy rule and a review-adjacent concern).
- **Backups + tested restore** for the event store (the review flagged backup capability as
  *unverified* — make it verifiable: scheduled backups, periodic restore drills, documented RPO/RTO).
- **Threat model & pen-test** before Fanar touches the real booking chain.

### 4. Non-functional requirements

| Attribute | Target |
|---|---|
| **Correctness** | Money paths: dual-calc NAV, reconciliation to depositary, property-based + golden-master tests; bitemporal restatement without data loss. |
| **Auditability** | 100% of state changes attributable (who/what/when/before-after); regulator-grade export. |
| **Availability** | Business-hours critical; daily close must complete. Start with a well-backed single node + fast restore; HA when justified. Define RPO ≤ 15 min, RTO ≤ 2 h (confirm with business). |
| **Performance** | Treasury plan < 1 min; NAV close for all funds well inside the daily window; API p95 < 300 ms for queries. |
| **Scalability** | Sterling's 6 funds today → design for 10× funds/instruments without re-architecture (projections + indexing, optional Timescale/Kafka seams). |
| **Security** | Per §3; pass an external review before production booking. |
| **Observability** | Traces/metrics/logs on every job and command; alerting on breaks and failures. |
| **Maintainability** | Modular boundaries; no EOL deps; ≥ 80% coverage on money modules; typed Python. |
| **Data residency / compliance** | Per the ownership decision — likely on-prem or Morocco/EU region; GDPR-aligned for client PII; AMMC retention rules. |
| **Usability** | Exception-only daily ops; a treasurer can produce + approve the plan in minutes; clear audit of every booking. |

### 5. Integrations

- **Manar** (strangler, via ACL) — read positions/cash/NAV; book tickets early-phase.
- **Maroclear** — settlement/position reconciliation.
- **Dépositaire bank** — cash/position statements, instructions.
- **Bank Al-Maghrib** — curves, adjudications (Sterling's `bam_adjudications`/`courbes`).
- **LSEG/Refinitiv** — market data/prices (Sterling's `lseg_screenshots`).
- **Email (Gmail/SMTP)** — report delivery, alerts (Sterling's `tools/gmail.py`).
- **File shares** (`\\192.168.1.106\...`) — keep drops during transition via a storage gateway;
  migrate consumers to the API/object store.
- **Keycloak**, **Vault** — identity and secrets.

### 6. Data migration & coexistence

- **Backfill the ledger** from Manar history + Sterling's exported archives (`histo_vl`,
  `actif_net_vl`, compo portefeuilles, échéanciers) — bitemporal, with `knowledge_date` = import
  time and `effective_date` = business date.
- **Shadow mode**: run Fanar's NAV/treasury in parallel with Manar; reconcile daily; promote a
  domain to system-of-record only after a defined clean-parallel period and regulatory sign-off.
- **Reversibility**: every migrated domain keeps its ACL path until formally retired, so Sterling
  can fall back to Manar during the transition.
