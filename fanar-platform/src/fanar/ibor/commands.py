"""Command handlers for the IBOR ledger (stdlib — unit-tested with the in-memory store).

A command expresses intent to change state; the handler validates it, builds the immutable
`Event`, and appends it to the store (idempotent via the command's idempotency key). The FastAPI
route is a thin wrapper over these functions, so the business logic is testable without a web server.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fanar.domain.events import Event, EventType
from fanar.ibor.event_store import EventStore


@dataclass
class RecordTransaction:
    fund: str
    instrument: str
    quantity: float
    effective_date: date
    sign: int = 1
    status: str = "validated"          # "captured" | "validated"
    tenant: str = "entity1"
    actor: str | None = None
    idempotency_key: str | None = None


def record_transaction(store: EventStore, cmd: RecordTransaction) -> Event:
    """Append a transaction event to the ledger and return it (with its assigned sequence)."""
    event_type = (
        EventType.TRANSACTION_VALIDATED if cmd.status == "validated"
        else EventType.TRANSACTION_CAPTURED
    )
    event = Event(
        type=event_type,
        aggregate_id=cmd.fund,
        tenant=cmd.tenant,
        payload={
            "fund": cmd.fund,
            "instrument": cmd.instrument,
            "quantity": cmd.quantity,
            "sign": cmd.sign,
        },
        effective_date=cmd.effective_date,
        actor=cmd.actor,
        idempotency_key=cmd.idempotency_key,
    )
    return store.append(event)
