"""Unit tests for Phase 5 Hybrid Code Review & False Positive Triangulation."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.review import (
    FindingCategoryEnum,
    SeverityEnum,
    TriangulationStatusEnum,
)
from app.domain.enums import CommentStatus, JobStatus
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.models.analysis_report import AnalysisReport
from app.infrastructure.db.models.repository import Repository
from app.infrastructure.db.models.review_comment import ReviewComment
from app.infrastructure.llm.mock_reviewer import MockLLMReviewer
from app.infrastructure.rag.vector_store import InMemoryVectorStore
from app.services.hybrid_review_service import (
    HybridReviewService,
    calculate_rank_score,
)


def test_composite_rank_score_formula():
    """Verifies that RankScore adheres to 0.45*Sev + 0.30*P(defect) + 0.25*Conf."""
    # Critical (1.0), P=0.90, Conf=0.95
    score1 = calculate_rank_score(SeverityEnum.CRITICAL, 0.90, 0.95)
    # 0.45*1.0 + 0.30*0.90 + 0.25*0.95 = 0.45 + 0.27 + 0.2375 = 0.9575
    assert score1 == 0.9575

    # Minor (0.4), P=0.10, Conf=0.80
    score2 = calculate_rank_score(SeverityEnum.MINOR, 0.10, 0.80)
    # 0.45*0.4 + 0.30*0.10 + 0.25*0.80 = 0.18 + 0.03 + 0.20 = 0.41
    assert score2 == 0.41


@pytest.mark.asyncio
async def test_false_positive_suppression_on_test_fixture():
    """Verifies that hardcoded secrets in test fixtures are suppressed as false alarms."""
    service = HybridReviewService(
        llm_client=MockLLMReviewer(),
        store=InMemoryVectorStore(),
    )

    test_code = '''
def test_login_endpoint():
    dummy_secret = "admin123"
    assert dummy_secret is not None
'''

    static_issues = [
        {
            "rule_id": "SEC-HARDCODED-SECRET",
            "title": "Hardcoded secret detected",
            "category": "SECURITY",
            "severity": "CRITICAL",
            "line_start": 3,
            "line_end": 3,
            "description": "Found string password in variable",
        }
    ]

    comments, review_out = await service.review_file(
        repository_id="repo-1",
        file_path="tests/fixtures/test_auth.py",
        code_content=test_code,
        static_issues=static_issues,
        defect_prediction={"defect_probability": 0.12, "risk_tier": "LOW"},
    )

    # 1. Active Review Comments should be 0 because the false positive was suppressed
    assert len(comments) == 0

    # 2. Review Output should document the override
    assert len(review_out.findings) == 1
    override = review_out.findings[0]
    assert override.category == FindingCategoryEnum.FALSE_POSITIVE_OVERRIDE
    assert override.triangulation_status == TriangulationStatusEnum.FALSE_POSITIVE_SUPPRESSED
    assert "test directory" in override.triangulation_rationale.lower()


@pytest.mark.asyncio
async def test_confirmed_vulnerability_with_suggested_diff():
    """Verifies that genuine SQL injection produces a confirmed review comment with patch."""
    service = HybridReviewService(
        llm_client=MockLLMReviewer(),
        store=InMemoryVectorStore(),
    )

    sql_code = '''
def find_user(cursor, user_id):
    cursor.execute(f"SELECT * FROM users WHERE username = '{user_id}'")
'''

    static_issues = [
        {
            "rule_id": "SEC-SQL-INJECTION",
            "title": "SQL Injection Detected (CWE-89)",
            "category": "SECURITY",
            "severity": "CRITICAL",
            "line_start": 3,
            "line_end": 3,
            "description": "Formatted string in SQL execute",
        }
    ]

    comments, review_out = await service.review_file(
        repository_id="repo-1",
        file_path="src/repositories/user_repo.py",
        code_content=sql_code,
        static_issues=static_issues,
        defect_prediction={"defect_probability": 0.65, "risk_tier": "HIGH"},
    )

    assert len(comments) == 1
    comment = comments[0]
    assert comment.file_path == "src/repositories/user_repo.py"
    assert comment.line_number == 3
    assert "SQL Injection" in comment.comment
    assert comment.suggested_patch is not None
    assert "--- a/" in comment.suggested_patch
    assert "cursor.execute(" in comment.suggested_patch


@pytest.mark.asyncio
async def test_defect_risk_escalation():
    """Verifies that high ML defect risk escalates inspection even without static rule flags."""
    service = HybridReviewService(
        llm_client=MockLLMReviewer(),
        store=InMemoryVectorStore(),
    )

    complex_code = '''
def complex_workflow(a, b, c, d):
    if a:
        if b:
            for x in c:
                if x > 10:
                    return d
    return None
'''

    comments, review_out = await service.review_file(
        repository_id="repo-1",
        file_path="src/engine/processor.py",
        code_content=complex_code,
        static_issues=[],  # Zero static flags
        defect_prediction={"defect_probability": 0.88, "risk_tier": "CRITICAL"},
    )

    assert len(comments) == 1
    assert "High Defect Risk" in comments[0].comment
    assert review_out.predicted_risk_level == "CRITICAL"


@pytest.mark.asyncio
async def test_reviews_rest_api_endpoints(async_client: AsyncClient, db_session: AsyncSession):
    """Verifies GET /reports/{id}/reviews and PATCH /reviews/{id}/status endpoints."""
    repo = Repository(name="Review Repo", url="https://github.com/org/rev")
    db_session.add(repo)
    await db_session.flush()

    job = AnalysisJob(
        repository_id=repo.id,
        commit_sha="fedcba9",
        status=JobStatus.COMPLETED,
        progress_percent=100.0,
    )
    db_session.add(job)
    await db_session.flush()

    report = AnalysisReport(
        job_id=job.id,
        overall_score=85.0,
        maintainability_score=80.0,
        security_score=90.0,
        testing_score=85.0,
        architecture_score=85.0,
        total_files=1,
        total_lines_of_code=100,
        total_functions=5,
        total_classes=1,
        technical_debt_minutes=20,
        summary_metadata={},
    )
    db_session.add(report)
    await db_session.flush()

    rev_comment = ReviewComment(
        report_id=report.id,
        file_path="src/api.py",
        line_number=12,
        comment="**[CRITICAL] SQL Injection** Use parameterized queries.",
        suggested_patch="@@ -1,1 +1,1 @@\n-raw_sql\n+param_sql",
        status=CommentStatus.PENDING,
    )
    db_session.add(rev_comment)
    await db_session.commit()

    # 1. GET /reports/{report_id}/reviews
    resp = await async_client.get(f"/api/v1/reports/{report.id}/reviews")
    assert resp.status_code == 200
    comments_data = resp.json()
    assert len(comments_data) == 1
    assert comments_data[0]["file_path"] == "src/api.py"
    assert comments_data[0]["status"] == "PENDING"

    # 2. PATCH /reviews/{comment_id}/status -> ACCEPTED
    comment_id = comments_data[0]["id"]
    patch_resp = await async_client.patch(
        f"/api/v1/reviews/{comment_id}/status",
        json={"status": "ACCEPTED"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "ACCEPTED"

    # Verify DB update
    updated_comment = await db_session.get(ReviewComment, comment_id)
    assert updated_comment is not None
    assert updated_comment.status == CommentStatus.ACCEPTED
