"""Analysis Report ORM model."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.analysis_job import AnalysisJob
    from app.infrastructure.db.models.defect_prediction import DefectPrediction
    from app.infrastructure.db.models.file_metric import FileMetric
    from app.infrastructure.db.models.issue import Issue
    from app.infrastructure.db.models.review_comment import ReviewComment


class AnalysisReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_reports"

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Aggregated Pillar Scores (0 to 100)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    maintainability_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    security_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    testing_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    architecture_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Summary Metrics
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_lines_of_code: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_functions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_classes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    technical_debt_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    summary_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="reports")
    issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    file_metrics: Mapped[list["FileMetric"]] = relationship(
        "FileMetric",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    defect_predictions: Mapped[list["DefectPrediction"]] = relationship(
        "DefectPrediction",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    review_comments: Mapped[list["ReviewComment"]] = relationship(
        "ReviewComment",
        back_populates="report",
        cascade="all, delete-orphan",
    )
