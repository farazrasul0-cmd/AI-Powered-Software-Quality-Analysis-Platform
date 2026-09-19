"""Pydantic schemas for Repositories."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RepositoryCreate(BaseModel):
    url: str = Field(..., description="Git clone URL (HTTPS or SSH)")
    name: str | None = Field(None, description="Optional custom name for repository")
    default_branch: str = Field("main", description="Default branch to analyze")


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    name: str
    description: str | None = None
    default_branch: str
    primary_language: str | None = None
    languages: dict[str, Any] = Field(default_factory=dict)
    disk_size_bytes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
