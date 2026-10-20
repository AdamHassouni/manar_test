# Fanar — a better Manar
## 00 · Overview, scope & ground rules

> **Codename "Fanar"** (فنار, *lighthouse*) — a placeholder for the platform you own, echoing
> *Manar* (منار, *beacon*). Rename freely.

**Status:** Draft v0.1 — development specification, pre-build.
**Author of record:** Adam Hassouni (Sterling Asset Management).
**Date:** 19 October 2026.

---

### 1. What we are replacing, and why

**Manar** is a commercial buy-side asset-management platform (vendor: **Perenity Software**,
observed version **8.1.9.6**) that Sterling runs on an internal network. From the infrastructure
review and from Sterling's own automation code, its functional surface is:

- An **Angular 14** single-page app talking to a **CQRS REST API** — reads under
  `/api/<domain>/query/...`, writes under `/api/<domain>/command/...`.
- Business domains: **administration, portfolio-management, OMS, accounting, risk-analysis,
  CRM/KYC, contribution-attribution, processing, reporting, notifications**.
- **Keycloak** identity (`/realms/manar`), multi-tenant login, bearer tokens.
- Core domain objects Sterling depends on daily: funds/FCPs, positions (securities + cash),
  NAV / *valeur liquidative* (VL), portfolio composition, repos, collateral, reference rates,
  yield curves, bond schedules (*échéanciers*), transaction booking.

**Why build our own.** Three independent pressures:

1. **Operational.** Sterling already runs a substantial automation layer (`sterling-automation`)
   on top of Manar — driving a headless browser, scraping screens, re-deriving NAV, planning
   treasury, and *booking* repos. This is a sign the vendor product does not cover the real
   workflow; Sterling is already building the missing platform, awkwardly, through the UI.
2. **Risk & maintainability.** The security review found: HTTP-only access, plain-text automation
   passwords on the workstation, an out-of-support Angular 14 frontend, password-grant OAuth with
   tokens in `localStorage`. Several of these are structural to the vendor deployment and cannot
   be fixed by Sterling alone.
3. **Strategic.** Owning the platform turns a fragile "RPA on a vendor UI" into a first-class
   system with its own data model, API, audit trail and UX — and lets Sterling add what Manar
   lacks (real IBOR, proper treasury/repo tooling, modelled yield curves, maker-checker controls).

### 2. The goal, in one sentence

> Build an **owned, modern, API-first Investment Book of Record and operations platform** for a
> Moroccan asset manager, that **subsumes `sterling-automation`**, **progressively replaces
> Manar capability-by-capability**, and is **better** on the axes that hurt today: data truth,
> treasury/repo tooling, security, auditability and automation.

### 3. Ground rules — clean-room & IP (read this first)

This project treats Manar as a **functional reference**, never a source to copy. Concretely:

- **Allowed:** observing *what* Manar does (its feature set); the **API contract** Sterling's own
  code already calls (an interoperability fact Sterling depends on); the **domain model** implied
  by the data Sterling exports; industry standards and published best practice.
- **Not allowed, and not done here:** decompiling or transcribing Perenity's proprietary
  server/business-logic source; lifting their code, data model DDL, or UI verbatim; circumventing
  licensing. Fanar is designed **from requirements**, not reconstructed from their binaries.
- **No live-server reverse engineering** was performed for this spec. If an exact live-API
  enumeration is later wanted, it is a **scoped, read-only** task, authorised explicitly, limited
  to the interface contract Sterling already consumes — not source reconstruction.
- **Secrets hygiene:** the credential files the review flagged (`creds.json`, `secrets/manar.json`)
  were **not** read, displayed, or used. They inform Fanar's secrets design (§ in `03`) and nothing
  more.
- **Legal checkpoint before build:** confirm Sterling's Manar licence/SLA terms on interoperability
  and data extraction, and that this is a sanctioned Sterling initiative (ownership, funding,
  data-governance sign-off). This is a **gating open decision** — see §7.

