"""Postgres-backed EventStore (SQLAlchemy sync engine) — same interface as InMemoryEventStore.

Append-only (the database also enforces it with a trigger, see migrations/versions/0001). The
`sequence` is assigned by the DB identity column; idempotency is enforced by the unique index on
`idempotency_key`, so a duplicate raises `DuplicateEventError` just like the in-memory store.
"""
from __future__ import annotations

from dataclasses import replace

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from fanar.domain.events import Event
from fanar.ibor.event_store import DuplicateEventError
from fanar.ibor.mapping import event_to_columns, row_to_event
from fanar.ibor.schema import events_table


class SqlAlchemyEventStore:
    """Implements the `EventStore` Protocol over a Postgres database."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def append(self, event: Event) -> Event:
        stmt = (
            insert(events_table)
            .values(**event_to_columns(event))
            .returning(events_table.c.sequence)
        )
        try:
            with self._engine.begin() as conn:
                sequence = conn.execute(stmt).scalar_one()
        except IntegrityError as exc:   # unique(event_id) or unique(idempotency_key)
            raise DuplicateEventError(event.idempotency_key or event.event_id) from exc
        return replace(event, sequence=int(sequence))

    def stream(self, aggregate_id: str) -> list[Event]:
        stmt = (
            select(events_table)
            .where(events_table.c.aggregate_id == aggregate_id)
            .order_by(events_table.c.sequence)
        )
        with self._engine.connect() as conn:
            return [row_to_event(row._mapping) for row in conn.execute(stmt)]

    def all(self) -> list[Event]:
        stmt = select(events_table).order_by(events_table.c.sequence)
        with self._engine.connect() as conn:
            return [row_to_event(row._mapping) for row in conn.execute(stmt)]
