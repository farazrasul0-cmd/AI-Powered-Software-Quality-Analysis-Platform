"""Pydantic schemas for Multi-Dimensional Quality Scorecard and Historical Trends."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RadarAxisPoint(BaseModel):
    """Data point for Recharts Radar Chart visualization."""
    axis: str = Field(..., description="Name of the quality dimension")
    value: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100")
    benchmark_value: float = Field(default=75.0, description="Industry/Academic benchmark baseline")


class PillarScore(BaseModel):
    """Detailed breakdown of an individual quality pillar."""
    name: str
    score: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_contribution: float
    grade: Literal["A", "B", "C", "D", "F"]
    benchmark_percentile: float = Field(..., ge=0.0, le=100.0)
    summary: str


class RecommendationItem(BaseModel):
    """Prioritized remediation recommendation for improving codebase quality."""
    rank: int
    pillar: str
    title: str
    description: str
    effort_minutes: int
    potential_score_impact: float


class RadarScorecardResponse(BaseModel):
    """Composite Multi-Dimensional Quality Scorecard response."""
    report_id: str
    overall_score: float = Field(..., ge=0.0, le=100.0)
    grade: Literal["A", "B", "C", "D", "F"]
    radar_data: list[RadarAxisPoint]
    pillars: list[PillarScore]
    technical_debt_minutes: int
    recommendations: list[RecommendationItem]
    false_positives_suppressed: int
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScorecardTrendPoint(BaseModel):
    """Historical quality milestone for a repository commit/run."""
    report_id: str
    commit_hash: str | None = None
    analyzed_at: datetime
    overall_score: float
    maintainability_score: float
    security_score: float
    architecture_score: float
    testing_score: float


class ScorecardTrendResponse(BaseModel):
    """Historical quality trend sequence for a repository."""
    repository_id: str
    repository_name: str
    points: list[ScorecardTrendPoint]
    trend_direction: Literal["IMPROVING", "STABLE", "DEGRADING"]
    delta_since_previous: float

    model_config = ConfigDict(from_attributes=True)
