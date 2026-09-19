"""Radar Scorecard and Historical Trends Endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas.scorecard import (
    PillarScore,
    RadarAxisPoint,
    RadarScorecardResponse,
    RecommendationItem,
    ScorecardTrendPoint,
    ScorecardTrendResponse,
)
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.models.repository import Repository
from app.infrastructure.db.session import get_db_session
from app.repositories.report_repo import ReportRepo
from app.services.scoring_service import ScoringService

router = APIRouter(tags=["Scorecard"])


@router.get("/reports/{report_id}/scorecard", response_model=RadarScorecardResponse)
async def get_report_scorecard(
    report_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Calculates multi-dimensional radar quality scorecard with false-positive suppression."""
    repo = ReportRepo(session)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis report {report_id} not found",
        )

    # Extract metadata components
    circular_deps = None
    if report.summary_metadata and isinstance(report.summary_metadata, dict):
        circular_deps = report.summary_metadata.get("circular_dependencies")

    # Run multi-dimensional scoring engine
    scorecard = ScoringService.calculate_scores(
        file_metrics=report.file_metrics,
        issues=report.issues,
        reviews=report.review_comments,
        circular_dependencies=circular_deps,
        defect_predictions=report.defect_predictions,
    )

    radar_points = [
        RadarAxisPoint(
            axis=item["axis"],
            value=item["value"],
            benchmark_value=item.get("benchmark_value", 75.0),
        )
        for item in scorecard.radar_data
    ]

    pillar_scores = [
        PillarScore(
            name=p["name"],
            score=p["score"],
            weight=p["weight"],
            weighted_contribution=p["weighted_contribution"],
            grade=p["grade"],
            benchmark_percentile=p["benchmark_percentile"],
            summary=p["summary"],
        )
        for p in scorecard.pillars
    ]

    recommendations = [
        RecommendationItem(
            rank=r["rank"],
            pillar=r["pillar"],
            title=r["title"],
            description=r["description"],
            effort_minutes=r["effort_minutes"],
            potential_score_impact=r["potential_score_impact"],
        )
        for r in scorecard.recommendations
    ]

    return RadarScorecardResponse(
        report_id=report.id,
        overall_score=scorecard.overall_score,
        grade=scorecard.grade,  # type: ignore[arg-type]
        radar_data=radar_points,
        pillars=pillar_scores,
        technical_debt_minutes=scorecard.technical_debt_minutes,
        recommendations=recommendations,
        false_positives_suppressed=scorecard.false_positives_suppressed,
        calculated_at=report.updated_at or datetime.utcnow(),
    )


@router.get("/repositories/{repository_id}/trends", response_model=ScorecardTrendResponse)
async def get_repository_trends(
    repository_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieves chronological quality scorecard progression across repository runs."""
    # Verify repository exists
    repo_res = await session.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repo = repo_res.scalar_one_or_none()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {repository_id} not found",
        )

    # Fetch jobs and their reports in chronological order
    jobs_res = await session.execute(
        select(AnalysisJob)
        .where(AnalysisJob.repository_id == repository_id)
        .options(selectinload(AnalysisJob.reports))
        .order_by(AnalysisJob.created_at.asc())
    )
    jobs = jobs_res.scalars().all()

    points: list[ScorecardTrendPoint] = []
    for job in jobs:
        for rep in job.reports:
            points.append(
                ScorecardTrendPoint(
                    report_id=rep.id,
                    commit_hash=job.commit_sha,
                    analyzed_at=rep.created_at or job.created_at,
                    overall_score=rep.overall_score,
                    maintainability_score=rep.maintainability_score,
                    security_score=rep.security_score,
                    architecture_score=rep.architecture_score,
                    testing_score=rep.testing_score,
                )
            )

    # Calculate trend direction and delta
    trend_dir = "STABLE"
    delta = 0.0
    if len(points) >= 2:
        delta = round(points[-1].overall_score - points[-2].overall_score, 1)
        first_score = points[0].overall_score
        last_score = points[-1].overall_score
        if last_score - first_score >= 2.0:
            trend_dir = "IMPROVING"
        elif last_score - first_score <= -2.0:
            trend_dir = "DEGRADING"

    return ScorecardTrendResponse(
        repository_id=repo.id,
        repository_name=repo.name,
        points=points,
        trend_direction=trend_dir,  # type: ignore[arg-type]
        delta_since_previous=delta,
    )
