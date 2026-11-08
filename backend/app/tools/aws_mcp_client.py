"""
tools/aws_mcp_client.py — Loads AWS MCP tools via langchain-mcp-adapters.

The MultiServerMCPClient is kept as a module-level singleton so the
subprocess is only spawned once per worker. Call get_aws_tools() inside
any async context (FastAPI lifespan, agent node, etc.).

AWS authentication uses SigV4 via standard boto3 credential chain:
  - IAM role / instance profile  (preferred in prod)
  - ~/.aws/credentials            (local dev)
  - AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars

certifi provides the CA bundle for HTTPS to MCP endpoints.
No OAuth / OAuth2 is used here — only SigV4.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import certifi
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MCP server registry
# Add more AWS MCP servers here as the scope grows.
# Each entry maps to one `uvx`-launched server process (stdio transport).
# ---------------------------------------------------------------------------
AWS_MCP_SERVERS: dict[str, dict[str, Any]] = {
    # Core AWS operations — resource tagging API, describe calls, etc.
    "awslabs-core": {
        "transport": "stdio",
        "command": "uvx",
        "args": ["awslabs.core-mcp-server@latest"],
        "env": {
            "FASTMCP_LOG_LEVEL": "ERROR",
            # certifi CA bundle used by the MCP subprocess for outbound HTTPS
            "SSL_CERT_FILE": certifi.where(),
        },
    },
    # AWS documentation MCP — gives the LLM context on service APIs
    "awslabs-docs": {
        "transport": "stdio",
        "command": "uvx",
        "args": ["awslabs.aws-documentation-mcp-server@latest"],
        "env": {
            "FASTMCP_LOG_LEVEL": "ERROR",
            "AWS_DOCUMENTATION_PARTITION": "aws",
            "SSL_CERT_FILE": certifi.where(),
        },
    },
}


@lru_cache(maxsize=1)
def _get_client() -> MultiServerMCPClient:
    """Return (and cache) the MCP client singleton."""
    return MultiServerMCPClient(AWS_MCP_SERVERS)


async def get_aws_tools() -> list[BaseTool]:
    """Return LangChain-compatible tools from all configured MCP servers.

    Call this once at startup and pass the result to bind_tools() / ToolNode.
    """
    client = _get_client()
    tools = await client.get_tools()
    logger.info("Loaded %d AWS MCP tools", len(tools))
    return tools
