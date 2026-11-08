"""
graph/builder.py — Assembles and compiles the LangGraph StateGraph.

Usage:
    from app.graph.builder import build_graph

    graph = build_graph()
    result = await graph.ainvoke(
        {"user_prompt": "...", "session_id": "abc123"},
        config={"configurable": {"thread_id": "abc123"}},
    )

The compiled graph uses InMemorySaver for checkpointing so that
the HITL interrupt() can pause and resume across HTTP calls.

To add a new agent:
  1. Write your node function in app/agents/<name>.py
  2. Import it here
  3. builder.add_node("<name>", your_node_fn)
  4. Wire edges
"""

from __future__ import annotations

import logging

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.dependency_mapper import run_dependency_mapper
from app.agents.deployment_stub import run_deployment_stub
from app.agents.hitl_gate import run_hitl_gate
from app.agents.iac_generator import run_iac_generator
from app.agents.intent_parser import run_intent_parser
from app.agents.resource_discovery import run_resource_discovery
from app.graph.edges import (
    route_after_discovery,
    route_after_iac,
    route_after_intent_parser,
    route_after_mapper,
)
from app.graph.state import MigrationGraphState

logger = logging.getLogger(__name__)

# Module-level checkpointer — shared across all graph invocations in this process.
# Replace with AsyncSqliteSaver or RedisSaver for production multi-worker setups.
_checkpointer = InMemorySaver()


def build_graph() -> StateGraph:
    """Build, compile and return the migration agent graph.

    Nodes added in this sprint (Phase 1):
      intent_parser → resource_discovery → dependency_mapper
      → iac_generator → hitl_gate → deployment_stub

    Phase 2 nodes (deployment, validation, cleanup) slot in after
    deployment_stub without touching this scaffold.
    """
    builder = StateGraph(MigrationGraphState)

    # ── Nodes ──────────────────────────────────────────────────────────────
    builder.add_node("intent_parser", run_intent_parser)
    builder.add_node("resource_discovery", run_resource_discovery)
    builder.add_node("dependency_mapper", run_dependency_mapper)
    builder.add_node("iac_generator", run_iac_generator)
    builder.add_node("hitl_gate", run_hitl_gate)
    builder.add_node("deployment_stub", run_deployment_stub)

    # Terminal error node — just ends the graph cleanly on unrecoverable errors
    builder.add_node("end_with_error", lambda state: {"current_step": "failed"})

    # ── Edges ───────────────────────────────────────────────────────────────
    builder.add_edge(START, "intent_parser")

    builder.add_conditional_edges(
        "intent_parser",
        route_after_intent_parser,
        {
            "resource_discovery": "resource_discovery",
            "end_with_error": "end_with_error",
        },
    )

    builder.add_conditional_edges(
        "resource_discovery",
        route_after_discovery,
        {"dependency_mapper": "dependency_mapper"},
    )

    builder.add_conditional_edges(
        "dependency_mapper",
        route_after_mapper,
        {"iac_generator": "iac_generator"},
    )

    builder.add_conditional_edges(
        "iac_generator",
        route_after_iac,
        {"hitl_gate": "hitl_gate"},
    )

    # hitl_gate uses Command(goto=...) internally — no add_conditional_edges needed.
    # LangGraph follows the Command's goto directly.

    builder.add_edge("deployment_stub", END)
    builder.add_edge("end_with_error", END)

    # ── Compile ─────────────────────────────────────────────────────────────
    graph = builder.compile(checkpointer=_checkpointer)
    logger.info("[graph/builder] Graph compiled successfully")
    return graph


# Singleton — import this wherever you need the graph
migration_graph = build_graph()
