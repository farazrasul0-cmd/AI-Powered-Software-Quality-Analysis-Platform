"""Pydantic schemas for Issues, Metrics, and Defect Predictions."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.enums import FindingCategory, FindingSeverity, RiskTier


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_id: str
    category: FindingCategory
    severity: FindingSeverity
    file_path: str
    line_start: int
    line_end: int
    title: str
    description: str
    snippet: str | None = None
    remediation: str | None = None
    cwe_id: str | None = None


class FileMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_path: str
    language: str | None = None
    sloc: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    function_count: int
    class_count: int
    maintainability_index: float
    halstead_metrics: dict[str, Any]


class DefectPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_path: str
    defect_probability: float
    risk_tier: RiskTier
    model_version: str
    shap_factors: dict[str, Any]
