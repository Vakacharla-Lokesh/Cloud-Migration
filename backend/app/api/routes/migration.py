"""
api/routes/migration.py — Migration endpoints.

POST   /api/migration/start                    kick off a new migration
GET    /api/migration/{session_id}/status      poll current state
GET    /api/migration/{session_id}/stream      SSE live updates
POST   /api/migration/{session_id}/decision    submit HITL approve/reject
GET    /api/migration/{session_id}/iac         download the generated .tf file
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from app.api.graph_runner import resume_graph, start_graph
from app.api.session_store import session_store
from app.schemas.api import (
    HITLDecisionRequest,
    HITLDecisionResponse,
    MigrationStatusResponse,
    StartMigrationRequest,
    StartMigrationResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/migration", tags=["migration"])


# ── POST /start ───────────────────────────────────────────────────────────────

@router.post(
    "/start",
    response_model=StartMigrationResponse,
    status_code=202,
    summary="Start a migration pipeline",
)
async def start_migration(body: StartMigrationRequest) -> StartMigrationResponse:
    """
    Accepts a natural-language prompt and kicks off the agent pipeline.
    Returns immediately with a session_id; the graph runs in the background.
    Poll /status or connect to /stream for progress.
    """
    session_id = body.session_id or str(uuid.uuid4())

    if session_store.get(session_id):
        raise HTTPException(
            status_code=409,
            detail=f"Session '{session_id}' already exists. Use a different session_id.",
        )

    session_store.create(session_id)
    await start_graph(session_id, body.prompt)

    logger.info("[POST /start] Session %s created", session_id)
    return StartMigrationResponse(session_id=session_id)


# ── GET /status ───────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/status",
    response_model=MigrationStatusResponse,
    summary="Poll migration status",
)
async def get_status(session_id: str) -> MigrationStatusResponse:
    """Lightweight status check — no SSE required."""
    try:
        entry = session_store.get_or_raise(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return MigrationStatusResponse(
        session_id=session_id,
        current_step=entry.current_step,
        errors=entry.errors,
        iac_file_path=entry.iac_file_path,
        generated_iac=entry.generated_iac,
        awaiting_human=entry.status == "awaiting_human",
    )


# ── GET /stream — SSE ─────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/stream",
    summary="SSE stream of agent step events",
    response_class=StreamingResponse,
)
async def stream_events(session_id: str, request: Request) -> StreamingResponse:
    """
    Server-Sent Events stream.
    Each event is a JSON-encoded SSEEvent pushed by the graph runner.

    Frontend usage:
        const es = new EventSource(`/api/migration/${sessionId}/stream`);
        es.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    try:
        entry = session_store.get_or_raise(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    async def event_generator():
        try:
            while True:
                # Check if the client disconnected
                if await request.is_disconnected():
                    logger.info("[SSE] Client disconnected from session %s", session_id)
                    break

                try:
                    # Wait up to 25 s for next event (SSE keep-alive before 30 s timeout)
                    event = await asyncio.wait_for(entry.event_queue.get(), timeout=25.0)
                    payload = json.dumps(event)
                    yield f"data: {payload}\n\n"

                    # Terminal events — close the stream
                    if event.get("event") in ("completed", "error"):
                        break

                except asyncio.TimeoutError:
                    # Send a keep-alive comment so the connection stays open
                    yield ": keep-alive\n\n"

        except asyncio.CancelledError:
            pass

    # asyncio needs to be in scope inside the generator
    import asyncio  # noqa: PLC0415 — intentional late import inside generator

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disables Nginx buffering
        },
    )


# ── POST /decision — HITL resume ──────────────────────────────────────────────

@router.post(
    "/{session_id}/decision",
    response_model=HITLDecisionResponse,
    summary="Submit HITL approve / reject decision",
)
async def submit_decision(
    session_id: str,
    body: HITLDecisionRequest,
) -> HITLDecisionResponse:
    """
    Resume the paused graph with the human's decision.
    The graph continues from where interrupt() paused it.
    """
    try:
        entry = session_store.get_or_raise(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    if entry.status != "awaiting_human":
        raise HTTPException(
            status_code=409,
            detail=f"Session is not awaiting human input (current status: {entry.status})",
        )

    if body.decision == "reject" and not body.feedback:
        raise HTTPException(
            status_code=422,
            detail="feedback is required when rejecting — the IaC generator needs it to improve.",
        )

    logger.info("[POST /decision] Session %s — decision: %s", session_id, body.decision)
    await resume_graph(session_id, body.decision, body.feedback)

    return HITLDecisionResponse(
        session_id=session_id,
        decision=body.decision,
        message="Graph resumed. Connect to /stream for further updates.",
    )


# ── GET /iac — download generated Terraform file ─────────────────────────────

@router.get(
    "/{session_id}/iac",
    summary="Download generated IaC (.tf) file",
)
async def download_iac(session_id: str) -> FileResponse:
    """
    Returns the generated .tf file as a file download.
    Only available after the iac_generator node has run.
    """
    try:
        entry = session_store.get_or_raise(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    if not entry.iac_file_path:
        raise HTTPException(
            status_code=404,
            detail="IaC not yet generated for this session.",
        )

    path = Path(entry.iac_file_path)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"IaC file not found on disk: {entry.iac_file_path}",
        )

    return FileResponse(
        path=str(path),
        filename=f"{session_id}.tf",
        media_type="text/plain",
    )