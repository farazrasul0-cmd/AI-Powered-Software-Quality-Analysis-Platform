"""Integration tests for SARIF/HTML Exports and GitHub Webhooks endpoints."""

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import FindingCategory, FindingSeverity, JobStatus
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.models.analysis_report import AnalysisReport
from app.infrastructure.db.models.file_metric import FileMetric
from app.infrastructure.db.models.issue import Issue
from app.infrastructure.db.models.repository import Repository
from app.infrastructure.github.webhook_handler import github_webhook_handler


@pytest.mark.asyncio
async def test_exports_endpoints(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Seed dummy repo, job, report
    repo = Repository(
        name="Export Test Repo",
        url="https://github.com/example/export-test.git",
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
        overall_score=88.0,
        maintainability_score=85.0,
        security_score=90.0,
        testing_score=75.0,
        architecture_score=85.0,
        total_files=1,
        total_lines_of_code=80,
        technical_debt_minutes=45,
        summary_metadata={},
    )
    db_session.add(report)
    await db_session.flush()

    metric = FileMetric(
        report_id=report.id,
        file_path="src/app.py",
        sloc=80,
        cyclomatic_complexity=3,
        cognitive_complexity=2,
        maintainability_index=85.0,
    )
    issue = Issue(
        report_id=report.id,
        rule_id="SEC-INSECURE-HASH",
        cwe_id="CWE-327",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        file_path="src/app.py",
        line_start=15,
        line_end=15,
        title="Weak Hash Function",
        description="MD5 algorithm in use",
    )
    db_session.add(metric)
    db_session.add(issue)
    await db_session.commit()

    # 2. Test SARIF export
    sarif_res = await async_client.get(f"/api/v1/reports/{report.id}/export/sarif")
    assert sarif_res.status_code == 200
    sarif_data = sarif_res.json()
    assert sarif_data["version"] == "2.1.0"
    assert len(sarif_data["runs"][0]["results"]) >= 1

    # 3. Test Markdown export
    md_res = await async_client.get(f"/api/v1/reports/{report.id}/export/markdown")
    assert md_res.status_code == 200
    assert "# 🛡️ Software Quality Analysis" in md_res.text

    # 4. Test HTML export
    html_res = await async_client.get(f"/api/v1/reports/{report.id}/export/html")
    assert html_res.status_code == 200
    assert "<!DOCTYPE html>" in html_res.text


@pytest.mark.asyncio
async def test_github_webhook_endpoint(async_client: AsyncClient, db_session: AsyncSession):
    secret = github_webhook_handler.secret
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 101,
            "title": "Add feature X",
            "head": {"sha": "1234567890abcdef1234567890abcdef12345678", "ref": "feature-x"},
            "base": {"sha": "abcdef1234567890abcdef1234567890abcdef12", "ref": "main"},
            "html_url": "https://github.com/example/export-test/pull/101",
        },
        "repository": {
            "id": 9999,
            "name": "export-test",
            "full_name": "example/export-test",
            "clone_url": "https://github.com/example/export-test.git",
            "default_branch": "main",
        },
    }
    raw_body = json.dumps(payload).encode("utf-8")

    # 1. Request without signature -> 401
    res_no_sig = await async_client.post(
        "/api/v1/webhooks/github",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-GitHub-Event": "pull_request"},
    )
    assert res_no_sig.status_code == 401

    # 2. Request with valid HMAC signature -> 202
    expected_hash = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    res_valid_sig = await async_client.post(
        "/api/v1/webhooks/github",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": f"sha256={expected_hash}",
        },
    )
    assert res_valid_sig.status_code == 202
    data = res_valid_sig.json()
    assert data["status"] == "accepted"
    assert data["pr_number"] == 101
    assert "job_id" in data
