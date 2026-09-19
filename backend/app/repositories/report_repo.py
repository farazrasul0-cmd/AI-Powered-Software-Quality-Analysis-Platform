"""Analysis Report database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models.analysis_report import AnalysisReport


class ReportRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, report_id: str) -> AnalysisReport | None:
        result = await self.session.execute(
            select(AnalysisReport)
            .where(AnalysisReport.id == report_id)
            .options(
                selectinload(AnalysisReport.issues),
                selectinload(AnalysisReport.file_metrics),
                selectinload(AnalysisReport.defect_predictions),
                selectinload(AnalysisReport.review_comments),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_job_id(self, job_id: str) -> AnalysisReport | None:
        result = await self.session.execute(
            select(AnalysisReport)
            .where(AnalysisReport.job_id == job_id)
            .options(
                selectinload(AnalysisReport.issues),
                selectinload(AnalysisReport.file_metrics),
                selectinload(AnalysisReport.defect_predictions),
                selectinload(AnalysisReport.review_comments),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, report: AnalysisReport) -> AnalysisReport:
        self.session.add(report)
        await self.session.flush()
        return report
