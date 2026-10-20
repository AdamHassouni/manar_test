# Fanar — 01 · Reference benchmarking

The point of this file: steal the *best proven idea* from each category of mature platform, and be
explicit about where Fanar deliberately differs. None of this implies copying code — these are
design patterns and capabilities, publicly documented, that define what "good" looks like in
investment management software.

> Product facts below are from general industry knowledge (cutoff Jan 2026). Treat vendor specifics
> (exact module names, ownership after acquisitions) as **verify-before-quoting**, not load-bearing.

---

### 1. Front-to-back / IBOR platforms (the shape to aim at)

| Platform | Vendor | The idea worth borrowing |
|---|---|---|
| **Aladdin** | BlackRock | **One position store + risk-first.** Single security master and position/risk truth shared by PM, risk and trading. Risk analytics (factor models, scenario/stress) are not a bolt-on. |
| **SimCorp Dimension / SimCorp One** | SimCorp | **IBOR + integrated accounting.** An Investment Book of Record that reconciles front-office positions with back-office accounting continuously; multi-asset; intraday + end-of-day. |
| **Geneva / APX / Moxy** | SS&C Advent | **Bitemporal "knowledge date" accounting.** Geneva records *effective date* and *knowledge date* separately — restate the past without destroying what you reported. The gold standard for audit & NAV restatement. Moxy = order/trade management. |
| **Enfusion** | Enfusion | **Cloud-native single data model.** OMS + PMS + accounting + analytics over one real-time shared ledger, delivered SaaS. The architectural template for Fanar. |
| **Limina IMS** | Limina | **API-first, event-driven, mid-size fit.** Modern IBOR/PMS for managers the size of Sterling; good UX; integration-friendly. Proof the Fanar ambition is realistic at mid scale. |

**Fanar takeaway:** be built **around an IBOR** — a single event-sourced ledger of transactions
from which positions, cash and NAV are *derived*, never re-scraped. Adopt Geneva's **bitemporal**
model as a first-class requirement. Target Enfusion/Limina's single-model, API-first shape at
Sterling's scale (not Aladdin's enterprise footprint).

### 2. OMS / EMS / compliance (the "booking" done right)

| Platform | The idea worth borrowing |
|---|---|
| **Charles River IMS** (State Street Alpha) | **Pre-/post-trade compliance rules engine** + order lifecycle + **FIX** connectivity. Orders are checked against mandate/regulatory limits *before* they go out. |
| **Bloomberg AIM / TOMS** | Order & execution management with deep market-data integration. |
| **SS&C Moxy** | Trade order management with allocation and modelling for multi-fund orders. |

**Fanar takeaway:** model orders/tickets with an explicit **lifecycle** (proposed → approved →
sent → confirmed → settled), a **compliance/limits check** gate, and **maker-checker** approval.
Sterling already does a primitive version (`treso` "preview → book", recompute-before-book,
never-book-twice) — formalise it. Use **FIX / ISO 20022** vocabulary even if the first counterparties
are reached by other means.

### 3. Investment accounting, reconciliation & data quality

| Platform | The idea worth borrowing |
|---|---|
| **Clearwater Analytics** | **Automated reconciliation + data aggregation as the core product.** Pull from custodians/banks, normalise, reconcile, flag breaks. Data quality is the feature. |
| **Temenos Multifonds** | **Fund accounting + transfer agency**, multi-jurisdiction, strong in francophone/African markets — relevant context for Morocco. |
| **FIS InvestOne / SS&C** | Large-scale fund accounting engines. |

**Fanar takeaway:** build a **reconciliation engine** early (positions/cash vs **Maroclear** and
the **dépositaire** bank; NAV vs independent recompute). Treat **data quality as a module**, not an
afterthought — Sterling already hand-rolls `validation_vl` and `validation_courbe`; make them
native with break management and sign-off.

### 4. Fixed income, treasury, repo & collateral (Sterling's hot path)

| Platform | The idea worth borrowing |
|---|---|
| **Murex MX.3** | Treasury, money-market, **repo and collateral management**, fixed-income analytics — the reference for the exact workflow Sterling automates. |
| **Calypso** (Adenza / Nasdaq) | Repo/securities-finance lifecycle, collateral optimisation, margining. |
| **QuantLib** (open source) | **Bond pricing, yield-curve bootstrapping, day-count conventions, schedules.** Replace the Excel `Pricer-ADAM.xlsm` and hand-rolled échéancier logic with a tested library. |

