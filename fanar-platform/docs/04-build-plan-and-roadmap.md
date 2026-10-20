# Fanar — 04 · Build plan, roadmap & decisions

Strategy: **strangler fig** (Option B). Build the IBOR spine + control plane, then migrate
capabilities off Manar one at a time, starting where Sterling already has working logic. Every
phase ships something usable and reversible.

---

### 1. Guiding principles

1. **Shadow before system-of-record.** Fanar computes in parallel and reconciles against Manar
   until a domain is proven and signed off. No big-bang cutover.
2. **Start where you're strongest.** Treasury/repo, NAV, market data and reporting already exist
   as Sterling code — port them into Fanar first; they are the fastest wins and the biggest pain.
3. **Spine first.** Reference data + IBOR ledger + control plane underpin everything; build them
   in Phase 0/1 even though they're less visible.
4. **Security is phase-zero, not a hardening sprint.** TLS, Keycloak PKCE+MFA, Vault and audit are
   in from the first deployable.
5. **Reversible always.** Keep the ACL path to Manar per domain until that domain is retired.

### 2. Phases

#### Phase 0 — Foundations & spine (≈ 6–8 weeks)
- Repo, CI/CD (tests + SAST + SBOM/dependency scan), environments (dev/shadow).
- Platform security baseline: TLS, Keycloak (auth-code + PKCE + MFA), BFF session cookies, Vault,
  RBAC skeleton, immutable audit log, idempotency framework.
- **IBOR skeleton**: event store + projection pattern on Postgres; bitemporal model.
- **Reference data (M1)** + **control plane (M12)**: productise the `sterling-automation` job
  framework (jobs, run history, notifications, scheduler, control UI) onto Fanar's API.
- **ACL to Manar**: one server-side adapter replacing headless-browser scraping (vaulted creds,
  read-only by default, the `/command/` guard).
- *Exit:* Fanar can authenticate users, run scheduled jobs server-side, read Manar via the ACL,
  and record events/audit. No workstation dependency.

#### Phase 1 — Read-side truth: market data, IBOR, NAV, reporting (≈ 10–14 weeks)
- **Market data & curves (M2)**: ingest BAM curves/adjudications + LSEG; port **NSS + Kalman**;
  curve validation.
- **IBOR positions & cash (M3)**: project positions/cash from ingested transactions; backfill from
  Manar + Sterling archives.
- **NAV/VL engine (M4)**: QuantLib pricing; dual-calc validation (port `validation_vl`); history.
- **Reporting & exports (M7)**: reproduce actif_net_vl, compo portefeuilles, histo VL, échéanciers,
  TAUX with stable schemas + existing file-share drops.
- Run **NAV in shadow**, reconcile against Manar daily.
- *Exit:* Fanar independently reproduces daily NAV + reports, matching Manar within tolerance,
  entirely from its own data — no scraping on the read side.

#### Phase 2 — Write-side: treasury/repo & OMS (≈ 12–16 weeks)
- **Treasury, repo & collateral (M5)**: port `treso`/`repos_reconduction` natively — plan,
  collateral optimisation, proposal + booking panel, **rehearse → recompute → maker-checker →
  idempotent book**, full audit. Book via ACL to Manar initially.
- **OMS lifecycle (M6)** with compliance/limits gate for the ticket types Sterling books.
- **Reconciliation (M8)** first cut: NAV + position/cash breaks queue.
- *Exit:* Sterling runs the daily treasury plan and books repos **through Fanar** (writing to Manar
  via the ACL) with two-person approval and complete audit — replacing the current bespoke path.

#### Phase 3 — Reconciliation, risk, and becoming system-of-record (≈ ongoing, 6+ mo)
- **Reconciliation (M8)** vs **Maroclear** + dépositaire.
- **Risk & analytics (M9)**: duration/convexity, exposures, limits, scenarios.
- **AMMC/ASFIM regulatory reporting**.
- Promote proven domains to **system-of-record**; begin **direct** counterparty/depositary
  connectivity to remove Manar from the booking chain.
- *Exit (= Option C territory):* Manar demoted to legacy/retired for migrated domains; ACL paths
  deleted domain-by-domain.

#### Phase 4 — Optional extensions
CRM/KYC/TA (M10), full accounting (M11), broader asset classes, multi-manager/SaaS. Decide later.

