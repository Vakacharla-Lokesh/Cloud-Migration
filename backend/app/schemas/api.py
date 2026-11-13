"""
schemas/api.py — Request and response bodies for FastAPI endpoints.
Kept separate from migration.py (domain models) so each layer owns its types.
"""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ── Inbound ─────────────────────────────────────────────────────────────────

class StartMigrationRequest(BaseModel):
    """Body for POST /api/migration/start"""
    prompt: str = Field(
        ...,
        min_length=10,
        description="Natural language prompt describing the migration",
        examples=["Migrate all resources tagged app=n8n-csp-host from ap-south-1 to us-east-1 using terraform"],
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional. If omitted, a UUID is generated server-side.",
    )


class HITLDecisionRequest(BaseModel):
    """Body for POST /api/migration/{session_id}/decision"""
    decision: Literal["approve", "reject"] = Field(..., description="Human approval decision")
    feedback: str = Field(
        default="",
        description="Optional feedback (required when decision=reject so IaC generator can improve)",
    )


# ── Outbound ─────────────────────────────────────────────────────────────────

class StartMigrationResponse(BaseModel):
    session_id: str
    message: str = "Migration started. Connect to /api/migration/{session_id}/stream for live updates."


class MigrationStatusResponse(BaseModel):
    session_id: str
    current_step: str
    errors: list[str] = []
    # Populated once IaC is generated
    iac_file_path: Optional[str] = None
    generated_iac: Optional[str] = None
    # Populated once HITL gate fires
    awaiting_human: bool = False


class HITLDecisionResponse(BaseModel):
    session_id: str
    decision: str
    message: str


class ErrorResponse(BaseModel):
    detail: str
    session_id: Optional[str] = None


# ── SSE event envelope ────────────────────────────────────────────────────────

class SSEEvent(BaseModel):
    """Shape of every SSE payload sent to the frontend."""
    event: Literal[
        "step_update",
        "iac_ready",
        "hitl_required",
        "hitl_resumed",
        "completed",
        "error",
    ]
    session_id: str
    data: dict[str, Any] = Field(default_factory=dict)