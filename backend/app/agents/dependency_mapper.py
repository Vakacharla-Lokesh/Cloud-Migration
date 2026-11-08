"""
agents/dependency_mapper.py — Agent 3: Dependency Mapper

Builds a dependency DAG from discovered resources so that IaC blocks
are generated in the correct provisioning order.

Example dependency chain from your notes:
  S3 Bucket → CloudFront Distribution → (IAM OAC role)

The LLM reasons over the resource list and known AWS dependency rules
to produce an adjacency list (DAG) + a topologically-sorted order.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict, deque

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import MigrationGraphState
from app.llm import get_llm
from app.schemas.migration import AWSResource

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AWS infrastructure dependency analyser.
Given a list of AWS resources, produce a dependency graph showing which
resources must be created BEFORE others.

Rules:
- S3 buckets must be created before CloudFront distributions that reference them.
- IAM roles / policies must be created before the resources that assume them.
- VPCs before subnets, subnets before EC2/RDS instances, etc.
- Security groups before EC2 instances.

Return a JSON object with TWO keys:
  "graph":   { "arn1": ["arn2", "arn3"], ... }   (arn2, arn3 depend on arn1)
  "ordered": ["arn1", "arn2", ...]                (topological order, create first → last)

Return ONLY valid JSON.
"""


def _topological_sort(graph: dict[str, list[str]], arns: list[str]) -> list[str]:
    """Kahn's algorithm fallback if the LLM order is incomplete."""
    in_degree: dict[str, int] = defaultdict(int)
    all_nodes = set(arns)
    for node in all_nodes:
        in_degree.setdefault(node, 0)
    for node, deps in graph.items():
        for dep in deps:
            in_degree[dep] += 1

    queue = deque([n for n in all_nodes if in_degree[n] == 0])
    result: list[str] = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for dep in graph.get(node, []):
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)

    # Append any nodes not reached (cycles / islands)
    missing = [n for n in all_nodes if n not in result]
    return result + missing


def run_dependency_mapper(state: MigrationGraphState) -> dict:
    """LangGraph node: map resource dependencies."""
    logger.info("[dependency_mapper] Building dependency graph")

    resources: list[AWSResource] = state.get("discovered_resources", [])
    if not resources:
        logger.warning("[dependency_mapper] No resources to map")
        return {
            "dependency_graph": {},
            "ordered_resources": [],
            "current_step": "dependency_mapped",
        }

    llm = get_llm()
    resource_summary = json.dumps(
        [{"arn": r.arn, "resource_type": r.resource_type, "resource_id": r.resource_id} for r in resources],
        indent=2,
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Resources:\n{resource_summary}"),
    ]

    try:
        response = llm.invoke(messages)
        payload = json.loads(response.content)
        graph: dict[str, list[str]] = payload.get("graph", {})
        llm_order: list[str] = payload.get("ordered", [])
    except Exception as exc:
        logger.warning("[dependency_mapper] LLM DAG parse failed (%s); falling back to flat order", exc)
        graph = {}
        llm_order = [r.arn for r in resources]

    # Validate / complete the order with Kahn's algorithm
    all_arns = [r.arn for r in resources]
    if set(llm_order) != set(all_arns):
        llm_order = _topological_sort(graph, all_arns)

    arn_to_resource = {r.arn: r for r in resources}
    ordered_resources = [arn_to_resource[arn] for arn in llm_order if arn in arn_to_resource]

    logger.info("[dependency_mapper] Ordered %d resources", len(ordered_resources))
    return {
        "dependency_graph": graph,
        "ordered_resources": ordered_resources,
        "current_step": "dependency_mapped",
    }
