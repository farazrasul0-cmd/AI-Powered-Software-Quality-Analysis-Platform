"""File Metric ORM model."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.analysis_report import AnalysisReport


class FileMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "file_metrics"

    report_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_reports.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)

    sloc: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cyclomatic_complexity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cognitive_complexity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    function_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    class_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maintainability_index: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)

    halstead_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    report: Mapped["AnalysisReport"] = relationship("AnalysisReport", back_populates="file_metrics")