### 4. Scope options (pick the ambition)

| Option | What it means | Effort | Recommendation |
|---|---|---|---|
| **A. Augment** | Keep Manar as system-of-record; make `sterling-automation` a proper product (own DB, API, UI, security) around it. | ~1–2 eng · 6–9 mo | Floor — do this regardless |
| **B. Strangle** (recommended) | Build Fanar as the new IBOR + operations platform; move capabilities off Manar one domain at a time behind an anti-corruption layer; Manar shrinks to legacy. | ~3–5 eng · 12–24 mo | **Recommended path** |
| **C. Full replace** | Reimplement Manar's entire front-to-back scope (fund accounting, full OMS, compliance, CRM/KYC, regulatory) and retire it. | 8+ eng · 3–5 yr | End-state of B, not a day-one goal |

**Recommended: B (the "strangler fig").** It delivers value continuously, never requires a
big-bang cutover, lets Sterling keep running while Fanar grows, and makes C an *outcome* rather
than an upfront bet. The rest of these specs assume **B**, with the full target architecture (C's
end-state) described so nothing we build early boxes us in.

### 5. What "better" means (the success criteria)

Fanar is better than Manar if, measurably:

1. **One source of truth (IBOR).** Positions, cash and NAV are computed from one event-sourced
   ledger — not re-scraped and re-derived per automation. Target: zero screen-scraping in steady
   state.
2. **Treasury & repo as a first-class product.** The daily interfund + market repo plan,
   collateral selection, and booking (currently bespoke Python) become native, with maker-checker
   controls. Target: treasury plan in <1 min, booked with two-person approval and full audit.
3. **Security by construction.** HTTPS everywhere, OIDC auth-code + PKCE + MFA, no tokens in
   `localStorage`, secrets in a vault, RBAC + segregation of duties, immutable audit log. Every
   finding in the review closed by design (traceability matrix in `03`).
4. **Correctness you can defend.** Bitemporal data (effective date + knowledge/as-of date) so NAV
   restatements and "what did we know when" are first-class. Independent NAV validation and
   reconciliation against the depositary (Maroclear) and the bank.
5. **Automation-native.** Every operation is an API call with an idempotency key; scheduling,
   run history, notifications and a control plane are built in (carry forward the good parts of
   `sterling-automation`). Target: unattended daily close with exception-only human review.
6. **Modern, supported stack.** No end-of-life frameworks; SBOM + patch cadence; test coverage on
   the money paths.

### 6. The document set

- `00-overview-and-scope.md` — this file.
- `01-reference-benchmarking.md` — comparable platforms, what to borrow from each, how we differ.
- `02-functional-spec.md` — modules, domain model, API surface, the key workflows.
- `03-architecture-and-nfr.md` — target architecture, stack, data, **security findings → design**,
  non-functional requirements, integrations.
- `04-build-plan-and-roadmap.md` — strangler strategy, phases/milestones, MVP, team, estimates,
  risks, decision log.
- `05-domain-model-and-api.md` — the **buildable** domain model + API contract, grounded in the live
  Manar capture (`../../manar-analysis/`), with the Fanar↔Manar ACL mapping.

### 7. Gating open decisions (need a human answer)

1. **Mandate & ownership** — is this a sanctioned Sterling project (budget, owner, data governance),
   and are the Manar licence terms compatible with interoperability + building a replacement?
2. **Ambition** — confirm Option **B** (strangle) vs A (augment only) vs C (full replace now). This
   sets team size and timeline.
3. **Regulatory system-of-record** — until Fanar is validated, **Manar stays the official
   system-of-record** for NAV/accounting and regulatory reporting (AMMC/ASFIM). Fanar runs in
   **shadow/parallel** first. Confirm this constraint.
4. **Booking authority** — who may approve a write to the real market/custody chain (maker-checker
   roles), and will early Fanar booking go **through** Manar's API or **direct** to
   counterparties/depositary?

These are tracked in `04` §Decision log.
