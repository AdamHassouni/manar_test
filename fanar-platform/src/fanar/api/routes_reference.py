"""Reference-data routes — GET-only reads over the ReferenceService.

Defaults to the offline LocalReferenceSource so the app runs without Manar; wiring swaps in
ManarReferenceSource (through the ACL) when reading live reference data.
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from fanar.reference.service import LocalReferenceSource, ReferenceService

router = APIRouter()
_service = ReferenceService(LocalReferenceSource())


@router.get("/funds")
def funds() -> list[dict]:
    return [asdict(f) for f in _service.funds()]


@router.get("/posting-rules")
def posting_rules() -> list[dict]:
    return [asdict(p) for p in _service.posting_rules()]


@router.get("/counterparties")
def counterparties() -> list[dict]:
    return [asdict(c) for c in _service.counterparties()]


@router.get("/curve-types")
def curve_types() -> list[dict]:
    return [asdict(c) for c in _service.curve_types()]


@router.get("/codifications/{cls}")
def codifications(cls: str) -> list[dict]:
    return [asdict(c) for c in _service.codifications(cls)]
