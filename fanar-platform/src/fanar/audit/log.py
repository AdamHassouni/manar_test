"""Audit entries and an in-memory append-only log (stdlib — unit-tested).

Every state-changing action records an entry (who/what/when/correlation) so the system is
attributable end to end (docs/03 §4). The Postgres-backed log implements the same Protocol.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Protocol


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AuditEntry:
    actor: str
    action: str
    target: str
    at: datetime = field(default_factory=_now)
    details: dict = field(default_factory=dict)
    correlation_id: str | None = None
    id: str = field(default_factory=_uuid)
    sequence: int | None = None


class AuditLog(Protocol):
    def record(self, entry: AuditEntry) -> AuditEntry: ...
    def recent(self, limit: int = 50) -> list[AuditEntry]: ...


class InMemoryAuditLog:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> AuditEntry:
        stored = replace(entry, sequence=len(self._entries) + 1)
        self._entries.append(stored)
        return stored

    def recent(self, limit: int = 50) -> list[AuditEntry]:
        return list(reversed(self._entries))[:limit]
