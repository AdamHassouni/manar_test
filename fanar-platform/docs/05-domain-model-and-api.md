# Fanar — 05 · Grounded domain model & API contract

> **What this is.** The buildable domain model and API contract for Fanar, **grounded in the
> concrete shapes captured from Manar** (see `../../manar-analysis/03`,`04`,`05`). It supersedes the
> indicative entity list in `02` §2–3 — that file stays the narrative; this one is the spec you code
> against.
>
> **Clean-room stance.** These are **Fanar-side** definitions: redesigned, typed, bitemporal, in
> consistent English, with Manar's quirks fixed (e.g. `toutalSouscritpion`→`subscriptionsTotal`,
> `coubre`→`curve`). Each entity lists its **Manar source** purely so the **anti-corruption layer
> (ACL)** can map fields during the strangler phase. No Manar source code is reproduced.

---

## 1. Canonical domain model

Conventions: every money-path fact is **bitemporal** (`effectiveDate` = business date it's true for;
`knowledgeDate` = when Fanar learned it). Amounts carry an explicit `currency` (MAD default). IDs are
Fanar-native; `externalRefs` holds Manar/Maroclear/custodian keys.

### 1.1 Tenant · Operator · Role
- **Tenant** — `id`, `code` (e.g. `entity1`), `name`, settings. *(Manar: tenant on login, everything scoped.)*
- **Operator/User** — `id`, `username`, `displayName`, `roles[]`, `tenantId`. *(Manar: Keycloak user; `realm_access.roles`.)*
- **Role** — `id`, `code`, `permissions[]`, plus **function** ∈ {front, back, risk, cloture} for
  segregation of duties. *(Manar: `operateurFront/Back/Risque` + validation stages.)*

### 1.2 Fund (OPCVM / FCP)
`id`, `code` (e.g. 3983), `name` ("STERLING BOND"), `type` (bond|equity|moneyMarket|diversified),
`currency`, `custodianId` (dépositaire), `securitiesAccountId` (e.g. `T_3983`), `minCash`,
mandate/limits, lifecycle dates. *(Manar: `portefeuille`, `depositairePortefeuille`,
`compteTitrePortefeuille`.)*

### 1.3 Instrument (security master)
`id`, `code`, `isin`, `category` (BDT|BSF|CD|action|OPCVM|repo…), `assetClass` (OBL|TCN|ACT),
`issuerId`, `quotationCurrency`, `settlementCurrency`, `division`, `lotSize` (`quotite`),
`nominal`, `issueDate`, `jouissanceDate`, `maturityDate`, `revisionDate`, `couponFrequency`,
`redemptionFrequency`, `couponMethod`, `interestType`, `rateType`, `rateValue`, `issueSpread`,
`issuePrice`, `redemptionPremium`, `economicSector`, `holdingForm`, `active`, `validationFlag`,
`ticker`, `parentInstrumentId`. *(Manar: `list/titres` — 410 fields incl. `codeIsin`, `categorie`,
`classe`, `emetteur`, `periodiciteCoupon`, `dateEcheance`, `quotite`…)*

### 1.4 PostingRule ("poste") — the accounting backbone
The single most important abstraction to reproduce. Each position/operation type declares how it
books, values, settles and accrues.
`code`, `label`, `assetClass`, `screen`, `sign`, `repoFlag`, `settlementFlag`, `stock`,
`settlementLagDays` (`decalageLivraison`), `valueLagDays` (`decalageValeur`), `priceDecimals`,
and the **linked posts**: `mirrorPost`, `interestPost`, `accruedInterestPost`, `collateralPost`,
`provisionPost`, `mtmInstrumentPost`, `mtmCommitmentPost`, `discountPost`; plus valuation/accounting
handlers (`valuationBean`, `accountingBean`, `deliveryBean`, `settlementBean`, `controlBean`,
`matterBean`) and brokerage tiers. *(Manar: `list/postes` — 186 entries; codes like REPOO/REPOOB/
REPOT/REPOTB, RREPO* for reverse.)*
> **Fanar design:** model this as a declarative **posting-rule table** driving the event→ledger
> projection, rather than hard-coded logic. It's how Manar stays configurable across instruments.

