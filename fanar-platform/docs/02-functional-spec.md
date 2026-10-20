# Fanar — 02 · Functional specification

Scope of this file: the modules, the domain model, the API surface, and the handful of workflows
that carry the business. Grounded in Manar's observed domain **and** Sterling's own operational
code, which already encodes the real rules.

---

### 1. Module map

Ordered by build priority (see `04`). ✦ = Sterling already automates this today; those are the
beachheads for the strangler.

| # | Module | Purpose | Priority |
|---|---|---|---|
| M1 | **Reference data & security master** ✦ | Instruments (BDT, BSF, CD, equities, OPCVM), issuers, counterparties, calendars, FX, rates (TAUX). Identifiers: ISIN/FIGI/internal, Manar portfolio codes. | P0 |
| M2 | **Market data & curves** ✦ | BAM curves + adjudications, LSEG/Refinitiv feed, prices, the **NSS + Kalman** curve model, curve validation. | P0 |
| M3 | **IBOR — positions, cash & ledger** ✦ | Event-sourced transaction ledger; derived positions (securities + cash "Banque Front"), per fund, bitemporal. The spine. | P0 |
| M4 | **NAV / VL engine** ✦ | Daily net asset value per fund, independent recompute, validation & sign-off, history (`histo_vl`). | P0 |
| M5 | **Treasury, repo & collateral** ✦ | Daily cash plan: interfund repos → market borrow/placement; collateral selection & optimisation; booking with maker-checker. The flagship. | P1 |
| M6 | **OMS / transaction booking** ✦ | Order/ticket lifecycle, allocations, compliance/limits gate, booking (initially via anti-corruption layer to Manar). | P1 |
| M7 | **Reporting & exports** ✦ | Portfolio composition, échéanciers, actif net, client/regulatory reports; the file-share exports Sterling produces today, plus AMMC/ASFIM. | P1 |
| M8 | **Reconciliation & data quality** | Positions/cash vs Maroclear + dépositaire; NAV vs recompute; break management. | P2 |
| M9 | **Risk & analytics** | Exposure, sensitivities (duration/convexity), limits, scenario/stress. | P2 |
| M10 | **CRM / KYC / AML** | Client onboarding, suitability, subscriptions/redemptions (if Sterling owns the TA function). | P3 |
| M11 | **Accounting** | Fund accounting / ledgers to the extent Fanar becomes system-of-record. | P3 |
| M12 | **Control plane** ✦ | Scheduling, run history, notifications, job UI, audit — the productised `sterling-automation` platform. Cross-cutting, built in P0. | P0 |

### 2. Domain model (core entities)

The money-path entities. Field lists are indicative, not a schema (DDL lives with the code).

> **Now grounded:** [`05-domain-model-and-api.md`](05-domain-model-and-api.md) gives the concrete,
> field-level model captured live from Manar (NAV/VL record, repo operation, **poste** posting-rules,
> securities master, maker-checker) plus the ACL mapping. Build against `05`; the list below is the
> narrative overview.

- **Fund (FCP / OPCVM)** — `id`, `code` (Manar portfolio code e.g. 3983), `name`
  (STERLING BOND…), `type` (bond/equity/money-market/diversified), `currency` (MAD),
  `depositary`, `min_cash`, mandate/limits, lifecycle dates.
- **Instrument** — `id`, `isin`, `figi`, `internal_code`, `type` (BDT/BSF/CD/equity/OPCVM/repo),
  `issuer`, `currency`, `day_count`, coupon schedule, maturity, rating, eligibility flags
  (gov / private / repo-eligible).
- **Price / Rate** — `instrument_id`, `source` (BAM/LSEG/computed), `effective_date`,
  `knowledge_date`, `value`, `curve_point?`.
- **Curve** — `id`, `family` (BAM), `effective_date`, points, fitted model params (NSS factors),
  Kalman state, validation status.
- **Transaction (ledger event)** — immutable: `id`, `fund_id`, `type` (buy/sell/repo-open/
  repo-close/coupon/subscription/redemption/fee…), `instrument_id?`, `quantity`, `price`,
  `amount`, `counterparty?`, `trade_date`, `value_date`, `effective_date`, `knowledge_date`,
  `source_ref` (e.g. Manar ticket id for idempotency), `booked_by`, `approved_by`.
- **Position (derived)** — `fund_id`, `instrument_id` (or cash account), `as_of`,
  `knowledge_date`, `quantity`, `amount`, `pool` (gov/private/borrowed) — a *projection* of the
  ledger, never hand-written.
- **CashAccount / CashPosition** — `fund_id`, `account` (Banque Front…), `currency`, `balance`,
  `as_of`.
- **Repo ticket** — `id`, `borrower_fund`, `lender` (fund or market counterparty), `collateral`
  (instrument + qty), `cash_amount`, `rate`, `start`, `maturity`, `poste` (position mapping),
  `status`, `manar_ref?`.
- **NAV / VL** — `fund_id`, `effective_date`, `knowledge_date`, `net_asset`, `units`,
  `vl_per_unit`, `status` (draft/validated/published), `validation`.
- **Order / Ticket (OMS)** — `id`, `fund_id`(s + allocation), `instrument`, `side`, `qty`,
  `limit`, lifecycle `status`, compliance result, `maker`, `checker`.
- **Party** — counterparties, banks (dépositaire), issuers, clients; LEI where available.
- **AuditEvent** — append-only: `who`, `what`, `when`, `before/after`, `correlation_id`.

