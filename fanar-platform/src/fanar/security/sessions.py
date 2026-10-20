"""Server-side session store for the BFF — pure stdlib, unit-tested.

Tokens live here (server side), keyed by an opaque session id that the browser holds only in an
httpOnly/secure/same-site cookie. In-memory for dev; a Redis/DB store implements the same Protocol
for production (sessions must survive restarts and be shared across instances).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol

from fanar.security.pkce import random_token


@dataclass
class Session:
    id: str
    data: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class SessionStore(Protocol):
    def create(self, data: dict) -> Session: ...
    def get(self, session_id: str) -> Session | None: ...
    def delete(self, session_id: str) -> None: ...


class InMemorySessionStore:
    """Dev store. `ttl_seconds=0` disables expiry."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._by_id: dict[str, Session] = {}
        self._ttl = ttl_seconds

    def create(self, data: dict) -> Session:
        session = Session(id=random_token(), data=dict(data))
        self._by_id[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        session = self._by_id.get(session_id)
        if session is None:
            return None
        if self._ttl and (time.time() - session.created_at) > self._ttl:
            self._by_id.pop(session_id, None)
            return None
        return session

    def delete(self, session_id: str) -> None:
        self._by_id.pop(session_id, None)
