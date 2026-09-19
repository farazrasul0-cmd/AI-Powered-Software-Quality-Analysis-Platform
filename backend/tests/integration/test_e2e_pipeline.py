"""Multi-Language End-to-End Analysis Pipeline Integration Test.

Tests complete platform lifecycle on a simulated Python + TypeScript repository:
Clone/Input -> AST Parsing -> Static Vulnerability Scan -> ML Defect Scoring ->
Hybrid LLM Review -> Multi-Pillar Scorecard -> SARIF / Markdown / HTML Export -> PR Commenting.
"""

import pytest

from app.domain.enums import FindingCategory, FindingSeverity, RiskTier
from app.infrastructure.ast_parser.python_visitor import analyze_python_source
from app.infrastructure.db.models.analysis_report import AnalysisReport
from app.infrastructure.db.models.defect_prediction import DefectPrediction
from app.infrastructure.db.models.file_metric import FileMetric
from app.infrastructure.db.models.issue import Issue
from app.infrastructure.github.pr_commenter import MockGitHubPRClient
from app.infrastructure.rag.chunker import UnifiedSemanticChunker
from app.services.export_service import ExportService
from app.services.hybrid_review_service import HybridReviewService
from app.services.scoring_service import ScoringService


@pytest.mark.asyncio
async def test_complete_multi_language_e2e_pipeline():
    # -------------------------------------------------------------------------
    # 1. Multi-Language Codebase Files
    # -------------------------------------------------------------------------
    python_code = """import sqlite3

def get_user_profile(user_input: str):
    conn = sqlite3.connect("users.db")
    # CWE-89 SQL Injection
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    return conn.cursor().execute(query).fetchall()

def complex_calculator(data, threshold):
    total = 0
    if data:
        for x in data:
            if x > threshold:
                for k in range(5):
                    total += x * k
    return total
"""

    typescript_code = """import React, { useState } from 'react';

interface WidgetProps {
    title: string;
    onSelect: (id: string) => void;
}

export const WidgetViewer: React.FC<WidgetProps> = ({ title, onSelect }) => {
    const [count, setCount] = useState<number>(0);

    const handleClick = () => {
        setCount(count + 1);
        onSelect(title);
    };

    return (
        <div className="p-4 bg-slate-900 rounded">
            <h2>{title}</h2>
            <button onClick={handleClick}>Clicked {count} times</button>
        </div>
    );
};
"""

    test_mock_code = """import unittest

class TestMock(unittest.TestCase):
    def test_sample(self):
        # Benign test mock credential candidate for suppression
        mock_password = "dummy_test_password_123"
        self.assertEqual(len(mock_password), 23)
"""

    # -------------------------------------------------------------------------
    # 2. Stage 1: AST Parsing & Semantic Chunking
    # -------------------------------------------------------------------------
    py_metrics = analyze_python_source(python_code)
    assert py_metrics.sloc > 10
    assert py_metrics.total_cyclomatic_complexity >= 4

    ts_chunks = UnifiedSemanticChunker.chunk_file("frontend/src/WidgetViewer.tsx", typescript_code)
    assert len(ts_chunks) >= 1
    assert any("WidgetViewer" in c.symbol_name for c in ts_chunks)

    # -------------------------------------------------------------------------
    # 3. Stage 2: Static Vulnerability Detection
    # -------------------------------------------------------------------------
    sqli_issue = Issue(
        report_id="e2e-report",
        rule_id="SEC-SQLI",
        cwe_id="CWE-89",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.CRITICAL,
        file_path="backend/app/auth.py",
        line_start=7,
        line_end=7,
        title="SQL Injection",
        description="Direct SQL concatenation format string",
    )

    test_fixture_issue = Issue(
        report_id="e2e-report",
        rule_id="SEC-PWD-HARDCODED",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        file_path="tests/test_mock.py",
        line_start=6,
        line_end=6,
        title="Hardcoded Credential in Test",
        description="mock_password in test module",
    )

    # -------------------------------------------------------------------------
    # 4. Stage 3: ML Defect Risk Prediction
    # -------------------------------------------------------------------------
    py_defect = DefectPrediction(
        report_id="e2e-report",
        file_path="backend/app/auth.py",
        defect_probability=0.78,
        risk_tier=RiskTier.HIGH,
        model_version="defect_model_v1",
        shap_factors={},
    )

    # -------------------------------------------------------------------------
    # 5. Stage 4: Hybrid AI Review & False Positive Suppression
    # -------------------------------------------------------------------------
    hybrid_service = HybridReviewService()
    comments, review_out = await hybrid_service.review_file(
        repository_id="e2e-repo",
        file_path="backend/app/auth.py",
        code_content=python_code,
        static_issues=[sqli_issue],
        defect_prediction=py_defect,
        report_id="e2e-report",
    )

    # Verify review generated finding with patch
    assert len(review_out.findings) >= 1
    first_finding = review_out.findings[0]
    assert first_finding.suggested_fix is not None
    assert "@@" in first_finding.suggested_fix.unified_diff

    # Review comment created for database persistence
    assert len(comments) >= 1
    assert comments[0].suggested_patch is not None

    # Also review test fixture file to trigger false positive suppression
    _, test_review_out = await hybrid_service.review_file(
        repository_id="e2e-repo",
        file_path="tests/test_mock.py",
        code_content=test_mock_code,
        static_issues=[test_fixture_issue],
        report_id="e2e-report",
    )
    # The test fixture finding is classified as FALSE_POSITIVE_OVERRIDE
    fp_override = next(
        (f for f in test_review_out.findings if f.category == "FALSE_POSITIVE_OVERRIDE"),
        None,
    )
    assert fp_override is not None

    # -------------------------------------------------------------------------
    # 6. Stage 5: Multi-Pillar Composite Scorecard Calculation
    # -------------------------------------------------------------------------
    file_metrics = [
        FileMetric(
            report_id="e2e-report",
            file_path="backend/app/auth.py",
            sloc=py_metrics.sloc,
            cyclomatic_complexity=py_metrics.total_cyclomatic_complexity,
            cognitive_complexity=py_metrics.total_cyclomatic_complexity + 2,
            maintainability_index=75.0,
        ),
        FileMetric(
            report_id="e2e-report",
            file_path="frontend/src/WidgetViewer.tsx",
            sloc=30,
            cyclomatic_complexity=2,
            cognitive_complexity=1,
            maintainability_index=90.0,
        ),
        FileMetric(
            report_id="e2e-report",
            file_path="tests/test_mock.py",
            sloc=10,
            cyclomatic_complexity=1,
            cognitive_complexity=1,
            maintainability_index=95.0,
        ),
    ]

    all_issues = [sqli_issue, test_fixture_issue]
    all_reviews = [*review_out.findings, *test_review_out.findings]

    scorecard = ScoringService.calculate_scores(
        file_metrics=file_metrics,
        issues=all_issues,
        reviews=all_reviews,
        defect_predictions=[py_defect],
    )

    # Verify score calculation and false positive suppression
    assert scorecard.overall_score > 50.0
    assert scorecard.grade in ("A", "B", "C", "D")
    assert scorecard.false_positives_suppressed == 1  # test_mock.py suppressed
    assert len(scorecard.recommendations) >= 1
    assert scorecard.recommendations[0]["pillar"] in ("Security", "Architecture")

    # -------------------------------------------------------------------------
    # 7. Stage 6: Report Exporting (SARIF, Markdown, HTML)
    # -------------------------------------------------------------------------
    report = AnalysisReport(
        id="e2e-report",
        job_id="e2e-job",
        overall_score=scorecard.overall_score,
        maintainability_score=scorecard.maintainability_score,
        security_score=scorecard.security_score,
        testing_score=scorecard.testing_score,
        architecture_score=scorecard.architecture_score,
        total_files=3,
        total_lines_of_code=py_metrics.sloc + 40,
        technical_debt_minutes=scorecard.technical_debt_minutes,
        summary_metadata={},
    )
    report.file_metrics = file_metrics
    report.issues = all_issues
    report.defect_predictions = [py_defect]
    report.review_comments = comments

    # A. SARIF v2.1.0 Export
    sarif = ExportService.generate_sarif(report, scorecard)
    assert sarif.version == "2.1.0"
    assert len(sarif.runs[0].results) >= 2

    # B. Markdown Summary
    md_summary = ExportService.generate_markdown_summary(report, scorecard, repo_name="MultiLang Repo")
    assert "# 🛡️ Software Quality Analysis: MultiLang Repo" in md_summary
    assert "Triangulation Engine Note" in md_summary

    # C. Printable HTML Executive Report
    html_report = ExportService.generate_printable_html(report, scorecard, repo_name="MultiLang Repo")
    assert "<!DOCTYPE html>" in html_report
    assert "MultiLang Repo" in html_report
    assert "window.print()" in html_report

    # -------------------------------------------------------------------------
    # 8. Stage 7: GitHub PR Commenting
    # -------------------------------------------------------------------------
    github_client = MockGitHubPRClient()

    summary_comment = await github_client.post_pr_summary(
        repo_full_name="example-org/multi-lang-app",
        pr_number=88,
        markdown_body=md_summary,
    )
    assert summary_comment["status"] == "success"
    assert len(github_client.posted_summaries) == 1

    inline_review = await github_client.post_inline_review(
        repo_full_name="example-org/multi-lang-app",
        pr_number=88,
        commit_sha="fedcba9876",
        summary_body=f"Automated AI Review: Grade {scorecard.grade}",
        comments=[
            {
                "path": c.file_path,
                "line": c.line_number,
                "body": c.comment,
            }
            for c in comments
        ],
    )
    assert inline_review["status"] == "success"
    assert len(github_client.posted_reviews) == 1
    assert len(github_client.posted_reviews[0]["comments"]) >= 1
