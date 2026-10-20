"""Immutable domain events — the spine of the IBOR ledger.

An event is an append-only, **bitemporal** fact:
  * `effective_date` — the business date the fact is true for (valid time).
  * `recorded_at`    — when Fanar learned it (knowledge/transaction time).
Positions, cash and NAV are *projections* folded from these events, never written directly
(docs/03 §1, docs/05 §1). Events are frozen → immutable by construction.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum


class EventType(str, Enum):
    TRANSACTION_CAPTURED = "transaction.captured"
    TRANSACTION_VALIDATED = "transaction.validated"      # maker-checker: checker approved
    TRANSACTION_CANCELLED = "transaction.cancelled"
    REPO_OPENED = "repo.opened"
    REPO_CLOSED = "repo.closed"
    PRICE_OBSERVED = "price.observed"
    NAV_COMPUTED = "nav.computed"
    NAV_VALIDATED = "nav.validated"
    REFERENCE_UPSERTED = "reference.upserted"


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Event:
    """One immutable ledger fact. `sequence` is assigned by the store on append."""
    type: EventType
    aggregate_id: str                 # fund code, instrument code, operation number…
    tenant: str
    payload: dict
    effective_date: date              # valid time (business date)
    event_id: str = field(default_factory=_uuid)
    recorded_at: datetime = field(default_factory=_now)   # knowledge time
    actor: str | None = None          # operator who caused it (maker/checker)
    correlation_id: str | None = None
    idempotency_key: str | None = None   # "never book twice" guarantee
    sequence: int | None = None
