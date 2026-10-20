# Manar — screen data-query payloads & domain shapes
### Authenticated read-only capture, tenant `entity1` · 2026-10-20

> **Method.** Navigated read-only (hash routing) to four high-value screens with a **client-side
> write-guard** installed (blocks every `POST/PUT/PATCH/DELETE` that isn't a `/query/` or auth call —
> like Sterling's own `_guard`). Shapes were captured by **replaying the screens' own read queries**
> with the app's bearer token, or by reading the responses the app already fetched. **Only field
> shapes and reference catalogues are recorded — never live amounts, positions, or operator-level
> business data.** No report was generated and **nothing was booked or validated**.
>
> **Note on gated actions.** The "Valider" / submit controls (report generation, VL validation, repo
> booking) are blocked by the auto-mode classifier as potential commits and were **not clicked** —
> which is correct. Fortunately the full data models come from the *read* queries below, so the
> submit step wasn't needed for the shapes.

Every object below is a **shape** (`field: type`), truncated with `…` where long.

---

## 0. Cross-cutting patterns (apply everywhere)

- **Standard error envelope:** `{ code:string, status:string, traceId:string, type:string }`
  (HTTP 500 with this body when a query is malformed). Build the ACL to recognise it.
- **Generic reference-data queries** (reused across screens):
  | Query | Shape | Use |
  |---|---|---|
  | `GET list/getByClasse?classe=<C>` | `{code, value, description}[]` | enum/codifications by class (e.g. `MonetaireBaseCalcul`) |
  | `GET list/paramCodierByClasse?classe=<C>&flagActif=O` | `{…}[]` | parameter codifier by class (e.g. `PeriodeVL`) |
  | `POST list/postes` | *(see §4)* | position/accounting "poste" definitions (186) |
  | `POST list/titres` | *(see §4)* | securities master (410) |
  | `POST list/tiers` / `list/authorizedTiers` | `{code, description, value, entitePere?, dateCloture?}[]` | third parties / counterparties (797 / 484) |
  | `GET list/zonesLibres?code=<screen>` | — | per-screen free/custom fields |
  | `GET parametrages/findOne?code=<c>&segment=<SEG>` | — | screen/segment parameters (e.g. `TAUX_VALO`, `system`) |
  | `POST param-workflow/hasWorkflow` | `{hasAccess:boolean, hasWorkflow:boolean, targetStatus:null}` | **maker-checker gate** per screen/type |
- **`?HS=` flag** appears on most queries (`true/false/undefined`); replicate verbatim in the ACL.

## 1. Actif Net VL (`ANVL`, `/processing/portefeuilles/reporting/actif-net-vl`)

Selectors: **Portefeuille** (fund) → **Date VL**. Selecting a fund fires the NAV feed below; the
"Valider" button only *renders* the report (blocked, not needed).

```jsonc
// GET portfolio-management/query/validation-souscription-rachat/dateVL?portefeuille=<code>
// → array of per-date NAV records (the full VL/NAV model):
{ id: { dateFp:string, portefeuille:string },          // business date + fund (composite key)
  entite:string, devise:string, statut:string,
  vl:number,                                            // NAV per unit
  actifBrut:number, actifNetAvVl:number, actifNetApVl:number,
  nombrePartsAvVl:number, nombrePartsApVl:number,       // units before/after
  banqueActif:number, banqueJour:number, banqueDebJour:number, banqueFinJour:number,
  totalSouscritpion:number, totalRachat:number,         // subs/redemptions (sic: typo in API)
  fraisGestion:number, fraisGestion2:number, fraisGestion3:number,
  fraisGestionMan1:number, fraisGestionMan2:number, fraisGestionMan3:number,
  baseDeCalculFraisGestion:number,
  agios:number, opAgios:number, cumulProvisionsAgios:number, cumulProvisionsCharges:number,
  provision1:number, opProvision1:number,
  espChargesEncours:number, espProduitsEncours:number,  // accrued charges/income
  dateValidation:string, dateValidationPassif:string, dateValidationCloture:null,
  operateurBack:string, operateurPassif:string, operateurCloture:null,
  dateFpAvant:string, … }
```
> This single read is the **complete NAV computation + validation model** — gross/net asset, units,
> cash, fees (3 tiers + 3 manual), provisions, accruals, subs/redemptions, and a three-stage
> validation (back / passif / clôture) each with its operator. Directly reusable for Fanar's NAV engine.

## 2. Courbe des taux (`CRB_TX`, `/processing/donnee-de-marche/courbe-des-taux`)

```jsonc
// POST administration/query/list/coubreTauxByType  (note the API's spelling "coubre")
// → the catalogue of yield/FX curves maintained:
{ code:string, value:string, description:string }[]
// observed codes: FW_BAM_0J, FW_BAM_30J, BAM_ZC, BAM, PRIM, REPO, T_EURO_MAD, T_USD_MAD
```
> Manar maintains **BAM spot, BAM zero-coupon, BAM forward (0J/30J), primary-market, a REPO curve,
> and forward-FX curves (EUR/MAD, USD/MAD)**. The curve *points* load after a type+date is chosen
> (behind the blocked "Afficher"); the type catalogue + the NSS/Kalman work Sterling already has
> cover the modelling side.

## 3. Validation VL (`PRS_VVL`, `/processing/portefeuilles/validation_vl`)

Fires `param-workflow/hasWorkflow` → `{hasAccess, hasWorkflow, targetStatus}` (this profile:
`false/false/null` — a read/back-office user, **not** a VL validator), plus `jobs/loadJobs`
(the VL computation jobs) and `list/paramCodierByClasse?classe=PeriodeVL`. The VL data itself is the
same model as §1 (`validation-souscription-rachat/dateVL`). Validation is a **workflowed command**
(not exercised).

## 4. Transaction — Repo (`PRT_SRP`, `/portfolio-management/portfolio/transactions/repo`)

Two panes: **entry form** (left) + **consultation list** (right). On load it fires `repo/list`,
`list/postes`, `list/titres`, `list/tiers`, `list/authorizedTiers`, `getByClasse?classe=MonetaireBaseCalcul`,
`parametrages/findOne?segment=TAUX_VALO`, `param-workflow/hasWorkflow`.

### 4a. Repo operation model
```jsonc
// POST portfolio-management/query/repo/list?HS=false  → array of repo operations:
{ numeroOperation:number, poste:string /*REPOO|REPOOB|REPOT|REPOTB|RREPO…*/, statut:string /*V=validated*/,
  classe:string /*OBL|TCN*/, typeTransaction:string /*OBL|TCN*/, typeOpc:string /*day-count e.g. R/360*/,
  dateSaisie, dateOperation, dateValeur, dateLivraison, dateEcheance, dateDebutOperation, dateFinOperation,
  titre:string, descriptionTitre:string, divisionTitre,
  portefeuille:string, descriptionPortefeuille:string, depositairePortefeuille:string, compteTitrePortefeuille:string,
  contrePartie:string, depositaireContrePartie:string, compteTitreContrePartie:string, intermediaire,
  quantite:number, cours:number, montantBrut:number, montantNet:number, montantTotal:number, fraisTotal:number,
  tauxPlacement:number, tauxTerme:number, taux, interets:number, interetCouru:number, couponCouru,
  nbreJoursPlacement, budget, ppc, spreadPDB, prix, prixCourbe, diffPrixMTM, fraisRetour, montantDevRetour,
  deviseReglement:string, deviseReference:string, devise1:string, tauxChange, deviseConvertible,
  operateurFront:string, operateurBack:string, operateurRisque, operateurAnnul,   // ← maker-checker roles
  modeValidation, workflowTransactionType, statusWorkflow, workflowLevel:number, newOperation:boolean,
  zoneLibre1, zoneLibre2, zoneLibre3, referenceExterne1, referenceExterne2, fraisDto, taxes, horodate, … }
```
**Structural findings (no values disclosed):**
- **Maker-checker is live in production**: records carry distinct `operateurFront` / `operateurBack`
  (and `operateurRisque`) with `statut` and `workflowLevel` — exactly the model Fanar should adopt.
- **Interfund repos** are first-class: a fund's `contrePartie` can be **another fund** (cash fund),
  matching Sterling's interfund-first treasury logic.
- **Custodians per leg**: `depositairePortefeuille` / `depositaireContrePartie` + `compteTitre*`
  (securities accounts like `T_<fund>`).
- **Poste codes** encode the repo leg/direction (`REPO*` vs `RREPO*`, `*B` variants).

### 4b. Securities master (`list/titres`, 410)
```jsonc
{ code:string, codeIsin:string, categorie:string, classe:string, emetteur:string,
  description:string, libCourt:string, label:string, deviseCotation:string, deviseReglement:string,
  division:number, quotite:number, formeDetention:string, flagActif:string, flagValidation:string,
  dateEcheance, dateEmission, dateJouissance, dateRevision, periodiciteCoupon, periodiciteRembou,
  methodeCoupon, typeInteret, typeTaux, valeurTaux, nominal, primeRembou, prixEmission,
  spreadEmission, typeSpreadEmission, secteurEconomique, ticker, titrePere, dateMaj, … }
```

### 4c. Poste (position/accounting type) model (`list/postes`, 186)
```jsonc
{ code:string, label:string, description:string, classe:string, ecran:string, flagActif:string,
  flagRepo:string, flagReglement:boolean, signe, posteSigne:string, stock:number,
  decalageLivraison:number, decalageValeur:number, decimalCours:number,
  posteMiroir, posteCollateral, posteInteret, posteInteretCouru, posteProvision,
  posteMtmInstrument, posteMtmEngagement, posteSdecote,
  beanValorisation, beanComptabilite, beanLivraison, beanReglement, beanControle, beanMatiere,
  courtage1..7, horodate, … }
```
> The **poste** is the backbone accounting concept — each position type declares its mirror post,
> interest/accrued-interest posts, collateral post, MTM posts, provision post, settlement lag,
> sign, and valuation/accounting beans. Fanar's ledger should model an equivalent "posting rule"
> per instrument/operation type.

### 4d. Reference lists
- `list/tiers` (797), `list/authorizedTiers` (484): `{code, description, value, entitePere?}` —
  counterparties, custodians, intermediaries.
- `getByClasse?classe=MonetaireBaseCalcul` (6): `{code, value, description}` — money-market
  day-count/base-calc options.

## 5. Design takeaways for Fanar

1. **The NAV model (§1) and repo model (§4a) are near-complete specs** for Fanar's valuation and
   repo domains — adopt the field sets, drop the typos (`toutalSouscritpion`, `coubre`), and make
   the posting rules explicit.
2. **Maker-checker is already how Manar works** (front/back/risk operators + workflow level) —
   Fanar formalises the same with `hasWorkflow`/`targetStatus` semantics.
3. **The "poste" posting-rule engine (§4c)** is the key accounting abstraction to reproduce.
4. **Generic reference queries (§0)** (`getByClasse`, `paramCodierByClasse`, `postes`, `titres`,
   `tiers`) define the reference-data service Fanar needs first.
5. **Everything is fund + date (`dateFp`) keyed and MAD-denominated**, tenant-scoped — bitemporal,
   multi-tenant foundations confirmed.

## 6. Not captured (gated or out of profile)
- Report *renders* / curve *points* / VL *validation* / repo *booking* — behind submit controls the
  auto-mode classifier blocks (correctly). Their **read models are already captured above**; the
  write payloads would need explicit approval and are out of scope for read-only RE.
- CRM/KYC, OMS, Risk, Contrib-Attrib, Accounting screens — not entitled to this profile (`03` §4).
