"""Defect Prediction ORM model."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import RiskTier
from app.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.analysis_report import AnalysisReport


class DefectPrediction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "defect_predictions"

    report_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_reports.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    defect_probability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_tier: Mapped[RiskTier] = mapped_column(
        SQLEnum(RiskTier),
        default=RiskTier.LOW,
        index=True,
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(String(50), default="xgboost-v1.0", nullable=False)
    shap_factors: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    report: Mapped["AnalysisReport"] = relationship(
        "AnalysisReport", back_populates="defect_predictions"
    )
