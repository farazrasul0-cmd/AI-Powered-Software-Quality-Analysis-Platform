"""Review Comment ORM model."""

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import CommentStatus
from app.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.analysis_report import AnalysisReport


class ReviewComment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "review_comments"

    report_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_reports.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_patch: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CommentStatus] = mapped_column(
        SQLEnum(CommentStatus),
        default=CommentStatus.PENDING,
        index=True,
        nullable=False,
    )

    # Relationships
    report: Mapped["AnalysisReport"] = relationship(
        "AnalysisReport", back_populates="review_comments"
    )
