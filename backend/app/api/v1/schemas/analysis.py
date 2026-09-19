"""Pydantic schemas for Analysis Jobs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import JobStatus


class AnalysisTriggerRequest(BaseModel):
    repository_id: str = Field(..., description="ID of repository to analyze")
    branch: str | None = Field("main", description="Target branch")
    commit_sha: str | None = Field(None, description="Optional target commit hash")


class AnalysisJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    branch: str
    commit_sha: str | None = None
    status: JobStatus
    current_stage: str
    progress_percent: float
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
