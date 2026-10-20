"""Booking use case — the end-to-end vertical slice.

`book_transaction` ties the whole stack together:
  1. **Authorize** the caller (maker/checker role) — the principal comes from the BFF session or a
     bearer JWT (login).
  2. **Read reference data** (via the ACL to Manar when live, or the local seed) to validate the fund.
  3. **Append** the transaction event to the append-only IBOR ledger (idempotent).
  4. **Record an audit entry** (who/what/when) linked to the event by correlation id.

Pure orchestration over interfaces — unit-tested with the in-memory store, local reference and
in-memory audit log, so the whole slice is provable offline.
"""
from __future__ import annotations

from dataclasses import replace

from fanar.audit.log import AuditEntry, AuditLog
from fanar.ibor.commands import RecordTransaction, record_transaction
from fanar.ibor.event_store import EventStore
from fanar.reference.service import ReferenceService
from fanar.security.auth import Principal


class UnknownFund(ValueError):
    """The requested fund is not in reference data."""


def book_transaction(
    principal: Principal,
    cmd: RecordTransaction,
    *,
    store: EventStore,
    reference: ReferenceService,
    audit: AuditLog,
) -> dict:
    # 1) authorize
    principal.require("front", "back")

    # 2) read reference (through the ACL when live) and validate the fund
    known_funds = {f.code for f in reference.funds()}
    if known_funds and cmd.fund not in known_funds:
        raise UnknownFund(cmd.fund)

    # 3) append to the ledger, attributed to the caller
    cmd = replace(cmd, tenant=principal.tenant or cmd.tenant, actor=principal.username)
    event = record_transaction(store, cmd)

    # 4) audit
    entry = audit.record(AuditEntry(
        actor=principal.username,
        action="record_transaction",
        target=str(event.aggregate_id),
        at=event.recorded_at,
        details={"instrument": cmd.instrument, "quantity": cmd.quantity,
                 "event_id": event.event_id, "sequence": event.sequence},
        correlation_id=event.event_id,
    ))
    return {"event": event, "audit": entry}