**Bitemporality everywhere it matters** (prices, positions, NAV, curves): store both
`effective_date` (the business date a fact is true for) and `knowledge_date` (when Fanar learned
it). This is what makes a defensible NAV restatement possible — borrowed directly from SS&C Geneva.

### 3. API surface (shape, and the anti-corruption layer)

Fanar is **API-first**. Keep the useful part of Manar's convention — a **CQRS split** — but do it
cleanly:

- **Commands** `POST /api/v1/<domain>/commands/<name>` — intent to change state; validated,
  authorised, maker-checker where required; returns an accepted event or a rejection. **Idempotent**
  via a client-supplied `Idempotency-Key` (Sterling's "never book twice" becomes a platform
  guarantee).
- **Queries** `GET /api/v1/<domain>/<resource>?as_of=…&knowledge_date=…` — read projections;
  bitemporal params first-class.
- **Events** — every command emits a domain event to the ledger/stream; projections and
  subscribers (notifications, reconciliation) consume them.

Domains mirror the modules: `reference-data`, `market-data`, `ibor`, `nav`, `treasury`, `oms`,
`reporting`, `recon`, `risk`, `admin`. The **named command/query contract, error envelope, and the
confirmed Fanar↔Manar endpoint mapping** are in [`05-domain-model-and-api.md`](05-domain-model-and-api.md) §2–3.

**Anti-corruption layer (ACL) to Manar.** During the strangler phase Fanar must read from — and,
for booking, sometimes write through — Manar. Encapsulate *all* Manar interaction in one adapter
service that:
- speaks Manar's real API (`/api/<domain>/query|command/...`, Keycloak auth) exactly as
  `sterling-automation` already does, but server-side with vaulted credentials;
- translates Manar payloads ↔ Fanar's domain model;
- enforces **read-only vs write** modes (carry over the `_guard` idea: block `/command/` unless a
  booking is explicitly authorised);
- is the **only** component that knows Manar exists. When a domain is fully migrated, its ACL path
  is deleted — that is literally how we measure strangler progress.

> This replaces today's headless-browser scraping with a single, auditable, server-side adapter —
> and the day Manar is retired, you delete one service, not rewrite the platform.

### 4. Key workflows (the ones that must be excellent)

#### W1 — Daily NAV / VL close ✦
1. Ingest prices/curves (M2); validate (curve + price sanity, vs prior, vs independent source).
2. Project positions & cash from the IBOR ledger as of the business date (M3).
3. Compute net asset per fund and VL per unit (M4), using QuantLib pricing for bonds/échéanciers.
4. **Independent recompute** path cross-checks the primary (Sterling's `validation_vl` becomes a
   native dual-calc). Differences above tolerance raise a break.
5. Human **sign-off** → status `validated` → `published`; history retained bitemporally.
6. Exception-only: a clean day needs no clicks.

#### W2 — Daily treasury & repo plan ✦ (flagship)
Encodes the rules already in `jobs/treso.py` / `tools/treso.py`, made native:
1. Read each fund's cash (Banque Front) and eligible collateral as of the day (from IBOR, not
   scraping).
2. Plan, minimising tickets: **interfund repos first** (short funds borrow from surplus funds,
   giving borrowed securities first, then CD/BSF, then own BDT only if needed; own govvt bonds
   kept for the market); then **market** borrow/placement for the residual.
3. Constraints: every fund keeps ≥ `min_cash` (200k MAD); no ticket < `min_ticket` (1M MAD);
   largest-available-bond first; a fund only lends or only borrows.
4. Output a proposal (synthèse / interfonds / marché / collatéral) with a **booking panel**.
5. **Rehearse** → enters every ticket with saving blocked (preview); **recompute before book** —
   if cash/collateral changed since the proposal, book nothing; **maker-checker** approval; book
   each ticket idempotently; stop at first problem. Full audit of who proposed/approved/booked.

#### W3 — Repo rollover (reconduction) ✦
Detect maturing repos, propose rollovers, book with the same maker-checker + idempotency guarantees.

#### W4 — Order booking (OMS) ✦
Order captured → **compliance/limits gate** (mandate, regulatory, concentration) → maker-checker →
booked (via ACL to Manar initially, direct later) → confirmation → settles → reconciled.

#### W5 — Reconciliation
Scheduled pull of positions/cash from Maroclear + dépositaire → match against IBOR projection →
classify breaks → assign/resolve → sign-off. NAV breaks from W1 feed the same queue.

#### W6 — Reporting & exports ✦
Reproduce today's artefacts (actif_net_vl, compo portefeuilles, histo VL, échéanciers, TAUX) as
first-class reports with stable schemas and the same file-share drops, **plus** AMMC/ASFIM
regulatory outputs. Everything exportable; nothing locked in.

### 5. Control plane (productised `sterling-automation`) ✦

Carry forward — and harden — the genuinely good framework Sterling already has:
- **Jobs** with a clear contract (run/configure, timeout watchdog, single-instance lock).
- **Run history** (append-only, structured — today's `runs.jsonl`), surfaced in a UI.
- **Notifications** on success/failure with key metrics.
- **Control page**: per-capability actions (Run / Preview / **Book**), forms, live progress,
  history, schedule — but now driving **Fanar's own API**, not a scraped browser, and behind
  proper auth (today it is local-only + token; Fanar's is RBAC + MFA).
- **Scheduling** moves off per-workstation Windows Task Scheduler (a review finding: session/
  workstation dependency) to a server-side scheduler with HA.

### 6. Explicitly out of scope (for now)

Transfer agency at scale, multi-tenant SaaS for other managers, non-Moroccan markets, full
front-office EMS/algo trading. Revisit at Option C.
