"""Postgres-backed audit log (SQLAlchemy) — same interface as InMemoryAuditLog. Append-only."""
from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from fanar.audit.log import AuditEntry
from fanar.audit.schema import audit_table


class SqlAlchemyAuditLog:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record(self, entry: AuditEntry) -> AuditEntry:
        stmt = insert(audit_table).values(
            id=entry.id, actor=entry.actor, action=entry.action, target=entry.target,
            at=entry.at, correlation_id=entry.correlation_id, details=dict(entry.details),
        ).returning(audit_table.c.sequence)
        with self._engine.begin() as conn:
            sequence = conn.execute(stmt).scalar_one()
        return replace(entry, sequence=int(sequence))

    def recent(self, limit: int = 50) -> list[AuditEntry]:
        stmt = select(audit_table).order_by(audit_table.c.sequence.desc()).limit(limit)
        with self._engine.connect() as conn:
            return [self._row(row._mapping) for row in conn.execute(stmt)]

    @staticmethod
    def _row(m: Mapping) -> AuditEntry:
        return AuditEntry(
            actor=m["actor"], action=m["action"], target=m["target"], at=m["at"],
            details=dict(m["details"]), correlation_id=m["correlation_id"],
            id=str(m["id"]), sequence=m["sequence"],
        )
