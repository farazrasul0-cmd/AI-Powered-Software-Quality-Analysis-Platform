"""Server-Sent Events (SSE) streaming endpoint."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db_session
from app.infrastructure.redis.pubsub import EventBroadcaster
from app.repositories.analysis_job_repo import AnalysisJobRepo

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/sse/jobs/{job_id}", response_class=StreamingResponse)
async def stream_job_events(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Streams real-time pipeline events and progress percentage using Server-Sent Events (SSE)."""
    job_repo = AnalysisJobRepo(session)
    job = await job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        # Yield initial current state immediately
        initial_payload = {
            "job_id": job.id,
            "stage": job.current_stage,
            "progress": job.progress_percent,
            "message": f"Initial state: {job.status.value}",
            "data": {},
        }
        yield f"data: {json.dumps(initial_payload)}\n\n"

        # If already completed or failed, terminate stream
        if job.status.value in {"COMPLETED", "FAILED", "CANCELLED"}:
            return

        # Listen to Redis PubSub or poll database fallback
        try:
            async for event_chunk in EventBroadcaster.subscribe_events(job_id):
                yield event_chunk
        except Exception:
            # Fallback polling generator if Redis is not active
            while True:
                await asyncio.sleep(2.0)
                current = await job_repo.get_by_id(job_id)
                if not current:
                    break
                poll_payload = {
                    "job_id": current.id,
                    "stage": current.current_stage,
                    "progress": current.progress_percent,
                    "message": f"Status: {current.status.value}",
                    "data": {},
                }
                yield f"data: {json.dumps(poll_payload)}\n\n"
                if current.status.value in {"COMPLETED", "FAILED", "CANCELLED"}:
                    break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
