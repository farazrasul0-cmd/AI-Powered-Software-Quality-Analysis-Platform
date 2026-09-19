"""Repository ORM model."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.infrastructure.db.models.analysis_job import AnalysisJob


class Repository(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "repositories"

    url: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    primary_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    languages: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    disk_size_bytes: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    jobs: Mapped[list["AnalysisJob"]] = relationship(
        "AnalysisJob",
        back_populates="repository",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisJob.created_at)",
    )
