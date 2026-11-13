"""
graph/builder.py — Assembles and compiles the LangGraph StateGraph.

Import `migration_graph` from here everywhere you need the graph.
It is a CompiledStateGraph and has: ainvoke, astream, aget_state, etc.
"""
from __future__ import annotations

import logging

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

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

_checkpointer = InMemorySaver()


def _end_with_error(state: MigrationGraphState) -> dict[str, object]:
    return {
        "current_step": "failed",
        "errors": state.get("errors", []),
    }


def build_graph() -> CompiledStateGraph:
    builder = StateGraph(MigrationGraphState)

    # ── Nodes ─────────────────────────────────────────────────────────────
    builder.add_node("intent_parser", run_intent_parser)
    builder.add_node("resource_discovery", run_resource_discovery)
    builder.add_node("dependency_mapper", run_dependency_mapper)
    builder.add_node("iac_generator", run_iac_generator)
    builder.add_node("hitl_gate", run_hitl_gate)
    builder.add_node("deployment_stub", run_deployment_stub)
    builder.add_node("end_with_error", _end_with_error)

    # ── Edges ──────────────────────────────────────────────────────────────
    builder.add_edge(START, "intent_parser")

    builder.add_conditional_edges(
        "intent_parser",
        route_after_intent_parser,
        {"resource_discovery": "resource_discovery", "end_with_error": "end_with_error"},
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
    # hitl_gate returns Command(goto=...) — LangGraph routes from it directly
    builder.add_edge("deployment_stub", END)
    builder.add_edge("end_with_error", END)

    compiled: CompiledStateGraph = builder.compile(checkpointer=_checkpointer)
    logger.info(
        "[builder] Graph compiled — nodes: %s",
        list(compiled.nodes.keys()),
    )
    return compiled


migration_graph: CompiledStateGraph = build_graph()