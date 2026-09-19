"""Unit tests for Phase 4 Machine Learning Defect Prediction and TreeSHAP Explainability."""

import pytest
from httpx import AsyncClient
from ml_engine.data.nasa_promise_dataset import FEATURE_NAMES, generate_benchmark_dataset
from ml_engine.models.defect_predictor import DefectPredictor
from ml_engine.models.shap_explainer import DefectShapExplainer
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import JobStatus, RiskTier
from app.infrastructure.db.models.analysis_job import AnalysisJob
from app.infrastructure.db.models.analysis_report import AnalysisReport
from app.infrastructure.db.models.defect_prediction import DefectPrediction
from app.infrastructure.db.models.file_metric import FileMetric
from app.infrastructure.db.models.repository import Repository
from app.services.ml_service import MLDefectService


def test_benchmark_dataset_generation():
    """Verifies that the synthetic NASA MDP / PROMISE dataset produces valid distributions."""
    data = generate_benchmark_dataset(n_samples=200, defect_ratio=0.20, random_state=42)
    assert data.X.shape == (200, len(FEATURE_NAMES))
    assert len(data.y) == 200
    assert sum(data.y) == 40  # 20% defective
    assert data.feature_names == FEATURE_NAMES


def test_defect_feature_extraction():
    """Verifies that features are correctly extracted from FileMetric objects and dicts."""
    predictor = DefectPredictor()

    metric_dict = {
        "sloc": 150,
        "cyclomatic_complexity": 18,
        "cognitive_complexity": 22,
        "function_count": 8,
        "class_count": 2,
        "maintainability_index": 45.0,
        "halstead_metrics": {
            "volume": 3200.0,
            "difficulty": 14.5,
            "effort": 46400.0,
        },
    }

    feat = predictor.extract_features(metric_dict)
    assert len(feat) == 9
    assert feat[0] == 150.0  # sloc
    assert feat[1] == 18.0   # cc
    assert feat[2] == 22.0   # cog
    assert feat[3] == 3200.0 # vol
    assert feat[4] == 14.5   # diff
    assert feat[5] == 46400.0 # effort
    assert feat[6] == 8.0    # fn
    assert feat[7] == 2.0    # cls
    assert feat[8] == 45.0   # mi


def test_defect_probability_and_risk_tiers():
    """Verifies model probability calibration and risk tier discrimination."""
    predictor = DefectPredictor()

    clean_metric = {
        "sloc": 25,
        "cyclomatic_complexity": 2,
        "cognitive_complexity": 1,
        "function_count": 2,
        "class_count": 0,
        "maintainability_index": 92.0,
        "halstead_metrics": {"volume": 200.0, "difficulty": 2.0, "effort": 400.0},
    }

    complex_metric = {
        "sloc": 450,
        "cyclomatic_complexity": 35,
        "cognitive_complexity": 48,
        "function_count": 20,
        "class_count": 4,
        "maintainability_index": 28.0,
        "halstead_metrics": {"volume": 12000.0, "difficulty": 28.0, "effort": 336000.0},
    }

    clean_prob, clean_tier = predictor.predict_single(clean_metric)
    complex_prob, complex_tier = predictor.predict_single(complex_metric)

    assert 0.0 <= clean_prob <= 1.0
    assert 0.0 <= complex_prob <= 1.0
    assert complex_prob > clean_prob
    assert clean_tier in ["LOW", "MODERATE"]
    assert complex_tier in ["HIGH", "CRITICAL"]


def test_shap_explainer_local_attribution():
    """Verifies that TreeSHAP computes factor attributions, percentages, and remediation advice."""
    predictor = DefectPredictor()
    explainer = DefectShapExplainer(predictor.model, predictor.feature_names)

    sample_metric = {
        "sloc": 320,
        "cyclomatic_complexity": 28,
        "cognitive_complexity": 34,
        "function_count": 12,
        "class_count": 3,
        "maintainability_index": 35.0,
        "halstead_metrics": {"volume": 8500.0, "difficulty": 22.0, "effort": 187000.0},
    }

    feat = predictor.extract_features(sample_metric)
    prob = float(predictor.predict_proba(feat)[0])

    explanation = explainer.explain(feat, prob)

    assert "base_value" in explanation
    assert "predicted_probability" in explanation
    assert "dominant_factor" in explanation
    assert "summary" in explanation
    assert len(explanation["factors"]) == 9

    # Check that factors contain required keys
    for factor in explanation["factors"]:
        assert "feature_name" in factor
        assert "display_name" in factor
        assert "feature_value" in factor
        assert "shap_value" in factor
        assert factor["impact_direction"] in ["INCREASES_RISK", "DECREASES_RISK"]
        assert "percentage" in factor
        assert "remediation" in factor

    # Verify percentages sum approximately to 100%
    total_pct = sum(f["percentage"] for f in explanation["factors"])
    assert 98.0 <= total_pct <= 102.0


