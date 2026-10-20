"""FastAPI application — thin HTTP surface over the core services.

Run: `uvicorn fanar.api.app:app` (needs the project deps installed; see pyproject). The stdlib
core and its tests do not import this module.
"""
from __future__ import annotations

from fastapi import FastAPI

from fanar import __version__
from fanar.api.routes_reference import router as reference_router
from fanar.config import Settings

settings = Settings.from_env()
app = FastAPI(title="Fanar API", version=__version__)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "env": settings.env, "tenant": settings.tenant}


app.include_router(reference_router, prefix="/api/v1/reference", tags=["reference"])
