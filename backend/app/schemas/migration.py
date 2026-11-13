"""
schemas/migration.py — Core data models for the migration pipeline.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class MigrationRequest(BaseModel):
    """Parsed migration intent from the user prompt."""

    tag_key: str = Field(..., description="AWS tag key to filter resources by")
    tag_value: str = Field(..., description="Value of the tag")
    source_region: str = Field(..., description="AWS region to migrate FROM")
    target_region: str = Field(..., description="AWS region to migrate TO")
    iac_format: Literal["terraform", "cloudformation"] = Field(
        default="terraform",
        description="IaC output format",
    )


class AWSResource(BaseModel):
    """A discovered AWS resource."""

    arn: str = Field(..., description="Full ARN of the resource")
    resource_type: str = Field(..., description="e.g. 'AWS::S3::Bucket'")
    resource_id: str = Field(..., description="Short resource id / name")
    region: str
    tags: dict[str, str] = Field(default_factory=dict)
    config_snapshot: dict = Field(
        default_factory=dict,
        description="Raw config returned by discovery (security groups, policies, etc.)",
    )
