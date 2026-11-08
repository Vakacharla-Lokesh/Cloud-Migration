"""
agents/intent_parser.py — Agent 1: Intent Parser

Parses the raw user prompt into a structured MigrationRequest.
Uses structured output (with_structured_output) so the LLM returns
a validated Pydantic model directly — no manual JSON parsing.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import MigrationGraphState
from app.llm import get_llm
from app.schemas.migration import MigrationRequest

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AWS cloud migration assistant.
Extract the following from the user's migration request:
  - tag_key: the AWS resource tag key (e.g. "app", "project", "env")
  - tag_value: the value of that tag (e.g. "n8n-csp-host")
  - source_region: the AWS region to migrate FROM (e.g. "ap-south-1")
  - target_region: the AWS region to migrate TO (e.g. "us-east-1")
  - iac_format: "terraform" or "cloudformation" (default "terraform")

If the user does not specify a source region, default to "us-east-1".
If the user does not specify an iac_format, default to "terraform".
Return ONLY the structured fields — no explanation.
"""


def run_intent_parser(state: MigrationGraphState) -> dict:
    """LangGraph node: parse user prompt → MigrationRequest."""
    logger.info("[intent_parser] Parsing user prompt")

    llm = get_llm()
    structured_llm = llm.with_structured_output(MigrationRequest)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state["user_prompt"]),
    ]

    try:
        migration_request: MigrationRequest = structured_llm.invoke(messages)
        logger.info("[intent_parser] Parsed: %s", migration_request.model_dump())
        return {
            "migration_request": migration_request,
            "current_step": "intent_parsed",
            "parse_error": None,
        }
    except Exception as exc:
        logger.error("[intent_parser] Failed: %s", exc)
        return {
            "parse_error": str(exc),
            "current_step": "intent_parse_failed",
            "errors": [str(exc)],
        }
