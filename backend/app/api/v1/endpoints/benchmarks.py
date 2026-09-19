"""Academic Benchmark Experiments REST API Endpoints."""

from typing import Any

from fastapi import APIRouter

from app.benchmarks.corpus import BENCHMARK_CORPUS
from app.benchmarks.evaluator import AcademicBenchmarkEvaluator, BenchmarkSuiteResult

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@router.get("/experiments", response_model=BenchmarkSuiteResult)
def run_benchmark_experiments() -> BenchmarkSuiteResult:
    """Executes the academic benchmark suite evaluating RQ1, RQ2, and RQ3."""
    evaluator = AcademicBenchmarkEvaluator(BENCHMARK_CORPUS)
    return evaluator.evaluate_all()


@router.get("/corpus", response_model=list[dict[str, Any]])
def get_benchmark_corpus() -> list[dict[str, Any]]:
    """Retrieves ground-truth labeled benchmark samples."""
    return [
        {
            "sample_id": s.sample_id,
            "file_path": s.file_path,
            "sloc": s.sloc,
            "expected_defect": s.expected_defect,
            "true_defects_count": s.true_defects_count,
            "benign_alerts_count": s.benign_alerts_count,
            "ground_truth_findings": [
                {
                    "rule_id": f.rule_id,
                    "category": f.category,
                    "severity": f.severity,
                    "line": f.line,
                    "is_genuine_defect": f.is_genuine_defect,
                    "is_test_fixture_false_positive": f.is_test_fixture_false_positive,
                }
                for f in s.ground_truth_findings
            ],
        }
        for s in BENCHMARK_CORPUS
    ]
