"""SQLAlchemy table for the append-only event log (adapter — imports SQLAlchemy).

Kept separate from the stdlib core so `fanar.ibor.event_store` / `projections` / `mapping` stay
dependency-free. This `metadata` is also Alembic's target_metadata.
"""
from __future__ import annotations

from sqlalchemy import BigInteger, Column, Date, DateTime, MetaData, Numeric, String, Table, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = MetaData()

events_table = Table(
    "events",
    metadata,
    Column("sequence", BigInteger, primary_key=True, autoincrement=True),   # global order
    Column("event_id", UUID(as_uuid=False), nullable=False, unique=True),
    Column("type", String, nullable=False),
    Column("aggregate_id", String, nullable=False),
    Column("tenant", String, nullable=False),
    Column("effective_date", Date, nullable=False),                          # valid time
    Column("recorded_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("actor", String),
    Column("correlation_id", String),
    Column("idempotency_key", String, unique=True),                          # never book twice
    Column("payload", JSONB, nullable=False),
)

# Read models (projections) — rebuilt from the ledger; never written by hand.
positions_table = Table(
    "positions",
    metadata,
    Column("fund", String, primary_key=True),
    Column("instrument", String, primary_key=True),
    Column("quantity", Numeric, nullable=False, server_default=text("0")),
    Column("updated_sequence", BigInteger, nullable=False),
)

# One row per projector: the last event `sequence` it has applied (durable catch-up point).
checkpoints_table = Table(
    "projection_checkpoints",
    metadata,
    Column("projector", String, primary_key=True),
    Column("last_sequence", BigInteger, nullable=False, server_default=text("0")),
)
