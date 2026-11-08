"""
agents/resource_discovery.py — Agent 2: Resource Discovery

Calls AWS Resource Groups Tagging API (via MCP tools) to list all
resources matching the tag in the source region.

Pattern:
  LLM + bind_tools(aws_tools) → tool calls → ToolNode handles execution
  → LLM summarises → we parse the structured resource list back out.

The node is async because get_aws_tools() must be awaited.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode

from app.graph.state import MigrationGraphState
from app.llm import get_llm
from app.schemas.migration import AWSResource
from app.tools.aws_mcp_client import get_aws_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AWS resource discovery agent.
Your task: use the available AWS tools to list ALL resources
tagged with the given key/value pair in the given region.

Steps:
1. Call the resource tagging API tool to get resources by tag.
2. For each resource, fetch its configuration (security groups, policies, etc.) if tools are available.
3. Return a JSON array of objects with these fields:
   arn, resource_type, resource_id, region, tags, config_snapshot

Return ONLY valid JSON — no markdown fences, no explanation.
"""


async def run_resource_discovery(state: MigrationGraphState) -> dict:
    """LangGraph node: discover tagged AWS resources."""
    logger.info("[resource_discovery] Starting discovery")

    req = state.get("migration_request")
    if req is None:
        return {
            "discovery_error": "No migration_request in state — intent parser must run first.",
            "current_step": "discovery_failed",
            "errors": ["missing migration_request"],
        }

    aws_tools: list[BaseTool] = await get_aws_tools()
    llm = get_llm()
    llm_with_tools = llm.bind_tools(aws_tools)

    prompt = (
        f"Discover all AWS resources in region '{req.source_region}' "
        f"tagged with '{req.tag_key}={req.tag_value}'. "
        f"Return a JSON array of resource objects."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    # Agentic tool-call loop (max 5 iterations to avoid runaway)
    tool_node = ToolNode(aws_tools)
    for _ in range(5):
        response: AIMessage = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            # LLM is done calling tools — final answer is in response.content
            break

        # Execute tool calls and append results
        tool_results = await tool_node.ainvoke({"messages": messages})
        messages.extend(tool_results["messages"])

    # Extract the final JSON from the last AI message
    final_text = messages[-1].content if messages else ""
    try:
        raw_list: list[dict] = json.loads(final_text)
        resources = [AWSResource(**r) for r in raw_list]
        logger.info("[resource_discovery] Found %d resources", len(resources))
        return {
            "discovered_resources": resources,
            "current_step": "discovery_complete",
            "discovery_error": None,
        }
    except Exception as exc:
        logger.warning("[resource_discovery] JSON parse failed (%s); raw: %s", exc, final_text[:200])
        # Return empty list but don't hard-fail — dependency mapper handles it
        return {
            "discovered_resources": [],
            "discovery_error": str(exc),
            "current_step": "discovery_complete_with_errors",
            "errors": [str(exc)],
        }
