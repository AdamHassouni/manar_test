# Fanar — a better Manar

Development specification and build plan for an **owned, modern Investment Book of Record and
operations platform** for Sterling Asset Management — designed to subsume the `sterling-automation`
framework and **progressively replace** the vendor platform **Manar** (Perenity 8.1.9.6).

**Specs + a Phase 0 scaffold.** The `docs/` are the design; `src/fanar/` + `tests/` are the runnable
Phase 0 skeleton (IBOR event-store spike, read-only ACL to Manar, reference-data service, security
baseline) — see [`SKELETON.md`](SKELETON.md). No Manar source is copied; Manar is a *functional
reference* and the strangler target. See `docs/00` §3 for the clean-room / IP ground rules.

**Quickstart:** `cd fanar-platform && PYTHONPATH=src python -m unittest discover -s tests -t . -v` (49 tests, green).

## Read in order
1. [`docs/00-overview-and-scope.md`](docs/00-overview-and-scope.md) — context, clean-room rules,
   goals, scope options (recommended: **strangler**), gating decisions.
2. [`docs/01-reference-benchmarking.md`](docs/01-reference-benchmarking.md) — comparable platforms
   (Aladdin, SimCorp, SS&C Geneva/Moxy, Enfusion, Limina, Charles River, Clearwater, Murex/Calypso,
   QuantLib…), what to borrow, how Fanar differs, scorecard.
3. [`docs/02-functional-spec.md`](docs/02-functional-spec.md) — modules, domain model, API surface,
   anti-corruption layer, key workflows (NAV close, treasury/repo, booking).
4. [`docs/03-architecture-and-nfr.md`](docs/03-architecture-and-nfr.md) — target architecture, stack,
   data, **security findings → design matrix**, NFRs, integrations, migration.
5. [`docs/04-build-plan-and-roadmap.md`](docs/04-build-plan-and-roadmap.md) — phases, MVP, team,
   effort, risks, next steps, decision log.
6. [`docs/05-domain-model-and-api.md`](docs/05-domain-model-and-api.md) — **buildable** domain model
   + API contract, grounded in the live Manar capture (`../manar-analysis/`), with the Fanar↔Manar
   anti-corruption-layer mapping.

## One-paragraph summary
Fanar is built around an **event-sourced IBOR** (one ledger → derived positions/cash/NAV,
bitemporal like SS&C Geneva), is **API-first with CQRS** (Manar's query/command split done
cleanly), and **automation-native** (the good parts of `sterling-automation` — jobs, run history,
notifications, maker-checker "preview → book" — productised on a real API instead of screen
scraping). It fixes every finding in the infrastructure review by construction (HTTPS, PKCE+MFA,
Vault, no `localStorage` tokens, supported stack, server-side scheduling, immutable audit). It
flags **treasury/repo/collateral** and the **modelled BAM yield curve** as genuine differentiators
over both Manar and global vendors, and treats **Moroccan market/regulatory fit** (AMMC, Maroclear,
BAM, local instruments & calendar) as core rather than customisation.

**Status:** Draft v0.1. Four gating decisions (mandate, ambition, system-of-record constraint,
booking authority) + a legal/licence checkpoint need answers before build spend — see `docs/00` §7
and `docs/04` §7.
