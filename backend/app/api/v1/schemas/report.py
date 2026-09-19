"""Pydantic schemas for Analysis Reports."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.api.v1.schemas.issue import (
    DefectPredictionResponse,
    FileMetricResponse,
    IssueResponse,
)
from app.api.v1.schemas.review import ReviewCommentResponse


class AnalysisReportSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    overall_score: float
    maintainability_score: float
    security_score: float
    testing_score: float
    architecture_score: float
    total_files: int
    total_lines_of_code: int
    total_functions: int
    total_classes: int
    technical_debt_minutes: int
    summary_metadata: dict[str, Any]
    created_at: datetime


class AnalysisReportDetailResponse(AnalysisReportSummaryResponse):
    issues: list[IssueResponse] = []
    file_metrics: list[FileMetricResponse] = []
    defect_predictions: list[DefectPredictionResponse] = []
    review_comments: list[ReviewCommentResponse] = []
