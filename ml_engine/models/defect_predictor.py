"""Machine Learning Defect Predictor Engine.

Predicts software defect probability for source code modules using
calibrated Random Forest tree ensembles trained on software metric benchmarks.
"""

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ml_engine.data.nasa_promise_dataset import (
    FEATURE_NAMES,
    generate_benchmark_dataset,
)

# Default serialized model path
SERIALIZED_MODEL_PATH = Path(__file__).resolve().parent.parent / "serialized" / "defect_model_v1.joblib"


class DefectPredictor:
    """Random Forest software defect prediction engine."""

    def __init__(self, model_path: Path | str | None = None) -> None:
        self.feature_names = list(FEATURE_NAMES)
        self.model_version = "rf-defect-v1.0"
        self.model: RandomForestClassifier | None = None

        target_path = Path(model_path) if model_path else SERIALIZED_MODEL_PATH
        if target_path.exists():
            self._load(target_path)
        else:
            self._train_and_persist(target_path)

    def _load(self, path: Path) -> None:
        """Loads serialized model weights."""
        saved_data = joblib.load(path)
        self.model = saved_data["model"]
        self.model_version = saved_data.get("version", self.model_version)
        self.feature_names = saved_data.get("feature_names", self.feature_names)

    def _train_and_persist(self, path: Path | None = None) -> None:
        """Trains baseline model on benchmark dataset and persists to disk."""
        data = generate_benchmark_dataset(n_samples=2000, defect_ratio=0.18, random_state=42)
        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=4,
            class_weight="balanced",
            random_state=42,
        )
        clf.fit(data.X, data.y)
        self.model = clf

        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(
                {
                    "model": self.model,
                    "version": self.model_version,
                    "feature_names": self.feature_names,
                },
                path,
            )

    def extract_features(self, metric: Any) -> np.ndarray:
        """Extracts numerical feature vector from a FileMetric object or dict."""
        if hasattr(metric, "sloc"):
            sloc = float(getattr(metric, "sloc", 0))
            cc = float(getattr(metric, "cyclomatic_complexity", 1))
            cog = float(getattr(metric, "cognitive_complexity", 0))
            fn = float(getattr(metric, "function_count", 0))
            cls_count = float(getattr(metric, "class_count", 0))
            mi = float(getattr(metric, "maintainability_index", 100.0))
            halstead = getattr(metric, "halstead_metrics", {}) or {}
            vol = float(halstead.get("volume", 0.0))
            diff = float(halstead.get("difficulty", 1.0))
            effort = float(halstead.get("effort", 0.0))
        elif isinstance(metric, dict):
            sloc = float(metric.get("sloc", 0))
            cc = float(metric.get("cyclomatic_complexity", 1))
            cog = float(metric.get("cognitive_complexity", 0))
            fn = float(metric.get("function_count", 0))
            cls_count = float(metric.get("class_count", 0))
            mi = float(metric.get("maintainability_index", 100.0))
            halstead = metric.get("halstead_metrics", {}) or {}
            vol = float(halstead.get("volume", 0.0))
            diff = float(halstead.get("difficulty", 1.0))
            effort = float(halstead.get("effort", 0.0))
        else:
            raise TypeError(f"Unsupported metric type: {type(metric)}")

        return np.array(
            [sloc, cc, cog, vol, diff, effort, fn, cls_count, mi],
            dtype=np.float64,
        )

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Computes calibrated defect probability for input feature matrix."""
        if self.model is None:
            raise RuntimeError("Model has not been trained or loaded.")

        if X.ndim == 1:
            X = X.reshape(1, -1)

        probabilities = self.model.predict_proba(X)
        # Class 1 is defective
        return probabilities[:, 1]

    def predict_single(self, metric: Any) -> tuple[float, str]:
        """Predicts defect probability and assigns calibrated risk tier for a single module."""
        feat = self.extract_features(metric)
        prob = float(self.predict_proba(feat)[0])
        prob = max(0.01, min(0.99, prob))

        if prob >= 0.75:
            tier = "CRITICAL"
        elif prob >= 0.50:
            tier = "HIGH"
        elif prob >= 0.25:
            tier = "MODERATE"
        else:
            tier = "LOW"

        return round(prob, 4), tier
