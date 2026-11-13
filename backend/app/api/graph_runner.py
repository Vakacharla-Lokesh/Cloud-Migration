"""
api/graph_runner.py — Background async task that drives the LangGraph.

Responsibilities:
  1. Run migration_graph.astream() so we get node-by-node updates
  2. Push SSE events into the session's asyncio.Queue
  3. Detect GraphInterrupt (HITL gate fired) and park the session
  4. Resume the graph when the human sends a decision

The FastAPI endpoints call start_graph() and resume_graph() —
they don't touch the graph directly.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langgraph.errors import GraphInterrupt
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig

from app.api.session_store import session_store
from app.graph.builder import migration_graph

logger = logging.getLogger(__name__)


def _graph_config(session_id: str) -> RunnableConfig:
    """LangGraph run config — thread_id keys the checkpointer."""
    return {"configurable": {"thread_id": session_id}}


async def _run_graph(session_id: str, input_payload: dict | Command) -> None:
    """
    Core execution loop — streams graph events and handles HITL interrupts.
    Runs as a background asyncio task (fire-and-forget from the endpoint).
    """
    config = _graph_config(session_id)

    async def push(event_type: str, data: dict) -> None:
        await session_store.push_event(
            session_id,
            {"event": event_type, "session_id": session_id, "data": data},
        )

    try:
        async for chunk in migration_graph.astream(
            input_payload,
            config=config,
            stream_mode="updates",   # yields {node_name: state_delta} per node
        ):
            for node_name, state_delta in chunk.items():
                current_step = state_delta.get("current_step", node_name)
                errors = state_delta.get("errors", [])

                # Keep the session store in sync
                session_store.update(
                    session_id,
                    current_step=current_step,
                    errors=errors,
                )

                # Send a generic step update to the UI
                await push(
                    "step_update",
                    {
                        "node": node_name,
                        "step": current_step,
                        "errors": errors,
                    },
                )

                # IaC was just generated — send it in full
                if "generated_iac" in state_delta:
                    iac = state_delta["generated_iac"]
                    iac_path = state_delta.get("iac_file_path", "")
                    session_store.update(
                        session_id,
                        generated_iac=iac,
                        iac_file_path=iac_path,
                    )
                    await push(
                        "iac_ready",
                        {"generated_iac": iac, "iac_file_path": iac_path},
                    )

        # Graph ran to completion without an interrupt
        session_store.update(session_id, status="completed", current_step="done")
        await push("completed", {"message": "Migration pipeline finished."})

    except GraphInterrupt as exc:
        # HITL gate fired — park the session and tell the UI
        interrupt_payload: Any = exc.args[0] if exc.args else {}
        logger.info("[graph_runner] Session %s paused at HITL gate", session_id)
        session_store.update(session_id, status="awaiting_human", current_step="hitl_gate")
        await push(
            "hitl_required",
            {
                "message": "Human review required. POST /api/migration/{session_id}/decision to continue.",
                "interrupt_payload": interrupt_payload,
            },
        )

    except Exception as exc:
        logger.exception("[graph_runner] Session %s failed: %s", session_id, exc)
        session_store.update(session_id, status="failed", errors=[str(exc)])
        await push("error", {"detail": str(exc)})


async def start_graph(session_id: str, user_prompt: str) -> None:
    """
    Kick off a new migration graph run as a background task.
    Called by POST /api/migration/start.
    """
    input_payload = {
        "user_prompt": user_prompt,
        "session_id": session_id,
        "errors": [],
        "discovered_resources": [],
        "ordered_resources": [],
    }
    # Fire and forget — the endpoint returns immediately
    asyncio.create_task(_run_graph(session_id, input_payload))


async def resume_graph(session_id: str, decision: str, feedback: str) -> None:
    """
    Resume a parked graph after the human makes a HITL decision.
    Called by POST /api/migration/{session_id}/decision.
    """
    resume_payload = Command(resume={"decision": decision, "feedback": feedback})
    session_store.update(session_id, status="running", current_step="hitl_resumed")

    await session_store.push_event(
        session_id,
        {
            "event": "hitl_resumed",
            "session_id": session_id,
            "data": {"decision": decision, "feedback": feedback},
        },
    )
    asyncio.create_task(_run_graph(session_id, resume_payload))