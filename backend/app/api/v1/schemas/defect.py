"""Pydantic schemas for Defect Predictions and Summaries."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.enums import RiskTier


class DefectPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_path: str
    defect_probability: float
    risk_tier: RiskTier
    model_version: str
    shap_factors: dict[str, Any]


class DefectSummaryResponse(BaseModel):
    total_files_analyzed: int
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int
    average_defect_probability: float
    highest_risk_file: str | None = None
    highest_risk_probability: float = 0.0
