"""
graph/state.py — Shared state that flows through every node in the graph.

All fields are Optional so each agent only populates what it owns.
LangGraph checkpointer serialises this between node calls.
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

from app.schemas.migration import AWSResource, MigrationRequest


class MigrationGraphState(TypedDict, total=False):
    # ── LangGraph message bus (required for ToolNode / bind_tools pattern) ──
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Raw user input ──────────────────────────────────────────────────────
    user_prompt: str
    session_id: str

    # ── Intent parser output ────────────────────────────────────────────────
    migration_request: Optional[MigrationRequest]
    parse_error: Optional[str]           # set if intent parsing fails

    # ── Resource discovery output ───────────────────────────────────────────
    discovered_resources: list[AWSResource]
    discovery_error: Optional[str]

    # ── Dependency mapper output ────────────────────────────────────────────
    # Serialisable DAG: {arn: [arn, ...]} adjacency list
    dependency_graph: dict[str, list[str]]
    ordered_resources: list[AWSResource]  # topological sort result

    # ── IaC generator output ────────────────────────────────────────────────
    generated_iac: str                   # full rendered IaC string
    iac_file_path: str                   # e.g. "sessions/<session_id>.tf"

    # ── HITL gate ───────────────────────────────────────────────────────────
    # Populated by the interrupt() call; consumed by the edge after the gate.
    human_decision: Optional[Literal["approve", "reject"]]
    human_feedback: Optional[str]

    # ── Meta ────────────────────────────────────────────────────────────────
    current_step: str
    errors: list[str]
