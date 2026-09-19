"""Unit tests for Software Quality Scoring Service."""

from app.domain.enums import FindingCategory, FindingSeverity
from app.infrastructure.db.models.file_metric import FileMetric
from app.infrastructure.db.models.issue import Issue
from app.services.scoring_service import ScoringService


def test_perfect_clean_scorecard():
    metric = FileMetric(
        report_id="dummy",
        file_path="src/main.py",
        sloc=50,
        cyclomatic_complexity=2,
        cognitive_complexity=2,
        function_count=3,
        class_count=1,
        maintainability_index=95.0,
        halstead_metrics={},
    )
    scorecard = ScoringService.calculate_scores([metric], [])
    assert scorecard.overall_score >= 80.0
    assert scorecard.security_score == 100.0
    assert scorecard.technical_debt_minutes == 0


def test_score_penalties_with_critical_issues():
    metric = FileMetric(
        report_id="dummy",
        file_path="src/auth.py",
        sloc=150,
        cyclomatic_complexity=20,  # High complexity penalty
        maintainability_index=55.0,
        halstead_metrics={},
    )
    critical_sec_issue = Issue(
        report_id="dummy",
        rule_id="SEC-SQLI",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.CRITICAL,
        file_path="src/auth.py",
        line_start=10,
        line_end=12,
        title="SQL Injection",
        description="Raw SQL query",
    )
    scorecard = ScoringService.calculate_scores([metric], [critical_sec_issue])
    assert scorecard.security_score <= 75.0
    assert scorecard.technical_debt_minutes == 180
    assert scorecard.overall_score < 75.0
