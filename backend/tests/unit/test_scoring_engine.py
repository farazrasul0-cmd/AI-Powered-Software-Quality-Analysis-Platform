"""Unit tests for Phase 6 Multi-Dimensional Quality Scoring Engine."""

from app.api.v1.schemas.review import CodeReviewFinding, FindingCategoryEnum, SeverityEnum
from app.domain.enums import FindingCategory, FindingSeverity
from app.infrastructure.db.models.file_metric import FileMetric
from app.infrastructure.db.models.issue import Issue
from app.services.scoring_service import ScoringService


def test_clean_repository_scoring():
    metric = FileMetric(
        report_id="rep-1",
        file_path="src/utils.py",
        sloc=100,
        cyclomatic_complexity=4,
        cognitive_complexity=3,
        function_count=4,
        class_count=1,
        maintainability_index=95.0,
        halstead_metrics={"effort": 2000.0, "volume": 500.0},
    )
    test_metric = FileMetric(
        report_id="rep-1",
        file_path="tests/test_utils.py",
        sloc=80,
        cyclomatic_complexity=2,
        cognitive_complexity=1,
        function_count=3,
        class_count=1,
        maintainability_index=98.0,
        halstead_metrics={"effort": 1000.0},
    )

    scorecard = ScoringService.calculate_scores([metric, test_metric], [])
    assert scorecard.overall_score >= 85.0
    assert scorecard.grade in ("A", "B")
    assert scorecard.security_score == 100.0
    assert scorecard.technical_debt_minutes == 0
    assert len(scorecard.radar_data) == 5
    assert len(scorecard.pillars) == 4


def test_false_positive_suppression_protection():
    """Confirms that alerts classified as FALSE_POSITIVE_OVERRIDE do not penalize security."""
    metric = FileMetric(
        report_id="rep-2",
        file_path="tests/fixtures/mock_auth.py",
        sloc=60,
        cyclomatic_complexity=2,
        cognitive_complexity=1,
        function_count=2,
        class_count=0,
        maintainability_index=90.0,
    )
    test_sec_issue = Issue(
        report_id="rep-2",
        rule_id="SEC-PWD-HARDCODED",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        file_path="tests/fixtures/mock_auth.py",
        line_start=15,
        line_end=15,
        title="Hardcoded Credential in Test Fixture",
        description="password = 'mock_secret_key'",
    )

    # 1. Without suppression: Security score suffers a 15-point penalty
    unsuppressed = ScoringService.calculate_scores([metric], [test_sec_issue])
    assert unsuppressed.security_score == 85.0
    assert unsuppressed.technical_debt_minutes == 90
    assert unsuppressed.false_positives_suppressed == 0

    # 2. With suppression via Hybrid Review Finding: Security score stays 100.0
    fp_finding = CodeReviewFinding(
        file_path="tests/fixtures/mock_auth.py",
        line_start=15,
        line_end=15,
        title="Hardcoded Password Detected in Test Fixture",
        category=FindingCategoryEnum.FALSE_POSITIVE_OVERRIDE,
        severity=SeverityEnum.MINOR,
        confidence_score=0.95,
        triangulation_status="FALSE_POSITIVE_SUPPRESSED",
        rule_id="SEC-PWD-HARDCODED",
        issue_description="Benign test mock credential",
        remediation_advice="No action required for test mock",
    )

    suppressed = ScoringService.calculate_scores(
        [metric],
        [test_sec_issue],
        reviews=[fp_finding],
    )
    assert suppressed.security_score == 100.0
    assert suppressed.technical_debt_minutes == 0
    assert suppressed.false_positives_suppressed == 1


def test_architecture_penalties_and_ml_defect_risk():
    """Verifies circular dependency and TreeSHAP ML defect probability penalties."""
    metric = FileMetric(
        report_id="rep-3",
        file_path="src/services/order.py",
        sloc=200,
        cyclomatic_complexity=12,
        cognitive_complexity=15,
        function_count=10,
        class_count=2,
        maintainability_index=65.0,
    )

    circular_cycles = [["app.services.order", "app.services.payment", "app.services.order"]]
    defect_predictions = [
        {"file_path": "src/services/order.py", "defect_probability": 0.85, "risk_tier": "CRITICAL"}
    ]

    scorecard = ScoringService.calculate_scores(
        [metric],
        [],
        circular_dependencies=circular_cycles,
        defect_predictions=defect_predictions,
    )

    # Circular cycle costs 15 points; ML defect risk costs ~30*0.85 + 20 = ~45 points (capped at 35)
    assert scorecard.architecture_score <= 60.0
    assert len(scorecard.recommendations) >= 1
    # Check that highest recommendation highlights defect prone module or circular cycle
    first_rec = scorecard.recommendations[0]
    assert first_rec["pillar"] == "Architecture"


def test_letter_grade_thresholds():
    assert ScoringService._assign_grade(95.0) == "A"
    assert ScoringService._assign_grade(90.0) == "A"
    assert ScoringService._assign_grade(85.0) == "B"
    assert ScoringService._assign_grade(75.0) == "C"
    assert ScoringService._assign_grade(65.0) == "D"
    assert ScoringService._assign_grade(55.0) == "F"
