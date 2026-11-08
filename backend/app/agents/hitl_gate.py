"""
agents/hitl_gate.py — Human-in-the-Loop Gate (Agent 5)

Uses LangGraph's interrupt() to pause graph execution and surface
the generated IaC to the user for approval.

The graph is checkpointed (InMemorySaver) so state is preserved across
the pause. The FastAPI layer resumes with Command(resume=...) once
the user clicks Approve / Reject in the UI.

Decision values:
  - "approve" → graph continues to deployment (Phase 2)
  - "reject"  → graph loops back to IaC generator with feedback
"""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.types import interrupt, Command

from app.graph.state import MigrationGraphState

logger = logging.getLogger(__name__)


def run_hitl_gate(state: MigrationGraphState) -> Command:
    """LangGraph node: pause and ask the human to approve the generated IaC.

    interrupt() serialises the graph state to the checkpointer and raises
    GraphInterrupt. The node resumes when Command(resume=payload) is sent
    via graph.invoke() with the same thread_id.
    """
    logger.info("[hitl_gate] Pausing for human review")

    human_response: dict = interrupt(
        {
            "event": "iac_review_required",
            "message": "Please review the generated IaC before deployment.",
            "iac_file_path": state.get("iac_file_path", ""),
            "generated_iac": state.get("generated_iac", ""),
            "resource_count": len(state.get("ordered_resources", [])),
        }
    )

    decision: Literal["approve", "reject"] = human_response.get("decision", "reject")
    feedback: str = human_response.get("feedback", "")

    logger.info("[hitl_gate] Human decision: %s", decision)

    return Command(
        update={
            "human_decision": decision,
            "human_feedback": feedback if feedback else None,
            "current_step": f"hitl_{decision}d",
        },
        goto="deployment_stub" if decision == "approve" else "iac_generator",
    )
