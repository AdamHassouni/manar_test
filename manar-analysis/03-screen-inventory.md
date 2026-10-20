# Manar — screen inventory (authenticated)
### Captured read-only from `/modules/all-menu`, tenant `entity1` · 2026-10-20

> **Source:** live `GET /api/administration/query/modules/all-menu` for the signed-in user
> (username `HASOUNI@…`, tenant `entity1`). Menus are **server-driven**, so this is the exact,
> authoritative list of screens **this profile** is entitled to. **44 screens / 13 menu groups.**
> Read-only capture; no screen was submitted and no `/command/` was called.
>
> **Entitlement caveat:** this profile carries **Portfolio-Management, Processing, Tools and
> Administration**. The product also contains **CRM/KYC, OMS, Risk-Analysis, Contribution-Attribution
> and Accounting** (seen in the static bundle + i18n) — those are simply **not entitled** to this
> user/tenant, so they don't appear here. Capturing them needs a profile that has them (see §4).

Menu item schema: `{ code, lien (route), menu (i18n key), subItems (group code), ordre }`.

## 1. Group legend

| Group code | Area |
|---|---|
| `PRT_PRT` | Portfolio — Transaction entry (saisie) |
| `PRT_TFX` | Portfolio — Forex |
| `PRT_RPR` | Portfolio — Reporting (journals & statements) |
| `PRS_OPE` | Processing — Operations |
| `PRS_DNM` | Processing — Market data (données de marché) |
| `PRS_REP` | Processing — Portfolio reporting |
| `PRS_TRS` | Processing — Treasury (trésorerie) |
| `PRS_RPT` | Processing — Reporting |
| `TVL` | Processing — Valuation (VL/NAV) |
| `TL_DATA` | Tools — Data (import/interfaces) |
| `TL_RPT` | Tools — Reporting |
| `ADM_REF` | Administration — Reference data (référentiel) |
| `ADM_HBT` | Administration — Access control (habilitations) |

## 2. Full screen inventory (44)

### Portfolio — Transaction entry · `PRT_PRT`
| Code | Route | Screen |
|---|---|---|
| PRT_STR | `/portfolio-management/portfolio/transactions/action` | Equities (actions) |
| PRT_CTR | `/portfolio-management/portfolio/transactions/taux` | Rate/bond transactions (taux — BDT) |
| PRT_SRP | `/portfolio-management/portfolio/transactions/repo` | Repos (pensions) |
| PRT_SPE | `/portfolio-management/portfolio/transactions/pret-emprunt-titre` | Securities lending/borrowing |
| PRT_DAT | `/portfolio-management/portfolio/transactions/dat` | Term deposits (DAT) |
| PRT_OPC | `/portfolio-management/portfolio/transactions/opc` | Funds (OPCVM) |
| PRT_DVI | `/portfolio-management/portfolio/transactions/divers` | Miscellaneous |

### Portfolio — Forex · `PRT_TFX`
| Code | Route | Screen |
|---|---|---|
| PRT_CAC | `/portfolio-management/portfolio/forex/change-comptant` | Spot FX (change au comptant) |

### Portfolio — Reporting · `PRT_RPR`
| Code | Route | Screen |
|---|---|---|
| PRT_RJE | `…/reporting/journal-especes` | Cash journal |
| PRT_RJL | `…/reporting/journal-livraisons` | Deliveries journal |
| PRT_RJO | `…/reporting/journal-operations` | Operations journal |
| PRT_RJT | `…/reporting/journal-operations-temporaires` | Temporary-operations journal (repos) |
| PRT_RJV | `…/reporting/journal-pmv` | Gains/losses journal (PMV) |
| PRT_RRE | `…/reporting/releve-espece` | Cash statement |
| PRT_RMT | `…/reporting/releve-mouvements-titres` | Securities-movements statement |
| PRT_RRP | `…/reporting/releve-periodique` | Periodic statement |
| PRT_RRT | `…/reporting/releve-titres` | Securities statement |

### Processing — Operations · `PRS_OPE`
| Code | Route | Screen |
|---|---|---|
| PRS_GDC | `/processing/operations/collateral` | Collateral management |
| PRS_DEN | `/processing/operations/denouement` | Settlement (dénouement) |
| PRS_REG | `/processing/operations/reglement-isole` | Isolated settlement |
| PRS_VIR | `/processing/operations/virements-internes` | Internal transfers |