### 3. MVP (first demonstrable value, end of Phase 1)

> **"Fanar reproduces today's daily NAV and the standard exports for all six STERLING funds,
> from its own IBOR, over HTTPS with MFA, server-side on a schedule — matching Manar in shadow."**

That alone retires the read-side scraping, closes most security findings for the new path, and
proves the spine.

### 4. Team & effort (indicative — calibrate after the ambition decision)

| Role | Phase 0–1 | Phase 2–3 |
|---|---|---|
| Tech lead / architect (Python + domain) | 1 | 1 |
| Backend engineers | 1–2 | 2–3 |
| Frontend engineer | 0.5 | 1 |
| Quant / fixed-income (curves, pricing, NAV) | 0.5 (advisory) | 1 |
| DevOps/security (part-time) | 0.5 | 0.5 |
| Business/ops SME (Sterling treasury) | 0.5 | 0.5 |

Realistic steady state for Option B: **3–5 people**. Phase 0–1 ≈ **4–6 months**; booking live
(Phase 2) ≈ **9–12 months** from start; system-of-record for first domains ≈ **18–24 months**.
Adam's existing `sterling-automation` code materially shortens Phases 1–2.

### 5. Top risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Regulatory**: Fanar NAV used before validated | High | Shadow mode + sign-off gate; Manar stays system-of-record until AMMC-acceptable; keep audit. |
| **Licence/IP**: Manar terms restrict interop/extraction | High | Legal review *before* build (`00` §3, §7); clean-room discipline; no source reconstruction. |
| **Booking a wrong trade** | High | Maker-checker, recompute-before-book, idempotency, stop-at-first-problem, pen-test before go-live. |
| **Data migration gaps** (history incomplete/inconsistent) | Med | Bitemporal backfill with provenance; reconcile backfill vs Manar; keep ACL fallback. |
| **Scope creep → full rewrite too early** | Med | Hold to strangler; MVP discipline; Option C is an outcome, not a plan. |
| **Key-person dependency** (domain lives in one person's head/code) | Med | Document rules from `sterling-automation`; pair; tests encode the rules. |
| **Market-data feed access/licensing** (LSEG/BAM) | Med | Confirm redistribution/usage rights; isolate behind adapters. |
| **Over-engineering infra** (k8s/Kafka too soon) | Low–Med | Modular monolith + Postgres first; adopt heavier infra only on evidence. |

### 6. Immediate next steps (first 2 weeks, once mandated)

1. **Decisions** — resolve the four gating decisions in `00` §7 (mandate, ambition, system-of-record
   constraint, booking authority) + the legal/licence checkpoint.
2. **Domain rule capture** — extract and document the treasury/repo/NAV/collateral rules already in
   `sterling-automation` into a reviewed spec (they are the crown jewels).
3. **Optional scoped API enumeration** — if wanted, a read-only pass to document the exact Manar
   query/command contract the ACL must speak (authorised, interface-only).
4. **Stand up Phase 0 skeleton** — repo, CI, Keycloak PKCE+MFA, Vault, IBOR event-store spike,
   control-plane port — as a thin vertical slice (log in → run a job → read Manar via ACL → record
   an audited event).
5. **Pick names & conventions** — codename, API versioning, event schema registry, coding
   standards.

### 7. Decision log (open)

| # | Decision | Owner | Status |
|---|---|---|---|
| D1 | Sanctioned Sterling project? Budget/owner/data-governance | Sterling mgmt | **Open** |
| D2 | Manar licence/SLA allows interop + replacement? | Legal | **Open** |
| D3 | Ambition: B (strangle) vs A vs C | Sponsor | **Open** (spec assumes B) |
| D4 | Manar remains regulatory system-of-record until validated? | Compliance | **Open** (assumed yes) |
| D5 | Early booking via Manar ACL or direct to counterparties? | Ops + Compliance | **Open** |
| D6 | Deployment: on-prem vs cloud; data residency | IT + Compliance | **Open** |
| D7 | Frontend framework (Angular LTS vs React) | Tech lead | **Open** (either fine) |
| D8 | Primary language confirmed Python? | Tech lead | **Open** (recommended yes) |

> Nothing in Phase 0 is blocked by D4–D8; D1/D2 should clear before meaningful build spend.
