"""
agents/iac_generator.py — Agent 4: IaC Generator

For each resource in dependency order:
  1. Try to render a Jinja2 template (s3.tf.j2, cloudfront.tf.j2, …)
  2. For unknown resource types: ask the LLM to generate a Terraform block
  3. Concatenate all blocks → write to sessions/<session_id>.tf

NOT lift & shift: security configs are re-evaluated for the target region.
The provider header is always prepended.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import MigrationGraphState
from app.llm import get_llm
from app.schemas.migration import AWSResource

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template setup
# ---------------------------------------------------------------------------
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
SESSIONS_DIR = Path(__file__).parent.parent.parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# Map AWS resource type → template filename (terraform)
TERRAFORM_TEMPLATE_MAP: dict[str, str] = {
    "AWS::S3::Bucket": "s3.tf.j2",
    "AWS::CloudFront::Distribution": "cloudfront.tf.j2",
}

LLM_FALLBACK_PROMPT = """Generate a valid Terraform resource block for the following AWS resource.
Target region: {target_region}
Resource type: {resource_type}
Resource ID: {resource_id}
Config snapshot: {config_snapshot}

Rules:
- Use the hashicorp/aws provider (~> 5.0)
- Do NOT copy source-region-specific ARNs verbatim
- Re-evaluate security groups and IAM policies for the target region
- Add tags: MigratedFrom = "{source_region}", MigrationTool = "aws-migration-agent"
- Return ONLY the Terraform HCL block, no markdown fences, no explanation.
"""


def _render_terraform_block(
    resource: AWSResource,
    source_region: str,
    target_region: str,
    ordered_resources: list[AWSResource],
    llm,
) -> str:
    """Render one Terraform block for a resource."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR / "terraform")),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template_name = TERRAFORM_TEMPLATE_MAP.get(resource.resource_type)

    if template_name:
        try:
            template = env.get_template(template_name)
            # Build config dict from the resource's config_snapshot + defaults
            config = {
                "versioning_enabled": resource.config_snapshot.get("versioning_enabled", False),
                "block_public_acls": resource.config_snapshot.get("block_public_acls", True),
                "force_destroy": resource.config_snapshot.get("force_destroy", False),
                "ipv6_enabled": resource.config_snapshot.get("ipv6_enabled", True),
                "default_root_object": resource.config_snapshot.get("default_root_object", "index.html"),
                # For CloudFront: find the first S3 bucket in ordered list
                "origin_bucket_id": next(
                    (r.resource_id for r in ordered_resources if r.resource_type == "AWS::S3::Bucket"),
                    "PLACEHOLDER_BUCKET",
                ),
            }
            return template.render(
                resource=resource,
                config=config,
                source_region=source_region,
                target_region=target_region,
            )
        except TemplateNotFound:
            logger.warning("Template %s not found, falling back to LLM", template_name)

    # LLM fallback for unknown resource types
    logger.info("[iac_generator] LLM fallback for %s", resource.resource_type)
    messages = [
        SystemMessage(content="You are an expert Terraform engineer. Output only HCL, no fences."),
        HumanMessage(
            content=LLM_FALLBACK_PROMPT.format(
                target_region=target_region,
                resource_type=resource.resource_type,
                resource_id=resource.resource_id,
                config_snapshot=json.dumps(resource.config_snapshot, indent=2),
                source_region=source_region,
            )
        ),
    ]
    response = llm.invoke(messages)
    return response.content.strip()


def run_iac_generator(state: MigrationGraphState) -> dict:
    """LangGraph node: generate IaC and write to session file."""
    logger.info("[iac_generator] Generating IaC")

    ordered_resources: list[AWSResource] = state.get("ordered_resources", [])
    req = state.get("migration_request")
    session_id: str = state.get("session_id", "default")

    if not req:
        return {
            "current_step": "iac_failed",
            "errors": ["No migration_request available"],
        }

    llm = get_llm()
    blocks: list[str] = []

    # ── Provider header ──────────────────────────────────────────────────────
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR / "terraform")),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    provider_block = env.get_template("provider.tf.j2").render(
        source_region=req.source_region,
        target_region=req.target_region,
    )
    blocks.append(provider_block)
    blocks.append("\n# ═══════════════════════════════════════════════════════")
    blocks.append(f"# Resources migrated from: {req.source_region} → {req.target_region}")
    blocks.append(f"# Tag filter: {req.tag_key}={req.tag_value}")
    blocks.append("# ═══════════════════════════════════════════════════════\n")

    # ── Per-resource blocks ──────────────────────────────────────────────────
    for resource in ordered_resources:
        logger.info("[iac_generator] Rendering block for %s (%s)", resource.resource_id, resource.resource_type)
        block = _render_terraform_block(
            resource=resource,
            source_region=req.source_region,
            target_region=req.target_region,
            ordered_resources=ordered_resources,
            llm=llm,
        )
        blocks.append(block)
        blocks.append("")  # blank line between blocks

    full_iac = "\n".join(blocks)

    # ── Write to sessions/<session_id>.tf ────────────────────────────────────
    tf_path = SESSIONS_DIR / f"{session_id}.tf"
    tf_path.write_text(full_iac, encoding="utf-8")
    logger.info("[iac_generator] Written to %s", tf_path)

    return {
        "generated_iac": full_iac,
        "iac_file_path": str(tf_path),
        "current_step": "iac_generated",
    }
