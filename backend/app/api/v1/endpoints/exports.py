"""Report Export Endpoints: SARIF v2.1.0, Markdown PR Summary, and Printable HTML."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.export import SarifLog
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.models.repository import Repository
from app.infrastructure.db.session import get_db_session
from app.repositories.report_repo import ReportRepo
from app.services.export_service import ExportService
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/reports", tags=["Reports Export"])


@router.get("/{report_id}/export/sarif", response_model=SarifLog)
async def export_report_sarif(
    report_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Exports analysis report in OASIS standard SARIF v2.1.0 for GitHub Code Scanning."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    scorecard = ScoringService.calculate_scores(
        file_metrics=report.file_metrics,
        issues=report.issues,
        reviews=report.review_comments,
        defect_predictions=report.defect_predictions,
    )

    return ExportService.generate_sarif(report, scorecard)


@router.get("/{report_id}/export/markdown", response_class=PlainTextResponse)
async def export_report_markdown(
    report_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Exports analysis report as GitHub-Flavored Markdown summary for PR comments."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    scorecard = ScoringService.calculate_scores(
        file_metrics=report.file_metrics,
        issues=report.issues,
        reviews=report.review_comments,
        defect_predictions=report.defect_predictions,
    )

    repo_name = "Repository"
    if report.job_id:
        job = await session.get(AnalysisJob, report.job_id)
        if job and job.repository_id:
            repo_obj = await session.get(Repository, job.repository_id)
            if repo_obj:
                repo_name = repo_obj.name

    content = ExportService.generate_markdown_summary(report, scorecard, repo_name=repo_name)
    return PlainTextResponse(content=content, media_type="text/markdown")


@router.get("/{report_id}/export/html", response_class=HTMLResponse)
async def export_report_html(
    report_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Exports standalone, self-contained printable HTML executive report (Print to PDF)."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    scorecard = ScoringService.calculate_scores(
        file_metrics=report.file_metrics,
        issues=report.issues,
        reviews=report.review_comments,
        defect_predictions=report.defect_predictions,
    )

    repo_name = "Repository"
    if report.job_id:
        job = await session.get(AnalysisJob, report.job_id)
        if job and job.repository_id:
            repo_obj = await session.get(Repository, job.repository_id)
            if repo_obj:
                repo_name = repo_obj.name

    html_content = ExportService.generate_printable_html(report, scorecard, repo_name=repo_name)
    return HTMLResponse(content=html_content)
