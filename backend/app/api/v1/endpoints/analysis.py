"""Analysis Job triggering and status endpoints."""

import socket

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.analysis import AnalysisJobResponse, AnalysisTriggerRequest
from app.core.config import settings
from app.core.logging import logger
from app.domain.enums import JobStatus
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.session import async_session_factory, get_db_session
from app.repositories.analysis_job_repo import AnalysisJobRepo
from app.repositories.repository_repo import RepositoryRepo
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def _is_redis_available() -> bool:
    """Fast non-blocking socket check for Redis presence."""
    try:
        with socket.create_connection((settings.REDIS_HOST, settings.REDIS_PORT), timeout=0.2):
            return True
    except OSError:
        return False


async def _run_pipeline_background(job_id: str):
    logger.info(f"Starting background pipeline execution for job {job_id}...")
    try:
        async with async_session_factory() as session:
            service = IngestionService(session)
            await service.run_pipeline(job_id)
            logger.info(f"Completed background pipeline execution for job {job_id} successfully.")
    except Exception as e:
        logger.exception(f"Background pipeline execution failed for job {job_id}: {e}")


@router.post("/trigger", response_model=AnalysisJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_analysis(
    payload: AnalysisTriggerRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    repo_repo = RepositoryRepo(session)
    repo = await repo_repo.get_by_id(payload.repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {payload.repository_id} not found",
        )

    job = AnalysisJob(
        repository_id=payload.repository_id,
        branch=payload.branch or repo.default_branch,
        commit_sha=payload.commit_sha,
        status=JobStatus.QUEUED,
        current_stage="QUEUED",
        progress_percent=0.0,
    )
    job_repo = AnalysisJobRepo(session)
    job = await job_repo.create(job)
    await session.commit()

    # Fast check: If Redis is online, dispatch via Celery. Otherwise, immediately use BackgroundTasks.
    dispatched = False
    if _is_redis_available():
        try:
            from app.workers.celery_app import analyze_repository_task

            analyze_repository_task.apply_async(args=[job.id], queue="cpu_heavy")
            dispatched = True
            logger.info(f"Dispatched job {job.id} to Celery queue")
        except Exception as e:
            logger.warning(f"Celery unavailable ({e}), using async BackgroundTasks fallback")
    else:
        logger.info("Redis broker offline. Instantly falling back to async BackgroundTasks.")

    if not dispatched:
        import asyncio

        asyncio.create_task(_run_pipeline_background(job.id))

    return job


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
async def get_job_status(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    job_repo = AnalysisJobRepo(session)
    job = await job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.get("/repository/{repo_id}/jobs", response_model=list[AnalysisJobResponse])
async def list_repository_jobs(
    repo_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    job_repo = AnalysisJobRepo(session)
    return await job_repo.list_by_repo(repo_id)
