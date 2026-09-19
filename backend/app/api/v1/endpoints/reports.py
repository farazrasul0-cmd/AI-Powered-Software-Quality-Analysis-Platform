"""Analysis Reports retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.defect import DefectPredictionResponse, DefectSummaryResponse
from app.api.v1.schemas.issue import FileMetricResponse, IssueResponse
from app.api.v1.schemas.report import AnalysisReportDetailResponse
from app.domain.enums import FindingCategory, FindingSeverity, RiskTier
from app.infrastructure.db.session import get_db_session
from app.repositories.report_repo import ReportRepo

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{report_id}", response_model=AnalysisReportDetailResponse)
async def get_report_detail(
    report_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.get("/job/{job_id}", response_model=AnalysisReportDetailResponse)
async def get_report_by_job(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ReportRepo(session)
    report = await repo.get_by_job_id(job_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report for job not found"
        )
    return report


@router.get("/{report_id}/issues", response_model=list[IssueResponse])
async def get_report_issues(
    report_id: str,
    category: FindingCategory | None = Query(None, description="Filter by finding category"),
    severity: FindingSeverity | None = Query(None, description="Filter by finding severity"),
    file_path: str | None = Query(None, description="Filter by file path substring"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """Filters static analysis issues and code smells by category, severity, and file."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    filtered = report.issues
    if category:
        filtered = [i for i in filtered if i.category == category]
    if severity:
        filtered = [i for i in filtered if i.severity == severity]
    if file_path:
        filtered = [i for i in filtered if file_path.lower() in i.file_path.lower()]

    return filtered[offset : offset + limit]


@router.get("/{report_id}/metrics", response_model=list[FileMetricResponse])
async def get_report_metrics(
    report_id: str,
    sort_by: str = Query("cyclomatic_complexity", description="Field to sort metrics by"),
    order: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
    session: AsyncSession = Depends(get_db_session),
):
    """Returns file metrics sorted by complexity or SLOC."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    metrics = list(report.file_metrics)
    reverse = order.lower() == "desc"

    if sort_by == "cyclomatic_complexity":
        metrics.sort(key=lambda m: m.cyclomatic_complexity, reverse=reverse)
    elif sort_by == "cognitive_complexity":
        metrics.sort(key=lambda m: m.cognitive_complexity, reverse=reverse)
    elif sort_by == "sloc":
        metrics.sort(key=lambda m: m.sloc, reverse=reverse)
    elif sort_by == "maintainability_index":
        metrics.sort(key=lambda m: m.maintainability_index, reverse=reverse)

    return metrics


@router.get("/{report_id}/defects", response_model=list[DefectPredictionResponse])
async def get_report_defects(
    report_id: str,
    risk_tier: RiskTier | None = Query(None, description="Filter by risk tier"),
    min_probability: float | None = Query(None, ge=0.0, le=1.0, description="Minimum defect probability"),
    file_path: str | None = Query(None, description="Filter by file path substring"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieves ranked defect risk predictions and TreeSHAP explainability factors."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    predictions = list(report.defect_predictions)
    if risk_tier:
        predictions = [p for p in predictions if p.risk_tier == risk_tier]
    if min_probability is not None:
        predictions = [p for p in predictions if p.defect_probability >= min_probability]
    if file_path:
        predictions = [p for p in predictions if file_path.lower() in p.file_path.lower()]

    # Sort descending by defect probability
    predictions.sort(key=lambda p: p.defect_probability, reverse=True)
    return predictions[offset : offset + limit]


@router.get("/{report_id}/defects/summary", response_model=DefectSummaryResponse)
async def get_report_defects_summary(
    report_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Returns aggregated summary metrics across all defect predictions in the report."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    predictions = list(report.defect_predictions)
    total = len(predictions)
    if total == 0:
        return DefectSummaryResponse(
            total_files_analyzed=0,
            critical_count=0,
            high_count=0,
            moderate_count=0,
            low_count=0,
            average_defect_probability=0.0,
            highest_risk_file=None,
            highest_risk_probability=0.0,
        )

    critical_count = sum(1 for p in predictions if p.risk_tier == RiskTier.CRITICAL)
    high_count = sum(1 for p in predictions if p.risk_tier == RiskTier.HIGH)
    moderate_count = sum(1 for p in predictions if p.risk_tier == RiskTier.MODERATE)
    low_count = sum(1 for p in predictions if p.risk_tier == RiskTier.LOW)

    avg_prob = sum(p.defect_probability for p in predictions) / total
    sorted_preds = sorted(predictions, key=lambda p: p.defect_probability, reverse=True)
    highest_pred = sorted_preds[0] if sorted_preds else None

    return DefectSummaryResponse(
        total_files_analyzed=total,
        critical_count=critical_count,
        high_count=high_count,
        moderate_count=moderate_count,
        low_count=low_count,
        average_defect_probability=round(avg_prob, 4),
        highest_risk_file=highest_pred.file_path if highest_pred else None,
        highest_risk_probability=round(highest_pred.defect_probability, 4) if highest_pred else 0.0,
    )