### Processing — Market data · `PRS_DNM`
| Code | Route | Screen |
|---|---|---|
| ATT | `/processing/donnee-de-marche/analyse-titre-taux` | Rate-security analysis |
| CRB_TX | `/processing/donnee-de-marche/courbe-des-taux` | Yield curves (courbe des taux) |
| JRFR | `/processing/donnee-de-marche/jours-feries` | Holiday calendar |
| PCD | `/processing/donnee-de-marche/page-de-cotation-devises` | FX quotation page |
| PPCT | `/processing/donnee-de-marche/point-page-cotation` | Securities quotation point |

### Processing — Portfolio reporting · `PRS_REP`
| Code | Route | Screen |
|---|---|---|
| ANVL | `/processing/portefeuilles/reporting/actif-net-vl` | **Net asset & NAV (Actif Net / VL)** |
| DAC | `…/reporting/details-actifs-per-classe` | Assets by class |
| APF | `…/reporting/analyse-frais-pmv` | Fees & gains/losses analysis |
| EIDC | `…/reporting/evolution-indicateurs` | Indicators evolution |
| TFTR | `…/reporting/tombees-futures` | Future cash flows (maturities) |
| ENGMT | `…/reporting/engagements` | Commitments |
| TFND | `…/reporting/tresorerie-fonds` | Fund treasury |
| EACT | `…/reporting/evolutions-actifs` | Assets evolution |

### Processing — Valuation · `TVL`
| Code | Route | Screen |
|---|---|---|
| PRS_VVL | `/processing/portefeuilles/validation_vl` | **NAV validation (validation VL)** |
| PRS_VLP | `/processing/portefeuilles/vl-provisoire` | Provisional NAV |

### Processing — Treasury · `PRS_TRS` / Reporting · `PRS_RPT`
| Code | Route | Screen |
|---|---|---|
| PRS_TTF | `/processing/tresorerie/tombees-futures` | Treasury — future cash flows |
| PRS_RTF | `#` (report action) | Reporting — future cash flows |

### Tools · `TL_DATA` / `TL_RPT`
| Code | Route | Screen |
|---|---|---|
| PRS_IXML | `/administration/tools/data/importation` | Interface import (XML) |
| RPT_PRS | `/administration/tools/reporting/rapports-personnels` | Personal reports |

### Administration — Reference & access · `ADM_REF` / `ADM_HBT`
| Code | Route | Screen |
|---|---|---|
| ADM_REF_TTR | `/administration/referentiel/titre` | **Securities reference data (titres)** |
| ADM_LIC | `/administration/licence/detail` | Licence detail |
| ADM_USO | `/administration/profils/profils-list` | Profiles (roles) |
| ADM_USM | `/administration/users/utilisateurs-list` | Users |

## 3. What this confirms about the domain

- **The transaction taxonomy is explicit and central**: `action, taux, repo, pret-emprunt-titre,
  dat, opc, divers` + spot FX — exactly the instruments Sterling trades, each with its own entry
  screen and (per `01`) its own workflow/maker-checker.
- **A full middle/back-office**: operations (collateral, settlement/dénouement, internal transfers),
  market data (yield curves, holidays, quotations), valuation (VL validation + provisional VL),
  and a deep **reporting** suite (journals, statements, actif-net-VL, assets-by-class, fees/PMV,
  commitments, fund treasury, future cash flows).
- **Treasury & collateral are first-class** (`PRS_TRS`, `collateral`, temporary-operations journal)
  — aligning with Sterling's biggest automation effort.
- **Reference data + access control** (securities master, profiles, users, licence) round out the
  self-contained platform.

## 4. To extend (needs other profiles/entitlements)

To enumerate CRM/KYC, OMS (ordre-bourse, carnet d'ordre), Risk-Analysis (ratios AMMC, board review),
Contribution-Attribution and Accounting screens, repeat this capture signed in under a profile that
is entitled to those modules (same method: read `/modules/all-menu`). The static bundle already
proves those areas exist (`01` §6); they're just outside this user's menu.
