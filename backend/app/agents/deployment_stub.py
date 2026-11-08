"""
agents/deployment_stub.py — Phase 2 placeholder.

Swap this out in Phase 2 with the real deployment agent
(terraform apply / aws cloudformation deploy subprocess).
"""

from __future__ import annotations

import logging
from app.graph.state import MigrationGraphState

logger = logging.getLogger(__name__)


def run_deployment_stub(state: MigrationGraphState) -> dict:
    """Stub node — logs approval and exits cleanly."""
    logger.info("[deployment_stub] IaC approved. Deployment is deferred to Phase 2.")
    return {
        "current_step": "deployment_pending",
    }
