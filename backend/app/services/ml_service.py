"""Machine Learning Defect Prediction Service.

Bridges AST FileMetric records to the ML inference and TreeSHAP explainability engine.
"""

import sys
from pathlib import Path
from typing import Any

# Ensure project root or app root is in sys.path for ml_engine imports
for p in Path(__file__).resolve().parents:
    if (p / "ml_engine").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))
        break

from ml_engine.models.defect_predictor import DefectPredictor  # noqa: E402
from ml_engine.models.shap_explainer import DefectShapExplainer  # noqa: E402

from app.domain.enums import RiskTier  # noqa: E402
from app.infrastructure.db.models.defect_prediction import DefectPrediction  # noqa: E402
from app.infrastructure.db.models.file_metric import FileMetric  # noqa: E402


class MLDefectService:
    """Service providing ML defect risk inference and local TreeSHAP explanations."""

    def __init__(self, model_path: Path | str | None = None) -> None:
        self.predictor = DefectPredictor(model_path=model_path)
        self.explainer = DefectShapExplainer(
            model=self.predictor.model,
            feature_names=self.predictor.feature_names,
        )

    def predict_file(self, metric: FileMetric | dict[str, Any], report_id: str = "") -> DefectPrediction:
        """Predicts defect probability and generates TreeSHAP factors for a single file."""
        feat = self.predictor.extract_features(metric)
        prob, tier_str = self.predictor.predict_single(metric)

        shap_explanation = self.explainer.explain(feat, prob)

        file_path = (
            getattr(metric, "file_path", "")
            if hasattr(metric, "file_path")
            else metric.get("file_path", "unknown")
        )

        return DefectPrediction(
            report_id=report_id,
            file_path=file_path,
            defect_probability=round(prob, 3),
            risk_tier=RiskTier(tier_str),
            model_version=self.predictor.model_version,
            shap_factors=shap_explanation,
        )

    def predict_batch(
        self, metrics: list[FileMetric | dict[str, Any]], report_id: str = ""
    ) -> list[DefectPrediction]:
        """Predicts defect probabilities and explanations for a list of file metrics."""
        predictions: list[DefectPrediction] = []
        for m in metrics:
            pred = self.predict_file(m, report_id=report_id)
            predictions.append(pred)
        return predictions


# Default service instance for zero-cold-start inference
ml_defect_service = MLDefectService()
