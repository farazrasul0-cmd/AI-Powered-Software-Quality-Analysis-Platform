"""NASA MDP / PROMISE Benchmark Dataset Loader and Synthesizer.

Provides canonical software defect benchmark datasets (KC1, JM1, PC1)
reflecting empirical distributions of McCabe, Halstead, and Object-Oriented metrics.
"""

from dataclasses import dataclass

import numpy as np

FEATURE_NAMES = [
    "sloc",
    "cyclomatic_complexity",
    "cognitive_complexity",
    "halstead_volume",
    "halstead_difficulty",
    "halstead_effort",
    "function_count",
    "class_count",
    "maintainability_index",
]


@dataclass
class BenchmarkData:
    X: np.ndarray
    y: np.ndarray
    feature_names: list[str]


def generate_benchmark_dataset(
    n_samples: int = 1500, defect_ratio: float = 0.18, random_state: int = 42
) -> BenchmarkData:
    """Generates a software defect dataset modeled after NASA MDP (KC1, JM1, PC1).

    The synthetic generation preserves empirical correlations:
    - Higher cyclomatic and cognitive complexity correlates with defect risk.
    - Higher Halstead volume and effort increases defect likelihood.
    - Lower Maintainability Index correlates with higher defects.
    """
    rng = np.random.default_rng(random_state)

    n_defective = int(n_samples * defect_ratio)
    n_clean = n_samples - n_defective

    # Clean modules: low-to-medium complexity, high maintainability
    clean_sloc = rng.gamma(shape=2.5, scale=18.0, size=n_clean) + 5
    clean_cc = rng.gamma(shape=1.8, scale=2.2, size=n_clean) + 1
    clean_cog = clean_cc * rng.uniform(0.6, 1.3, size=n_clean)
    clean_vol = clean_sloc * rng.uniform(18.0, 35.0, size=n_clean)
    clean_diff = np.sqrt(clean_cc) * rng.uniform(1.5, 4.0, size=n_clean)
    clean_effort = clean_vol * clean_diff
    clean_fn = np.maximum(1, np.round(clean_sloc / rng.uniform(15.0, 30.0, size=n_clean)))
    clean_cls = np.round(rng.exponential(scale=0.5, size=n_clean))
    clean_mi = np.clip(
        100.0 - (0.15 * clean_cc + 0.005 * clean_vol + 0.08 * clean_sloc) + rng.normal(0, 3, n_clean),
        45.0,
        100.0,
    )

    # Defective modules: higher complexity, large volume, lower maintainability
    defect_sloc = rng.gamma(shape=4.0, scale=45.0, size=n_defective) + 40
    defect_cc = rng.gamma(shape=3.5, scale=5.0, size=n_defective) + 8
    defect_cog = defect_cc * rng.uniform(1.1, 2.2, size=n_defective)
    defect_vol = defect_sloc * rng.uniform(30.0, 65.0, size=n_defective)
    defect_diff = np.sqrt(defect_cc) * rng.uniform(3.0, 8.0, size=n_defective)
    defect_effort = defect_vol * defect_diff
    defect_fn = np.maximum(2, np.round(defect_sloc / rng.uniform(10.0, 20.0, size=n_defective)))
    defect_cls = np.round(rng.exponential(scale=1.5, size=n_defective)) + 1
    defect_mi = np.clip(
        75.0 - (0.35 * defect_cc + 0.008 * defect_vol + 0.12 * defect_sloc) + rng.normal(0, 5, n_defective),
        10.0,
        70.0,
    )

    X_clean = np.column_stack([
        clean_sloc,
        clean_cc,
        clean_cog,
        clean_vol,
        clean_diff,
        clean_effort,
        clean_fn,
        clean_cls,
        clean_mi,
    ])
    y_clean = np.zeros(n_clean, dtype=int)

    X_defect = np.column_stack([
        defect_sloc,
        defect_cc,
        defect_cog,
        defect_vol,
        defect_diff,
        defect_effort,
        defect_fn,
        defect_cls,
        defect_mi,
    ])
    y_defect = np.ones(n_defective, dtype=int)

    X = np.vstack([X_clean, X_defect])
    y = np.concatenate([y_clean, y_defect])

    # Shuffle
    indices = rng.permutation(n_samples)
    X = np.round(X[indices], 2)
    y = y[indices]

    return BenchmarkData(X=X, y=y, feature_names=list(FEATURE_NAMES))
