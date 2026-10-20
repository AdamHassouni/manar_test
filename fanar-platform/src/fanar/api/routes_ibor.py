"""IBOR routes — a command that appends to the ledger, and queries that read projections."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from fanar.api.deps import get_event_store, require_principal
from fanar.ibor.commands import RecordTransaction, record_transaction
from fanar.ibor.event_store import DuplicateEventError, EventStore
from fanar.ibor.projections import project_positions
from fanar.security.auth import AuthError, Principal

router = APIRouter()


class RecordTransactionIn(BaseModel):
    fund: str
    instrument: str
    quantity: float
    effective_date: date
    sign: int = 1
    status: str = "validated"       # captured | validated


@router.post("/commands/record-transaction", status_code=201)
def record_transaction_cmd(
    body: RecordTransactionIn,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(require_principal),
    store: EventStore = Depends(get_event_store),
) -> dict:
    try:
        principal.require("front", "back")          # maker-checker: only operators may book
    except AuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    cmd = RecordTransaction(
        **body.model_dump(),
        tenant=principal.tenant or "entity1",
        actor=principal.username,
        idempotency_key=idempotency_key,
    )
    try:
        event = record_transaction(store, cmd)
    except DuplicateEventError as exc:
        raise HTTPException(status_code=409, detail="duplicate idempotency key") from exc
    return {"event_id": event.event_id, "sequence": event.sequence, "type": event.type.value}


@router.get("/positions")
def positions(store: EventStore = Depends(get_event_store)) -> list[dict]:
    pos = project_positions(store.all())
    return [{"fund": f, "instrument": i, "quantity": q} for (f, i), q in sorted(pos.items())]


@router.get("/events/{aggregate_id}")
def events(aggregate_id: str, store: EventStore = Depends(get_event_store)) -> list[dict]:
    return [
        {"sequence": e.sequence, "type": e.type.value, "effective_date": e.effective_date.isoformat(),
         "payload": e.payload, "actor": e.actor}
        for e in store.stream(aggregate_id)
    ]
