# Manar — reverse-engineering & architecture

Evidence-based map of how the **Manar** platform (Perenity, v8.1.9.6) works, to guide a clean-room
rebuild and targeted REA. **Read-only, interface/behaviour only — no vendor source reproduced.**

- [`01-manar-architecture.md`](01-manar-architecture.md) — detailed architecture with diagrams:
  system context, frontend, server-driven routing/menu, auth/identity flow, CQRS API, module/screen
  map, transaction & workflow model, inferred domain model, confirmed/to-verify matrix.
- [`02-rea-plan.md`](02-rea-plan.md) — how to use REA best here: version baseline, read-only
  guardrails, and the **authenticated capture workflow** that enumerates every server-driven screen
  and the exact query/command payloads.
- [`03-screen-inventory.md`](03-screen-inventory.md) — **authenticated capture**: the full 44-screen
  inventory (codes, routes, labels) for tenant `entity1` from `/modules/all-menu`.
- [`04-api-contract.md`](04-api-contract.md) — **authenticated capture**: the API contract
  (conventions, observed endpoints, captured response shapes) for the anti-corruption layer.
- [`05-screen-payloads.md`](05-screen-payloads.md) — **authenticated capture**: per-screen data-query
  payload shapes + the core domain models (NAV/VL record, repo operation, securities master, poste
  posting-rule, reference lists, curve catalogue, maker-checker). Read-only; field shapes only.

**Method:** derived statically from the served frontend (webpack runtime + 11 lazy chunks ~2.9 MB,
i18n 7,243 keys, app config), the infrastructure/security review, and Sterling's own automation
(the API it already calls). No login, no writes, no bookings.

**Headline finding:** Manar is a **metadata/workflow-driven, multi-tenant SPA** — Angular 14 + hash
routing; menus/routes built server-side from licence entitlements (`/modules/menu`,
`/licence/checkLicence`); **CQRS** per domain (`…/query` · `…/command`); **Keycloak** auth (password
grant + app login + optional OTP, tokens in browser storage); a **per-transaction-type
workflow/maker-checker** engine surfaced as tasks; a **batch jobs** engine; config-driven params;
persisted user dashboards. The full per-module screen inventory is **server-driven**, so it's
enumerated in the authenticated pass (`02` §3), not from the static bundle.

**Status:** static pass complete. Authenticated walk-through pending your login.
