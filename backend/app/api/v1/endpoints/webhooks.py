"""GitHub Webhook Ingestion Endpoint."""

import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domain.enums import JobStatus
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.models.repository import Repository
from app.infrastructure.db.session import get_db_session
from app.infrastructure.github.webhook_handler import github_webhook_handler
from app.repositories.analysis_job_repo import AnalysisJobRepo
from app.repositories.repository_repo import RepositoryRepo

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
    session: AsyncSession = Depends(get_db_session),
):
    """Receives and validates GitHub webhook events using constant-time HMAC comparison."""
    raw_body = await request.body()

    # 1. Verify HMAC SHA-256 signature
    if not github_webhook_handler.verify_signature(raw_body, x_hub_signature_256):
        logger.warning("Rejected webhook due to invalid X-Hub-Signature-256 header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Hub-Signature-256 signature",
        )

    try:
        data = json.loads(raw_body.decode("utf-8"))
        payload = github_webhook_handler.parse_payload(data)
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {e}",
        ) from e

    # 2. Process Pull Request events
    if x_github_event == "pull_request" and payload.pull_request:
        pr = payload.pull_request
        repo_info = payload.repository

        if payload.action not in ("opened", "synchronize", "reopened"):
            return {"status": "ignored", "action": payload.action}

        # Find or create repository
        repo_repo = RepositoryRepo(session)
        existing_repo = await repo_repo.get_by_url(repo_info.clone_url)
        if not existing_repo:
            new_repo = Repository(
                name=repo_info.name,
                url=repo_info.clone_url,
                default_branch=repo_info.default_branch,
            )
            existing_repo = await repo_repo.create(new_repo)
            await session.commit()

        # Create queued analysis job for the PR commit
        job = AnalysisJob(
            repository_id=existing_repo.id,
            branch=pr.head.ref,
            commit_sha=pr.head.sha,
            status=JobStatus.QUEUED,
            current_stage="WEBHOOK_RECEIVED",
            progress_percent=0.0,
        )
        job_repo = AnalysisJobRepo(session)
        job = await job_repo.create(job)
        await session.commit()

        logger.info(
            f"Queued Analysis Job {job.id} for PR #{pr.number} ({pr.head.ref} @ {pr.head.sha[:7]})"
        )
        return {
            "status": "accepted",
            "job_id": job.id,
            "repository_id": existing_repo.id,
            "pr_number": pr.number,
            "commit_sha": pr.head.sha,
        }

    return {"status": "event_acknowledged", "event": x_github_event}
