"""Audit table — defined on the shared DB metadata (so Alembic sees it). Adapter (SQLAlchemy)."""
from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, String, Table, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from fanar.ibor.schema import metadata   # one MetaData for the whole DB

audit_table = Table(
    "audit_entries",
    metadata,
    Column("sequence", BigInteger, primary_key=True, autoincrement=True),
    Column("id", UUID(as_uuid=False), nullable=False, unique=True),
    Column("actor", String, nullable=False),
    Column("action", String, nullable=False),
    Column("target", String, nullable=False),
    Column("at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("correlation_id", String),
    Column("details", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
)
