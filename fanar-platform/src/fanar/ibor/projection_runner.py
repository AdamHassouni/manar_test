"""Projection runner — keeps read models in sync with the append-only ledger.

Design (transactional outbox + LISTEN/NOTIFY):
  * The `events` table **is** the outbox. Migration 0002 adds an `AFTER INSERT` trigger that
    `pg_notify('fanar_events', sequence)` — so it fires only when the appending transaction commits.
  * `catch_up()` is the durable path: per projector, read events with `sequence > checkpoint`,
    apply them in order, advance the checkpoint — all in one transaction. Safe to run anytime;
    resumable after a crash; idempotent.
  * `run_forever()` LISTENs on the channel and calls `catch_up()` on each notification, with a poll
    timeout as a safety net (a missed notification just means catch-up runs on the next poll).

This is an adapter (SQLAlchemy + psycopg); the per-event rule it applies (`position_deltas`) lives
in the pure core and is unit-tested there.
"""
from __future__ import annotations

from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection, Engine

from fanar.domain.events import Event
from fanar.ibor.mapping import row_to_event
from fanar.ibor.projections import position_deltas
from fanar.ibor.schema import checkpoints_table, events_table, positions_table

CHANNEL = "fanar_events"


class Projector(Protocol):
    name: str
    def apply(self, conn: Connection, event: Event) -> None: ...


class PositionProjector:
    """Maintains the `positions` read model by applying per-event deltas (UPSERT)."""

    name = "positions"

    def apply(self, conn: Connection, event: Event) -> None:
        for (fund, instrument), delta in position_deltas(event).items():
            if delta == 0:
                continue
            stmt = pg_insert(positions_table).values(
                fund=fund, instrument=instrument, quantity=delta, updated_sequence=event.sequence,
            ).on_conflict_do_update(
                index_elements=["fund", "instrument"],
                set_={
                    "quantity": positions_table.c.quantity + delta,
                    "updated_sequence": event.sequence,
                },
            )
            conn.execute(stmt)


class ProjectionRunner:
    def __init__(self, engine: Engine, projectors: list[Projector]) -> None:
        self._engine = engine
        self._projectors = projectors

    def catch_up(self) -> int:
        """Apply all un-processed events to each projector. Returns the number applied."""
        applied = 0
        for proj in self._projectors:
            with self._engine.begin() as conn:
                last = conn.execute(
                    select(checkpoints_table.c.last_sequence).where(checkpoints_table.c.projector == proj.name)
                ).scalar()
                if last is None:
                    conn.execute(
                        pg_insert(checkpoints_table)
                        .values(projector=proj.name, last_sequence=0)
                        .on_conflict_do_nothing()
                    )
                    last = 0
                rows = conn.execute(
                    select(events_table).where(events_table.c.sequence > last).order_by(events_table.c.sequence)
                ).all()
                for row in rows:
                    event = row_to_event(row._mapping)
                    proj.apply(conn, event)
                    last = event.sequence
                if rows:
                    conn.execute(
                        update(checkpoints_table).where(checkpoints_table.c.projector == proj.name)
                        .values(last_sequence=last)
                    )
                    applied += len(rows)
        return applied

    def run_forever(self, *, channel: str = CHANNEL, poll_interval: float = 5.0) -> None:  # pragma: no cover
        self.catch_up()
        raw = self._engine.raw_connection()
        try:
            dbapi = raw.driver_connection   # psycopg3 Connection
            dbapi.autocommit = True
            dbapi.execute(f"LISTEN {channel}")
            while True:
                # Block up to poll_interval for a notification, then catch up regardless.
                for _ in dbapi.notifies(timeout=poll_interval, stop_after=1):
                    break
                self.catch_up()
        finally:
            raw.close()


def main() -> None:  # pragma: no cover
    from sqlalchemy import create_engine

    from fanar.config import Settings

    settings = Settings.from_env()
    engine = create_engine(settings.db_dsn, future=True, pool_pre_ping=True)
    ProjectionRunner(engine, [PositionProjector()]).run_forever()


if __name__ == "__main__":   # pragma: no cover
    main()