### 1.5 Transaction (immutable ledger event) + Repo specialization
**Transaction (base):** `id`, `operationNumber`, `fundId`, `postingRuleCode`, `assetClass`,
`transactionType` (OBL|TCN|ACT…), `instrumentId`, `quantity`, `price`, `grossAmount`, `netAmount`,
`totalAmount`, `fees`, `tradeDate`, `valueDate`, `deliveryDate`, `maturityDate`,
`settlementCurrency`, `counterpartyId`, `counterpartyCustodianId`, `counterpartySecuritiesAccount`,
`intermediaryId`, `status` (captured|validated|settled|cancelled), **maker-checker**
(`operatorFront`, `operatorBack`, `operatorRisk`, `operatorCancel`), `workflowType`, `workflowStatus`,
`workflowLevel`, `externalRefs`, `freeFields[1..3]`, `effectiveDate`, `knowledgeDate`,
`idempotencyKey`. *(Manar: `repo/list` record — `numeroOperation`, `statut:"V"`, `operateurFront/Back`…)*

**Repo (extends Transaction):** `+ dayCount` (`typeOpc`, e.g. R/360), `placementRate`
(`tauxPlacement`), `forwardRate`/`forwardPrice` (`tauxTerme`), `interest` (`interets`),
`accruedInterest` (`interetCouru`), `placementDays`, `startDate`, `endDate`, `collateralInstrumentId`,
`returnFees`, `spreadPDB`, `budget`, `curvePrice`, `mtmDiff`. **Interfund** = `counterpartyId` is
another `Fund`. *(Manar: repo record fields.)*

### 1.6 Position & CashBalance (derived projections)
- **Position** — `fundId`, `instrumentId`, `postingRuleCode`, `asOf`, `knowledgeDate`, `quantity`,
  `amount`, `pool` (gov|private|borrowed), `securitiesAccount`. *(Manar: `workspace` positions.)*
- **CashBalance** — `fundId`, `account` (e.g. "Banque Front"), `currency`, `balance`,
  `intradayOpen`/`intradayClose`, `asOf`. *(Manar: `banqueFront`, `banqueJour`, `banqueDebJour`,
  `banqueFinJour`; `workspace/position-espece`.)*

### 1.7 Valuation / NAV (VL)
`fundId`, `effectiveDate` (`dateFp`), `knowledgeDate`, `currency`, `grossAsset` (`actifBrut`),
`netAssetPreNav` (`actifNetAvVl`), `netAssetPostNav` (`actifNetApVl`), `navPerUnit` (`vl`),
`unitsPre`/`unitsPost` (`nombreParts*`), `bankAsset`, `bankDay`, `subscriptionsTotal`,
`redemptionsTotal`, **fees** (`management1..3`, `managementManual1..3`, `feeCalcBase`), **provisions**
(`agios`, `provisionsAgiosCumulative`, `provisionsChargesCumulative`, `provision1`),
**accruals** (`accruedCharges`, `accruedIncome`), `status`, and a **three-stage validation**:
`{backValidation, liabilityValidation, closureValidation}` each `{date, operator}`.
*(Manar: `validation-souscription-rachat/dateVL` record.)*
> **Fanar design:** NAV is a **projection** from the ledger + prices, stored bitemporally, with the
> three sign-off stages modelled as workflow transitions (not mutable columns).

### 1.8 Counterparty / Party / Custodian
`id`, `code`, `name` (`description`), `kind` (fund|bank|custodian|broker|issuer|client),
`parentEntity` (`entitePere`), `authorizedFlag`, `closureDate`, `lei?`. *(Manar: `list/tiers` (797),
`list/authorizedTiers` (484); custodians e.g. DWAFA/DSGMB.)*

### 1.9 Curve · CurveType · CurvePoint
- **CurveType** — `code`, `name`, `description`. *(Manar: `coubreTauxByType` — BAM, BAM_ZC,
  FW_BAM_0J/30J, PRIM, REPO, T_EURO_MAD, T_USD_MAD.)*
- **Curve** — `curveTypeCode`, `effectiveDate`, `knowledgeDate`, `points[]`, fitted `nssParams`,
  `kalmanState`, `validationStatus`. **Fanar edge:** native NSS+Kalman modelling (Sterling already has it).
- **Price** — `instrumentId`, `source` (BAM|LSEG|computed), `effectiveDate`, `knowledgeDate`, `value`.

### 1.10 Workflow · Task (maker-checker)
- **WorkflowDefinition** — per `transactionType`: stages, required role functions, `levels`.
  Query `hasWorkflow(screen, type) → {hasAccess, hasWorkflow, targetStatus}`. *(Manar: `param-workflow/*`.)*
- **Task** — `id`, `type` (REPOS|TAUX|DAT|OPC|ACT|…), `refTransactionId`, `status`
  (pending|completed|cancelled), `assignedRole`, `createdBy`, `actedBy`, timestamps. *(Manar: `/taches`, `/tache/find`.)*

