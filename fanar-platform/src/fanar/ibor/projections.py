"""Projections — fold the event log into read models (positions, cash, NAV).

A projection is a *pure function of the event stream*: rebuildable from scratch, as-of any date,
which is what makes restatement and audit tractable (docs/03 §1). Phase 0 ships minimal position
and NAV projections to prove the pattern; richer projections (cash ladder, collateral pools) follow.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from fanar.domain.events import Event, EventType

PositionKey = tuple[str, str]   # (fund, instrument)


def project_positions(events: list[Event], as_of: date | None = None) -> dict[PositionKey, float]:
    """Net signed quantity per (fund, instrument) from validated transactions / repos.

    `as_of` filters on **effective_date** (valid time) — ask "what was true on date X".
    Payload shape: {fund, instrument, quantity, sign?}.
    """
    pos: dict[PositionKey, float] = defaultdict(float)
    for e in sorted(events, key=lambda e: (e.effective_date, e.sequence or 0)):
        if as_of and e.effective_date > as_of:
            continue
        p = e.payload
        if e.type in (EventType.TRANSACTION_VALIDATED, EventType.REPO_OPENED):
            pos[(p["fund"], p["instrument"])] += int(p.get("sign", 1)) * float(p.get("quantity", 0))
        elif e.type == EventType.REPO_CLOSED:
            pos[(p["fund"], p["instrument"])] -= float(p.get("quantity", 0))
        elif e.type == EventType.TRANSACTION_CANCELLED:
            pos[(p["fund"], p["instrument"])] -= int(p.get("sign", 1)) * float(p.get("quantity", 0))
    return {k: v for k, v in pos.items() if round(v, 6) != 0}


def latest_nav(events: list[Event], fund: str) -> dict | None:
    """Most recent validated NAV payload for a fund (by effective_date then sequence)."""
    navs = [
        e for e in events
        if e.type == EventType.NAV_VALIDATED and e.payload.get("fund") == fund
    ]
    if not navs:
        return None
    best = max(navs, key=lambda e: (e.effective_date, e.sequence or 0))
    return best.payload


def position_deltas(event: Event) -> dict[PositionKey, float]:
    """The signed position change a single event implies (pure — drives the live projection runner).

    The persisted `positions` read model is updated by *applying* these deltas; the same rule is
    used by `project_positions` for a full rebuild, so live and rebuilt states agree.
    """
    p = event.payload
    if event.type in (EventType.TRANSACTION_VALIDATED, EventType.REPO_OPENED):
        return {(p["fund"], p["instrument"]): int(p.get("sign", 1)) * float(p.get("quantity", 0))}
    if event.type == EventType.REPO_CLOSED:
        return {(p["fund"], p["instrument"]): -float(p.get("quantity", 0))}
    if event.type == EventType.TRANSACTION_CANCELLED:
        return {(p["fund"], p["instrument"]): -int(p.get("sign", 1)) * float(p.get("quantity", 0))}
    return {}
