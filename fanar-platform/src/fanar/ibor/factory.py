"""Select an EventStore implementation from settings.

Lazy imports keep the stdlib core (and its tests) free of SQLAlchemy. `env == "test"` or an empty
DSN yields the in-memory store; otherwise the Postgres store.
"""
from __future__ import annotations

from fanar.config import Settings
from fanar.ibor.event_store import EventStore


def build_event_store(settings: Settings) -> EventStore:
    if settings.env == "test" or not settings.db_dsn:
        from fanar.ibor.event_store import InMemoryEventStore
        return InMemoryEventStore()
    from sqlalchemy import create_engine
    from fanar.ibor.pg_event_store import SqlAlchemyEventStore
    engine = create_engine(settings.db_dsn, future=True, pool_pre_ping=True)
    return SqlAlchemyEventStore(engine)
