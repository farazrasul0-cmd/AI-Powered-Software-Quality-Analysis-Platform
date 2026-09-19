"""Analysis Job triggering and status endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.analysis import AnalysisJobResponse, AnalysisTriggerRequest
from app.core.logging import logger
from app.domain.enums import JobStatus
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.session import async_session_factory, get_db_session
from app.repositories.analysis_job_repo import AnalysisJobRepo
from app.repositories.repository_repo import RepositoryRepo
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/analysis", tags=["Analysis"])


async def _run_pipeline_background(job_id: str):
    async with async_session_factory() as session:
        service = IngestionService(session)
        try:
            await service.run_pipeline(job_id)
        except Exception as e:
            logger.error(f"Background pipeline execution failed for job {job_id}: {e}")


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

    # Try Celery dispatch, fallback gracefully to FastAPI background tasks
    dispatched = False
    try:
        from app.workers.celery_app import analyze_repository_task

        analyze_repository_task.apply_async(args=[job.id], queue="cpu_heavy")
        dispatched = True
        logger.info(f"Dispatched job {job.id} to Celery queue")
    except Exception as e:
        logger.warning(f"Celery unavailable ({e}), using async BackgroundTasks fallback")

    if not dispatched:
        background_tasks.add_task(_run_pipeline_background, job.id)

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
