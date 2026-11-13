"""
graph/edges.py — Conditional edge routing functions.

Each function takes the current state and returns the name of the
next node to route to. Used with add_conditional_edges().
"""

from __future__ import annotations

from app.graph.state import MigrationGraphState


def route_after_intent_parser(state: MigrationGraphState) -> str:
    """After intent parsing: go to discovery, or END on parse failure."""
    if state.get("parse_error"):
        return "end_with_error"
    return "resource_discovery"


def route_after_discovery(_state: MigrationGraphState) -> str:
    """After discovery: always proceed to mapper (even if empty — mapper handles it)."""
    return "dependency_mapper"


def route_after_mapper(_state: MigrationGraphState) -> str:
    """After dependency mapping: always proceed to IaC generation."""
    return "iac_generator"


def route_after_iac(_state: MigrationGraphState) -> str:
    """After IaC generation: proceed to HITL gate."""
    return "hitl_gate"
