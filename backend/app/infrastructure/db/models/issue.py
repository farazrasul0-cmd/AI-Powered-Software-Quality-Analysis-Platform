"""Issue ORM model."""

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import FindingCategory, FindingSeverity
from app.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.analysis_report import AnalysisReport


class Issue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "issues"

    report_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_reports.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    rule_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[FindingCategory] = mapped_column(
        SQLEnum(FindingCategory),
        default=FindingCategory.CODE_SMELL,
        index=True,
        nullable=False,
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        SQLEnum(FindingSeverity),
        default=FindingSeverity.MEDIUM,
        index=True,
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    line_end: Mapped[int] = mapped_column(Integer, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    cwe_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    report: Mapped["AnalysisReport"] = relationship("AnalysisReport", back_populates="issues")
