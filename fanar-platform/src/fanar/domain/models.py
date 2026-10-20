"""Core domain entities — grounded in docs/05 (field names cleaned/typed; Manar quirks fixed).

These are intentionally a representative slice for Phase 0, not the full schema. Amounts are MAD
unless stated; money-path records are bitemporal (effective_date + knowledge via the event log).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class AssetClass(str, Enum):
    OBL = "OBL"      # bonds (BDT…)
    TCN = "TCN"      # negotiable debt (CD/BSF)
    ACT = "ACT"      # equities
    OPC = "OPC"      # funds


class RoleFunction(str, Enum):
    FRONT = "front"   # maker
    BACK = "back"     # checker
    RISK = "risk"
    CLOTURE = "cloture"


class TxnStatus(str, Enum):
    CAPTURED = "captured"
    VALIDATED = "validated"      # Manar statut "V"
    SETTLED = "settled"
    CANCELLED = "cancelled"


# ---- reference data -----------------------------------------------------------------

@dataclass(frozen=True)
class Fund:
    code: str                    # 3983
    name: str                    # "STERLING BOND"
    type: str = "bond"           # bond|equity|moneyMarket|diversified
    currency: str = "MAD"
    custodian_id: str | None = None          # dépositaire
    securities_account_id: str | None = None # e.g. T_3983
    min_cash: float = 0.0


@dataclass(frozen=True)
class Instrument:
    code: str
    isin: str | None = None
    category: str = ""           # BDT|BSF|CD|action|OPCVM…
    asset_class: AssetClass = AssetClass.OBL
    issuer_id: str | None = None
    quotation_currency: str = "MAD"
    settlement_currency: str = "MAD"
    lot_size: float | None = None            # quotite
    maturity_date: date | None = None
    coupon_frequency: str | None = None
    active: bool = True


@dataclass(frozen=True)
class PostingRule:
    """The "poste" — how a position/operation type books, values, settles and accrues."""
    code: str                    # REPOO, REPOT, REPOOB…
    label: str = ""
    asset_class: AssetClass = AssetClass.OBL
    sign: int = 1
    repo_flag: bool = False
    settlement_lag_days: int = 0
    value_lag_days: int = 0
    mirror_post: str | None = None
    interest_post: str | None = None
    accrued_interest_post: str | None = None
    collateral_post: str | None = None
    provision_post: str | None = None
    mtm_instrument_post: str | None = None


@dataclass(frozen=True)
class Counterparty:
    code: str
    name: str = ""
    kind: str = "bank"           # fund|bank|custodian|broker|issuer|client
    parent_entity: str | None = None
    authorized: bool = True


@dataclass(frozen=True)
class Codification:
    cls: str                     # e.g. "MonetaireBaseCalcul", "PeriodeVL"
    code: str
    value: str = ""
    description: str = ""
    active: bool = True


@dataclass(frozen=True)
class CurveType:
    code: str                    # BAM, BAM_ZC, FW_BAM_0J, PRIM, REPO, T_EURO_MAD…
    name: str = ""
    description: str = ""


# ---- transactions -------------------------------------------------------------------

@dataclass
class Transaction:
    operation_number: int | None
    fund: str
    posting_rule: str            # poste code
    asset_class: AssetClass
    instrument: str
    quantity: float
    price: float
    gross_amount: float = 0.0
    net_amount: float = 0.0
    trade_date: date | None = None
    value_date: date | None = None
    maturity_date: date | None = None
    counterparty: str | None = None
    status: TxnStatus = TxnStatus.CAPTURED
    # maker-checker (confirmed live in Manar: operateurFront/Back/Risque)
    operator_front: str | None = None
    operator_back: str | None = None
    operator_risk: str | None = None
    workflow_level: int = 0
    idempotency_key: str | None = None


@dataclass
class Repo(Transaction):
    """Repo specialisation (docs/05 §1.5). Interfund when `counterparty` is a Fund code."""
    day_count: str = "R/360"
    placement_rate: float = 0.0
    forward_price: float = 0.0
    interest: float = 0.0
    accrued_interest: float = 0.0
    start_date: date | None = None
    end_date: date | None = None
    collateral_instrument: str | None = None


# ---- valuation ----------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationStage:
    date: date | None = None
    operator: str | None = None


@dataclass
class Valuation:
    """NAV / VL record (docs/05 §1.7). A projection of the ledger + prices, stored bitemporally."""
    fund: str
    effective_date: date
    currency: str = "MAD"
    gross_asset: float = 0.0
    net_asset_pre_nav: float = 0.0
    net_asset_post_nav: float = 0.0
    nav_per_unit: float = 0.0
    units_pre: float = 0.0
    units_post: float = 0.0
    subscriptions_total: float = 0.0
    redemptions_total: float = 0.0
    management_fees: float = 0.0
    status: str = "draft"        # draft|validated|published
    back_validation: ValidationStage = field(default_factory=ValidationStage)
    liability_validation: ValidationStage = field(default_factory=ValidationStage)
    closure_validation: ValidationStage = field(default_factory=ValidationStage)


# ---- workflow / maker-checker -------------------------------------------------------

@dataclass(frozen=True)
class WorkflowGate:
    """Result of the maker-checker gate (Manar: param-workflow/hasWorkflow)."""
    has_access: bool = False
    has_workflow: bool = False
    target_status: str | None = None
