"""Analysis Job database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import JobStatus
from app.infrastructure.db.models.analysis_job import AnalysisJob


class AnalysisJobRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, job_id: str) -> AnalysisJob | None:
        result = await self.session.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
        return result.scalar_one_or_none()

    async def list_by_repo(self, repo_id: str, limit: int = 20) -> list[AnalysisJob]:
        result = await self.session.execute(
            select(AnalysisJob)
            .where(AnalysisJob.repository_id == repo_id)
            .order_by(AnalysisJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, job: AnalysisJob) -> AnalysisJob:
        self.session.add(job)
        await self.session.flush()
        return job

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        current_stage: str,
        progress_percent: float,
        error_message: str | None = None,
    ) -> AnalysisJob | None:
        job = await self.get_by_id(job_id)
        if job:
            job.status = status
            job.current_stage = current_stage
            job.progress_percent = progress_percent
            if error_message is not None:
                job.error_message = error_message
            await self.session.flush()
        return job
