"""IBOR routes — a command that books through the application service (login -> reference -> ledger
-> audit), plus queries over the projections and the audit trail.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from fanar.api.deps import get_audit_log, get_event_store, get_reference_service, require_principal
from fanar.audit.log import AuditLog
from fanar.ibor.commands import RecordTransaction
from fanar.ibor.event_store import DuplicateEventError, EventStore
from fanar.ibor.projections import project_positions
from fanar.reference.service import ReferenceService
from fanar.security.auth import AuthError, Principal
from fanar.services.transactions import UnknownFund, book_transaction

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
    reference: ReferenceService = Depends(get_reference_service),
    audit: AuditLog = Depends(get_audit_log),
) -> dict:
    cmd = RecordTransaction(**body.model_dump(), idempotency_key=idempotency_key)
    try:
        result = book_transaction(principal, cmd, store=store, reference=reference, audit=audit)
    except AuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except UnknownFund as exc:
        raise HTTPException(status_code=422, detail=f"unknown fund: {exc}") from exc
    except DuplicateEventError as exc:
        raise HTTPException(status_code=409, detail="duplicate idempotency key") from exc
    event = result["event"]
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


@router.get("/audit")
def audit_recent(
    limit: int = 50,
    principal: Principal = Depends(require_principal),
    audit: AuditLog = Depends(get_audit_log),
) -> list[dict]:
    return [asdict(e) for e in audit.recent(limit)]
