"""Integration tests for Scorecard and Benchmark REST Endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import FindingCategory, FindingSeverity, JobStatus
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.models.analysis_report import AnalysisReport
from app.infrastructure.db.models.file_metric import FileMetric
from app.infrastructure.db.models.issue import Issue
from app.infrastructure.db.models.repository import Repository


@pytest.mark.asyncio
async def test_benchmark_experiments_endpoint(async_client: AsyncClient):
    res = await async_client.get("/api/v1/benchmarks/experiments")
    assert res.status_code == 200
    data = res.json()
    assert data["total_samples"] >= 5
    assert data["rq1"]["f1_improvement_over_static"] > 0.0
    assert data["rq2"]["recall_at_top_20_pct_loc"] >= 70.0
    assert data["rq3"]["false_positive_suppression_rate"] >= 30.0


@pytest.mark.asyncio
async def test_benchmark_corpus_endpoint(async_client: AsyncClient):
    res = await async_client.get("/api/v1/benchmarks/corpus")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5
    assert any(s["sample_id"] == "SEC_01_SQLI_CMD" for s in data)


@pytest.mark.asyncio
async def test_report_scorecard_endpoint(
    async_client: AsyncClient, db_session: AsyncSession
):
    # 1. Seed dummy repo, job, report, file metrics, issues
    repo = Repository(
        name="Scorecard Test Repo",
        url="https://github.com/example/scorecard-test.git",
        default_branch="main",
    )
    db_session.add(repo)
    await db_session.flush()

    job = AnalysisJob(
        repository_id=repo.id,
        status=JobStatus.COMPLETED,
        current_stage="COMPLETED",
        progress_percent=100.0,
    )
    db_session.add(job)
    await db_session.flush()

    report = AnalysisReport(
        job_id=job.id,
        overall_score=85.0,
        maintainability_score=80.0,
        security_score=90.0,
        testing_score=75.0,
        architecture_score=85.0,
        total_files=2,
        total_lines_of_code=150,
        technical_debt_minutes=30,
        summary_metadata={"circular_dependencies": []},
    )
    db_session.add(report)
    await db_session.flush()

    metric = FileMetric(
        report_id=report.id,
        file_path="src/main.py",
        sloc=100,
        cyclomatic_complexity=4,
        cognitive_complexity=3,
        maintainability_index=88.0,
        function_count=4,
        class_count=1,
    )
    issue = Issue(
        report_id=report.id,
        rule_id="SEC-01",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.LOW,
        file_path="src/main.py",
        line_start=10,
        line_end=11,
        title="Minor Sec Finding",
        description="Minor detail",
    )
    db_session.add(metric)
    db_session.add(issue)
    await db_session.commit()

    # 2. Query Scorecard endpoint
    res = await async_client.get(f"/api/v1/reports/{report.id}/scorecard")
    assert res.status_code == 200
    scorecard = res.json()
    assert scorecard["report_id"] == report.id
    assert scorecard["overall_score"] > 0
    assert scorecard["grade"] in ("A", "B", "C", "D", "F")
    assert len(scorecard["radar_data"]) == 5
    assert len(scorecard["pillars"]) == 4

    # 3. Query Repository Trends endpoint
    trend_res = await async_client.get(f"/api/v1/repositories/{repo.id}/trends")
    assert trend_res.status_code == 200
    trend_data = trend_res.json()
    assert trend_data["repository_id"] == repo.id
    assert len(trend_data["points"]) == 1
    assert trend_data["points"][0]["report_id"] == report.id
