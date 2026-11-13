"""
api/routes/health.py — Liveness and readiness probes.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str = "aws-migration-agent"


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/", include_in_schema=False)
async def root():
    return {"message": "AWS Migration Agent API — see /docs"}