### 1.11 Codification / ReferenceData
Generic key-value reference by class: `class`, `code`, `value`, `description`, `active`.
*(Manar: `list/getByClasse?classe=…`, `list/paramCodierByClasse?classe=…`, e.g. `MonetaireBaseCalcul`,
`PeriodeVL`.)* Fanar exposes one **reference-data service** over these.

### 1.12 Job · AuditEvent
- **Job** — `id`, `type`, `input`, `status` (pending|running|ok|failed), timestamps, `log`.
  *(Manar: `/jobs`, `jobs/loadJobs`, `STATUT_JOB_FAILED`.)*
- **AuditEvent** — append-only `{who, what, when, before, after, correlationId}`. Fanar-native
  (Manar's audit is server-side/opaque).

## 2. API contract (Fanar-side)

CQRS, **named + versioned**, bitemporal, idempotent:
- **Command** `POST /api/v1/<domain>/commands/<Name>` + body; header `Idempotency-Key`; returns the
  emitted event or a typed rejection. Maker-checker enforced where `WorkflowDefinition` requires it.
- **Query** `GET|POST /api/v1/<domain>/queries/<Name>?asOf=&knowledgeDate=` — reads projections
  (POST when the filter is large). Bitemporal params first-class.
- **Reference** `GET /api/v1/reference/{class}` — unifies Manar's `getByClasse`/`paramCodierByClasse`.
- **Error envelope** (adopt Manar's, enriched): `{ code, status, traceId, type, message?, details? }`.
- **Events** — every command emits a domain event to the ledger/stream.

Domains: `reference-data`, `market-data`, `ibor`, `nav`, `treasury`, `oms`, `reporting`, `recon`,
`risk`, `admin`.

## 3. Anti-corruption layer — Fanar ↔ Manar mapping

The ACL is the only component that speaks Manar. Confirmed mappings to build first:

| Fanar operation | Manar endpoint (observed) | Notes |
|---|---|---|
| `nav.queries.NavHistory(fund)` | `GET portfolio-management/query/validation-souscription-rachat/dateVL?portefeuille=` | full NAV model |
| `treasury.queries.RepoList` | `POST portfolio-management/query/repo/list?HS=false` | repo records |
| `ibor.queries.CashPositions(fund,date)` | `GET portfolio-management/query/workspace/position-espece` | Banque Front |
| `reference.Instruments` | `POST administration/query/list/titres` | securities master |
| `reference.PostingRules` | `POST administration/query/list/postes` | poste model |
| `reference.Counterparties` | `POST administration/query/list/{tiers,authorizedTiers}` | parties |
| `reference.{class}` | `GET administration/query/list/getByClasse?classe=` · `paramCodierByClasse?classe=` | codifications |
| `market-data.CurveTypes` | `POST administration/query/list/coubreTauxByType` | curve catalogue |
| `workflow.HasWorkflow(screen,type)` | `POST administration/query/param-workflow/hasWorkflow` | maker-checker gate |
| `jobs.List` | `POST administration/query/jobs`, `jobs/loadJobs` | batch jobs |
| *(write) treasury.commands.BookRepo* | `POST portfolio-management/command/repo` | **gated; maker-checker; not exercised in RE** |

ACL rules: replicate the `?HS=` flag verbatim; auth via vaulted service account (Bearer JWT, tenant);
**read-only by default**, `/command/` only behind an explicit, audited booking authorisation
(mirrors Sterling's `_guard`).

## 4. Maker-checker model (confirmed live in Manar)

Manar repos carry distinct `operateurFront` / `operateurBack` / `operateurRisque` and a `statut`
(`V`=validated) with `workflowLevel` — i.e. **segregation of duties is already the production
reality**. Fanar formalises it:
- **Maker** (front) captures → **Checker** (back) validates → optional **Risk** sign-off; each a
  workflow transition recorded with operator + timestamp (never a mutable field).
- `WorkflowDefinition` per `transactionType` decides whether a command needs validation before it
  settles; `hasWorkflow → {hasAccess, hasWorkflow, targetStatus}` is the gate; pending items land as
  **Tasks**. NAV uses the same pattern with three stages (back / liability / closure).

## 5. Open items (to confirm later, read-only)
- **Write payloads** (BookRepo, ValidateNav, order submit) — capture needs explicit approval; shapes
  above cover the read side the ACL needs to *read back* a booking.
- **Other modules** (CRM/KYC, OMS order, Risk ratios AMMC, Accounting) — capture under an entitled
  profile to extend §1.
- **Curve points** payload (post type+date) and reporting render payloads — behind submit controls.