def test_ml_service_predict_file_and_batch():
    """Verifies that MLDefectService produces populated DefectPrediction entities."""
    service = MLDefectService()

    metric = FileMetric(
        report_id="test-rep-1",
        file_path="src/engine/complex_processor.py",
        language="python",
        sloc=180,
        cyclomatic_complexity=20,
        cognitive_complexity=25,
        function_count=6,
        class_count=1,
        maintainability_index=52.0,
        halstead_metrics={"volume": 4200.0, "difficulty": 18.0, "effort": 75600.0},
    )

    pred = service.predict_file(metric, report_id="test-rep-1")

    assert pred.report_id == "test-rep-1"
    assert pred.file_path == "src/engine/complex_processor.py"
    assert 0.0 <= pred.defect_probability <= 1.0
    assert pred.risk_tier in [RiskTier.CRITICAL, RiskTier.HIGH, RiskTier.MODERATE, RiskTier.LOW]
    assert "factors" in pred.shap_factors
    assert len(pred.shap_factors["factors"]) == 9


@pytest.mark.asyncio
async def test_defects_api_endpoints(async_client: AsyncClient, db_session: AsyncSession):
    """Tests GET /api/v1/reports/{id}/defects and /defects/summary endpoints."""
    # 1. Seed Repository and Report
    repo = Repository(name="Defect API Test", url="https://github.com/org/defect-api")
    db_session.add(repo)
    await db_session.flush()

    job = AnalysisJob(
        repository_id=repo.id,
        commit_sha="abc1234",
        status=JobStatus.COMPLETED,
        progress_percent=100.0,
    )
    db_session.add(job)
    await db_session.flush()

    report = AnalysisReport(
        job_id=job.id,
        overall_score=80.0,
        maintainability_score=75.0,
        security_score=90.0,
        testing_score=85.0,
        architecture_score=80.0,
        total_files=3,
        total_lines_of_code=400,
        total_functions=15,
        total_classes=3,
        technical_debt_minutes=30,
        summary_metadata={},
    )
    db_session.add(report)
    await db_session.flush()

    # Seed 3 Defect Predictions
    pred1 = DefectPrediction(
        report_id=report.id,
        file_path="src/critical_module.py",
        defect_probability=0.88,
        risk_tier=RiskTier.CRITICAL,
        model_version="rf-defect-v1.0",
        shap_factors={"dominant_factor": "cyclomatic_complexity", "factors": []},
    )
    pred2 = DefectPrediction(
        report_id=report.id,
        file_path="src/high_risk_service.py",
        defect_probability=0.62,
        risk_tier=RiskTier.HIGH,
        model_version="rf-defect-v1.0",
        shap_factors={"dominant_factor": "halstead_effort", "factors": []},
    )
    pred3 = DefectPrediction(
        report_id=report.id,
        file_path="src/clean_utils.py",
        defect_probability=0.12,
        risk_tier=RiskTier.LOW,
        model_version="rf-defect-v1.0",
        shap_factors={"dominant_factor": "maintainability_index", "factors": []},
    )
    db_session.add_all([pred1, pred2, pred3])
    await db_session.commit()

    client = async_client
    # Test 1: Fetch all defects (sorted desc)
    resp = await client.get(f"/api/v1/reports/{report.id}/defects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["defect_probability"] == 0.88
    assert data[0]["risk_tier"] == "CRITICAL"
    assert data[2]["defect_probability"] == 0.12

    # Test 2: Filter by risk_tier
    resp_crit = await client.get(f"/api/v1/reports/{report.id}/defects?risk_tier=CRITICAL")
    assert resp_crit.status_code == 200
    crit_data = resp_crit.json()
    assert len(crit_data) == 1
    assert crit_data[0]["file_path"] == "src/critical_module.py"

    # Test 3: Filter by min_probability
    resp_prob = await client.get(f"/api/v1/reports/{report.id}/defects?min_probability=0.50")
    assert resp_prob.status_code == 200
    assert len(resp_prob.json()) == 2

    # Test 4: Defect Summary Endpoint
    resp_summary = await client.get(f"/api/v1/reports/{report.id}/defects/summary")
    assert resp_summary.status_code == 200
    summary = resp_summary.json()
    assert summary["total_files_analyzed"] == 3
    assert summary["critical_count"] == 1
    assert summary["high_count"] == 1
    assert summary["moderate_count"] == 0
    assert summary["low_count"] == 1
    assert summary["highest_risk_file"] == "src/critical_module.py"
    assert summary["highest_risk_probability"] == 0.88

