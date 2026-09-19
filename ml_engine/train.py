"""Training and evaluation pipeline for Software Defect Prediction.

Evaluates Random Forest classifier on benchmark software metrics
and serializes weights to ml_engine/serialized/defect_model_v1.joblib.
"""

from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from ml_engine.data.nasa_promise_dataset import (
    FEATURE_NAMES,
    generate_benchmark_dataset,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "serialized"
OUTPUT_MODEL_FILE = OUTPUT_DIR / "defect_model_v1.joblib"


def train_defect_model() -> dict[str, float]:
    """Trains and serializes the defect prediction model, returning test metrics."""
    print("Generating NASA MDP / PROMISE benchmark dataset...")
    data = generate_benchmark_dataset(n_samples=2500, defect_ratio=0.18, random_state=42)

    X_train, X_test, y_train, y_test = train_test_split(
        data.X, data.y, test_size=0.25, random_state=42, stratify=data.y
    )

    print(f"Dataset split: {len(X_train)} train samples, {len(X_test)} test samples.")
    print("Training Random Forest defect classifier...")

    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=8,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # Evaluation
    y_pred_proba = clf.predict_proba(X_test)[:, 1]
    y_pred = clf.predict(X_test)

    roc_auc = float(roc_auc_score(y_test, y_pred_proba))
    pr_auc = float(average_precision_score(y_test, y_pred_proba))
    f1 = float(f1_score(y_test, y_pred))

    print("\n--- Defect Prediction Model Benchmark Evaluation ---")
    print(f"ROC-AUC: {roc_auc:.4f} (Target: >= 0.75)")
    print(f"PR-AUC:  {pr_auc:.4f} (Target: >= 0.65)")
    print(f"F1:      {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Clean", "Defective"]))

    # Serialize
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": clf,
            "version": "rf-defect-v1.0",
            "feature_names": FEATURE_NAMES,
            "metrics": {"roc_auc": roc_auc, "pr_auc": pr_auc, "f1": f1},
        },
        OUTPUT_MODEL_FILE,
    )
    print(f"Model saved successfully to {OUTPUT_MODEL_FILE}")

    return {"roc_auc": roc_auc, "pr_auc": pr_auc, "f1": f1}


if __name__ == "__main__":
    train_defect_model()