**Fanar takeaway:** make **treasury + repo + collateral** a flagship native module (it is Sterling's
daily pain and differentiator). Borrow Murex/Calypso's **collateral optimisation** framing for the
interfund-first, cheapest-collateral-first logic Sterling already encodes. Use **QuantLib** for
pricing/curves; keep the **Nelson-Siegel-Svensson + Kalman** curve model Sterling built as a
first-class analytics feature (most vendors don't model the curve, they just store rates — this is
a genuine edge).

### 5. Identity, platform & standards (don't reinvent)

| Component | Choice / idea |
|---|---|
| **Keycloak** | Keep it (Manar already uses it). Do it properly: **authorization-code + PKCE**, **MFA**, short-lived tokens, refresh rotation, **no tokens in `localStorage`** — use secure, httpOnly, same-site cookies with a backend-for-frontend. |
| **FIX 4.4/5.0, ISO 20022, SWIFT** | Messaging/order vocabulary and settlement standards. |
| **OpenFIGI / ISIN / LEI** | Instrument & counterparty identification in the security master. |
| **HashiCorp Vault / cloud KMS** | Secrets — directly answers the plain-text-password finding. |
| **OpenTelemetry, Prometheus, Grafana** | Observability baked in. |

### 6. Morocco-specific reference points (the real operating context)

These are not competitors; they are the regulatory/market environment Fanar must fit — and an area
where global vendors are weak and Sterling can be strong.

- **AMMC** (Autorité Marocaine du Marché des Capitaux) — OPCVM/FCP regulation and reporting.
- **ASFIM** — the fund-management association; industry reporting/standards.
- **Bank Al-Maghrib (BAM)** — reference yield curves, T-bill (BDT) **adjudications**, money market.
- **Maroclear** — central securities depository → the reconciliation counterparty for settlement.
- **Dépositaire** (custodian bank) — independent controls on the manager.
- Instruments & conventions: **BDT** (Bons du Trésor), **BSF**, **CD** (certificats de dépôt),
  **pensions livrées** (repos), MAD, local day-count and the Moroccan + religious holiday calendar
  (Sterling already maintains this in `settings.toml`).

**Fanar takeaway:** native Moroccan market data, calendar, instrument types and **AMMC/ASFIM
regulatory reporting** are a built-in differentiator. Global platforms treat these as costly
customisations; Fanar treats them as the home market.

### 7. Where Fanar deliberately differs from all of them

1. **Automation-native, not automation-friendly.** Every capability is an idempotent API with
   scheduling, run history and notifications built in — because Sterling *starts* from a mature
   automation framework. Most vendors bolt automation on; Fanar is born from it.
2. **Local-market-first.** Moroccan regulation, calendar, instruments and the modelled BAM curve
   are core, not plugins.
3. **Right-sized.** Not an Aladdin/SimCorp enterprise install. A focused IBOR + treasury/ops
   platform for a single mid-size manager, cloud-native and operable by a small team.
4. **Transparent & owned.** Open data model, exportable everything, no vendor lock-in, no
   screen-scraping, full audit. The anti-Manar.

### 8. Scorecard — Manar today vs. Fanar target vs. best-in-class

| Capability | Manar (today, observed) | Best-in-class | Fanar target |
|---|---|---|---|
| Single source of truth / IBOR | Implicit; Sterling re-derives by scraping | Aladdin/SimCorp | Event-sourced IBOR, derived positions/NAV |
| Bitemporal / restatement | Unknown | Geneva | First-class (effective + knowledge date) |
| Treasury/repo/collateral | Manual in UI; Sterling automates externally | Murex/Calypso | Native flagship module |
| Yield-curve modelling | Stores rates | (rare) | NSS + Kalman native analytics |
| OMS lifecycle + compliance gate | Booking screens | Charles River | Explicit lifecycle + limits + maker-checker |
| Reconciliation | Exports to file share | Clearwater | Native engine vs Maroclear/bank |
| Security posture | HTTP, localStorage tokens, EOL Angular | — | HTTPS, PKCE+MFA, vault, immutable audit |
| Automation/API | CQRS API (used via scraping) | Enfusion/Limina | API-first, idempotent, scheduled |
| Local regulatory fit | Present | Temenos (generic) | AMMC/ASFIM native |
