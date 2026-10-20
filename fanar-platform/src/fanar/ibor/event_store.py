"""Append-only, bitemporal event store (IBOR spine) — Phase 0 spike.

A storage interface plus an in-memory implementation good enough to exercise the
ledger -> projection pattern in tests without a database. The production store (Postgres: an
append-only `events` table + transactional outbox + LISTEN/NOTIFY) implements the same `EventStore`
Protocol and swaps in behind it.

Invariants:
  * append-only — no update, no delete (restatement is a *new* event, bitemporally).
  * monotonic `sequence` assigned on append (global order).
  * idempotency — a repeated `idempotency_key` is rejected, so "never book twice" is a platform
    guarantee rather than per-job discipline (docs/02, docs/05).
"""
from __future__ import annotations

from dataclasses import replace
from typing import Protocol, runtime_checkable

from fanar.domain.events import Event


class DuplicateEventError(RuntimeError):
    """Raised when an event with an already-seen idempotency key is appended."""


@runtime_checkable
class EventStore(Protocol):
    def append(self, event: Event) -> Event: ...
    def stream(self, aggregate_id: str) -> list[Event]: ...
    def all(self) -> list[Event]: ...


class InMemoryEventStore:
    """Reference implementation for tests and the spike. Thread-unsafe by design (single-writer)."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._seen_keys: set[str] = set()

    def append(self, event: Event) -> Event:
        if event.idempotency_key and event.idempotency_key in self._seen_keys:
            raise DuplicateEventError(event.idempotency_key)
        stored = replace(event, sequence=len(self._events) + 1)
        self._events.append(stored)
        if stored.idempotency_key:
            self._seen_keys.add(stored.idempotency_key)
        return stored

    def stream(self, aggregate_id: str) -> list[Event]:
        return [e for e in self._events if e.aggregate_id == aggregate_id]

    def all(self) -> list[Event]:
        return list(self._events)
