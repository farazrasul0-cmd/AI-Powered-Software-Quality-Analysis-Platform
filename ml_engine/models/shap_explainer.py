"""Local Explainable AI engine using TreeSHAP for software defect prediction.

Quantifies feature attributions for each software module, computing exact
Shapley values indicating which metrics increase or decrease defect risk.
"""

from typing import Any

import numpy as np
import shap

from ml_engine.data.nasa_promise_dataset import FEATURE_NAMES

DISPLAY_NAMES: dict[str, str] = {
    "sloc": "Source Lines of Code (SLOC)",
    "cyclomatic_complexity": "Cyclomatic Complexity",
    "cognitive_complexity": "Cognitive Complexity",
    "halstead_volume": "Halstead Volume",
    "halstead_difficulty": "Halstead Difficulty",
    "halstead_effort": "Halstead Effort",
    "function_count": "Function Count",
    "class_count": "Class Count",
    "maintainability_index": "Maintainability Index",
}

REMEDIATION_GUIDANCE: dict[str, str] = {
    "cyclomatic_complexity": "Refactor deeply branched methods; extract compound conditions into smaller helper functions.",
    "cognitive_complexity": "Reduce nesting levels and break complex control flows into linear procedures.",
    "halstead_volume": "Decompose monolithic functions and minimize intermediate operand usage.",
    "halstead_difficulty": "Reduce unique operator complexity and simplify operand transformations.",
    "halstead_effort": "Simplify computational logic to reduce mental effort required for maintenance.",
    "sloc": "Break oversized source files exceeding modular limits into cohesive, focused modules.",
    "maintainability_index": "Increase modularity, reduce method length, and adhere to clean architecture patterns.",
    "function_count": "Decompose module responsibilities into separate single-responsibility units.",
    "class_count": "Split god classes into decoupled domain services.",
}


class DefectShapExplainer:
    """Computes TreeSHAP feature attributions for defect predictions."""

    def __init__(self, model: Any, feature_names: list[str] | None = None) -> None:
        self.model = model
        self.feature_names = feature_names or list(FEATURE_NAMES)
        self.explainer = shap.TreeExplainer(model)

    def explain(self, feature_vector: np.ndarray, predicted_probability: float) -> dict[str, Any]:
        """Calculates Shapley values and human-readable risk attribution for a sample."""
        if feature_vector.ndim == 1:
            X = feature_vector.reshape(1, -1)
        else:
            X = feature_vector

        sv = self.explainer.shap_values(X)

        # Extract class 1 (defective) Shapley values
        if isinstance(sv, list) and len(sv) == 2:
            # List of arrays [class_0, class_1]
            raw_shap = sv[1][0]
        elif isinstance(sv, np.ndarray) and sv.ndim == 3 and sv.shape[2] == 2:
            # (n_samples, n_features, 2)
            raw_shap = sv[0, :, 1]
        elif isinstance(sv, np.ndarray) and sv.ndim == 2:
            # (n_samples, n_features)
            raw_shap = sv[0]
        else:
            raw_shap = np.array(sv).flatten()[: len(self.feature_names)]

        # Base value (expected probability)
        exp_val = self.explainer.expected_value
        if isinstance(exp_val, (list, np.ndarray)) and len(exp_val) >= 2:
            base_val = float(exp_val[1])
        elif isinstance(exp_val, (int, float, np.floating)):
            base_val = float(exp_val)
        else:
            base_val = 0.50

        # Calculate relative impact percentages
        abs_sum = float(np.sum(np.abs(raw_shap)))
        if abs_sum <= 0:
            abs_sum = 1e-6

        factors: list[dict[str, Any]] = []
        for i, name in enumerate(self.feature_names):
            val = float(X[0, i])
            shap_val = float(raw_shap[i])
            pct = round((abs(shap_val) / abs_sum) * 100.0, 1)
            direction = "INCREASES_RISK" if shap_val >= 0 else "DECREASES_RISK"

            factors.append({
                "feature_name": name,
                "display_name": DISPLAY_NAMES.get(name, name),
                "feature_value": round(val, 2),
                "shap_value": round(shap_val, 4),
                "impact_direction": direction,
                "percentage": pct,
                "remediation": REMEDIATION_GUIDANCE.get(name, "Review metric and consider refactoring."),
            })

        # Sort factors by absolute magnitude descending
        factors.sort(key=lambda f: abs(f["shap_value"]), reverse=True)

        dominant = factors[0] if factors else None
        dominant_name = dominant["feature_name"] if dominant else "general_metrics"

        # Generate engineering summary
        pos_factors = [f for f in factors if f["impact_direction"] == "INCREASES_RISK"]
        if pos_factors and predicted_probability >= 0.50:
            top_pos = pos_factors[0]
            summary = (
                f"{top_pos['display_name']} ({top_pos['feature_value']}) is the primary risk driver, "
                f"accounting for {top_pos['percentage']}% of elevated defect probability."
            )
        elif predicted_probability < 0.25:
            summary = "Module exhibits healthy maintainability metrics with low statistical defect likelihood."
        else:
            summary = "Moderate defect risk driven by combined metric interactions."

        return {
            "base_value": round(base_val, 4),
            "predicted_probability": round(predicted_probability, 4),
            "dominant_factor": dominant_name,
            "summary": summary,
            "factors": factors,
        }
