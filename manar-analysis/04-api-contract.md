# Manar — API contract (authenticated capture)
### Observed read-only, tenant `entity1` · 2026-10-20

> Captured by letting the signed-in SPA fire its own calls (reload + navigation) and reading them,
> plus a few direct **GET `/query/`** reads with the app's own bearer token. **No `/command/` was
> ever called; nothing was written or booked.** Only request/response **shapes** are recorded — no
> customer data, tokens, or secrets.

## 1. Conventions

- **Base:** same-origin `http://192.168.1.104/api/<domain>/<side>/<resource>`.
  Domains seen in use: **`administration`**, **`portfolio-management`**; also `notifications`,
  `reporting`, `manar-api` (from the bundle).
- **CQRS:** reads under `…/query/…`, writes under `…/command/…` (writes not exercised).
- **Auth:** `Authorization: Bearer <JWT>` on every call; the JWT (Keycloak, realm `manar`) carries
  `realm_access.roles` used for client-side RBAC. Tenant (`entity1`) is established at login
  (`/auth/login?tenant=…`) and bound to the token/session.
- **Query transport is mixed:** simple reads are **GET**; filtered/paged reads are **POST to a
  `…/query/…` URL with a JSON body** (still read-only by convention). Common params:
  `?HS=true` (seen on several queries), `?currentPage=0&size=20` (paging), `?code=…`,
  `?ecran=…`, `?username=…&type=…`.
- **Errors:** responses carry an `errors: []` array (see échéancier) alongside the payload;
  the app has a rich error-code catalogue (order validation, licence, workflow — see `01` §7).

## 2. Observed endpoints (authenticated)

### administration/query
| Endpoint | Method | Purpose |
|---|---|---|
| `/auth/login?tenant=…` | POST | Login (tenant + credentials) → `user_details` |
| `/auth/sendOTP`, `/auth/verify` | POST | 2FA (when enabled) |
| `/modules/all-menu` | GET | **Full entitled screen list** (see `03`) |
| `/modules/menu?code=…` | GET | Menu hierarchy for a module/code |
| `/licence/checkLicence?tenant=…` | GET | Licence/entitlement gate |
| `/parametrages/findOne?code=…&segment=system` | GET | App parameters |
| `/parametrage-theme/get-theme` | GET | UI theme config |
| `/widgets/get-all`, `/widgets/user-widget?username=…&type=DASHBOARD` | GET | Dashboard widgets |
| `/favoris/getAll?ecran=…`, `/favoris/save`, `/favoris/delete` | GET/POST | User favourites |
| `/notification/findAll?currentPage=&size=&HS=true` | POST | Notifications (paged) |
| `/notification/countUnread`, `/setRead`, `/setReadAll` | GET/POST | Notification state |
| `/jobs?HS=true`, `/jobs/loadJobById`, `/jobs/{id}` | GET/POST | **Batch jobs engine** |
| `/tache/find` | POST | **Tasks / workflow queue** |
| `/users/find`, `/users/get-parametrage` | GET | Users / per-user config |
| `/param-workflow/hasWorkflow`, `/active-type-transactions`, `/typeTransactions` | GET | **Per-type workflow (maker-checker)** |

### portfolio-management/query
| Endpoint | Method | Purpose |
|---|---|---|
| `/dashboard/actions` | GET | Pending operations feed |
| `/echeancier-taux/echeancier?HS=true` | POST | Coupon/maturity schedule + corporate actions |
| `/workspace/position-espece` | GET | Cash positions (from own automation) |
| `/repo/list` | GET | Repo list (from own automation) |
| *(command)* `/command/repo` | POST | Book a repo — **write, not exercised** |

### notifications
| Endpoint | Method | Purpose |
|---|---|---|
| `/alerts/list`, `/alerts/read-lot`, `/alerts/read/{id}` | GET/POST | Alerts |
| `/push/subscribe/{clientId}`, `/push/unsubscribe/{clientId}` | GET | Web-push registration |

## 3. Captured response shapes (fields only, no data)

```jsonc
// GET administration/query/modules/all-menu  → array of:
{ code:string, lien:string, menu:string /*i18n key*/, subItems:string /*group*/,
  ordre:number, module:null, icon:null, moduleIcon:null }

// GET administration/query/parametrage-theme/get-theme
{ id:number, nom:string, modeTheme:string, image:string,
  principal:string, secondaire:string, tertiaire:string, quaternaire:string }

// GET administration/query/favoris/getAll?ecran=DASHBOARD  → array of:
{ id:number, ecran:string, libelle:string, filter:string, utilisateur:string, parent:null }

// GET portfolio-management/query/dashboard/actions  → array of (operations feed):
{ num_operation:number, date_operation:string, portefeuille:string, titre:string,
  poste:string, quantite:number, cours:number, statut:string }

// POST portfolio-management/query/echeancier-taux/echeancier?HS=true
{ ost:[] /*corporate actions*/, operations:[], events:[], dateTombeeDebut:string, errors:[] }

// GET administration/query/widgets/get-all → []   (none configured for this user)
// POST administration/query/jobs?HS=true   → []   (no jobs in window at capture time)
```

**Reading of the operations shape** (`dashboard/actions`): operations are keyed by a numeric
`num_operation`, carry a `portefeuille` (fund), an instrument `titre`, a `poste` (position/account
bucket — matches the "poste" concept in Sterling's repo logic), `quantite`, `cours` (price), a
`date_operation`, and a `statut` (lifecycle state) — a clean template for Fanar's transaction model.

## 4. Contract notes for the rebuild / anti-corruption layer

- The **two-fat-endpoints-per-domain** style (`/query`, `/command`) with the operation in the
  resource path + body is workable but under-documented; Fanar should expose **named, versioned
  commands/queries** with published schemas (`02` of the Fanar spec).
- **`HS=true`** and the GET-vs-POST-query split should be captured exactly in the ACL adapter so
  Fanar can read from Manar during the strangler phase without surprises.
- **Workflow is server-side per transaction type** (`param-workflow/*`) — the ACL must read
  `hasWorkflow`/`typeTransactions` to know whether a booking needs validation before it appears in
  `/tache`.
- **Everything is tenant-scoped**; multi-tenancy is foundational, not optional.

## 5. Remaining to capture (follow-up, read-only)

Per-screen data-query payloads for the entry/reporting screens (e.g. `actif-net-vl`,
`courbe-des-taux`, `validation_vl`, the transaction screens) require **selecting a fund + date in
the UI** to trigger the main query — do this read-only (never submit/`command`) and read the
resulting `/query/` call. Also: capture under a CRM/OMS/Risk-entitled profile to extend `03`.
