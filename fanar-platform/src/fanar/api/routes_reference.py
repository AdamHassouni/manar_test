"""Reference-data routes — GET-only reads over the ReferenceService.

The service is resolved per request from `get_reference_service` (local seed by default, or live
Manar via the ACL when `FANAR_REFERENCE_SOURCE=manar` — always read-only).
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from fanar.api.deps import get_reference_service
from fanar.reference.service import ReferenceService

router = APIRouter()


@router.get("/funds")
def funds(service: ReferenceService = Depends(get_reference_service)) -> list[dict]:
    return [asdict(f) for f in service.funds()]


@router.get("/posting-rules")
def posting_rules(service: ReferenceService = Depends(get_reference_service)) -> list[dict]:
    return [asdict(p) for p in service.posting_rules()]


@router.get("/counterparties")
def counterparties(service: ReferenceService = Depends(get_reference_service)) -> list[dict]:
    return [asdict(c) for c in service.counterparties()]


@router.get("/curve-types")
def curve_types(service: ReferenceService = Depends(get_reference_service)) -> list[dict]:
    return [asdict(c) for c in service.curve_types()]


@router.get("/codifications/{cls}")
def codifications(cls: str, service: ReferenceService = Depends(get_reference_service)) -> list[dict]:
    return [asdict(c) for c in service.codifications(cls)]
