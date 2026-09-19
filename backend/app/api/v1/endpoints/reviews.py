"""Review Comments REST API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.review import ReviewCommentResponse
from app.domain.enums import CommentStatus
from app.infrastructure.db.models.review_comment import ReviewComment
from app.infrastructure.db.session import get_db_session
from app.repositories.report_repo import ReportRepo

router = APIRouter(tags=["Reviews"])


class UpdateCommentStatusRequest(BaseModel):
    status: CommentStatus


@router.get("/reports/{report_id}/reviews", response_model=list[ReviewCommentResponse])
async def get_report_reviews(
    report_id: str,
    status_filter: CommentStatus | None = Query(None, alias="status", description="Filter by comment status"),
    file_path: str | None = Query(None, description="Filter by file path substring"),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieves all AI-generated code review comments for an analysis report."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    comments = list(report.review_comments)
    if status_filter:
        comments = [c for c in comments if c.status == status_filter]
    if file_path:
        comments = [c for c in comments if file_path.lower() in c.file_path.lower()]

    # Sort by file_path, line_number
    comments.sort(key=lambda c: (c.file_path, c.line_number))
    return comments


@router.patch("/reviews/{comment_id}/status", response_model=ReviewCommentResponse)
async def update_review_comment_status(
    comment_id: str,
    body: UpdateCommentStatusRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Updates review comment workflow status (ACCEPTED, DISMISSED, PENDING)."""
    comment = await session.get(ReviewComment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review comment not found")

    comment.status = body.status
    await session.commit()
    await session.refresh(comment)
    return comment
