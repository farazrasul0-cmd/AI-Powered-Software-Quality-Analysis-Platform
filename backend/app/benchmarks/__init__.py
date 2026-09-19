"""Academic Benchmark Experiments Testbed for Empirical Software Quality Evaluation.

Contains ground-truth corpora, evaluation metrics, and deterministic runners for:
- RQ1: Detection accuracy across Static Alone, LLM Alone, and Hybrid Triangulation.
- RQ2: Defect ranking efficiency (Recall@Top20%LOC / Pareto curves).
- RQ3: False Positive Suppression Rate (FPSR) on benign test fixtures.
"""

from app.benchmarks.corpus import BENCHMARK_CORPUS, BenchmarkSample
from app.benchmarks.evaluator import AcademicBenchmarkEvaluator, BenchmarkSuiteResult

__all__ = [
    "BENCHMARK_CORPUS",
    "BenchmarkSample",
    "AcademicBenchmarkEvaluator",
    "BenchmarkSuiteResult",
]
