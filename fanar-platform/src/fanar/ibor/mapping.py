"""Pure mapping between `Event` and a database row (dict of column values).

No DB driver is imported here, so it is unit-tested without Postgres. `event_to_columns` omits
`sequence` (the database assigns it); `row_to_event` rebuilds the full Event from a row mapping.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

from fanar.domain.events import Event, EventType


def event_to_columns(event: Event) -> dict[str, Any]:
    """Column values for an INSERT (no `sequence` — the DB generates it)."""
    return {
        "event_id": event.event_id,
        "type": event.type.value,
        "aggregate_id": event.aggregate_id,
        "tenant": event.tenant,
        "effective_date": event.effective_date,
        "recorded_at": event.recorded_at,
        "actor": event.actor,
        "correlation_id": event.correlation_id,
        "idempotency_key": event.idempotency_key,
        "payload": dict(event.payload),
    }


def row_to_event(row: Mapping[str, Any]) -> Event:
    """Rebuild an Event from a selected row (dict or SQLAlchemy RowMapping)."""
    return Event(
        type=EventType(row["type"]),
        aggregate_id=row["aggregate_id"],
        tenant=row["tenant"],
        payload=dict(row["payload"]),
        effective_date=_as_date(row["effective_date"]),
        event_id=str(row["event_id"]),
        recorded_at=row["recorded_at"],
        actor=row.get("actor"),
        correlation_id=row.get("correlation_id"),
        idempotency_key=row.get("idempotency_key"),
        sequence=row.get("sequence"),
    )


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))
