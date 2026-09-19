"""Unit tests for Academic Benchmark Evaluation Engine (RQ1, RQ2, RQ3)."""

from app.benchmarks.corpus import BENCHMARK_CORPUS
from app.benchmarks.evaluator import AcademicBenchmarkEvaluator


def test_academic_benchmark_evaluation_suite():
    evaluator = AcademicBenchmarkEvaluator(BENCHMARK_CORPUS)
    result = evaluator.evaluate_all()

    # 1. General Corpus Integrity
    assert result.total_samples >= 5
    assert result.total_sloc > 100
    assert result.total_ground_truth_defects >= 5

    # 2. RQ1 Verification (Detection Accuracy)
    rq1 = result.rq1
    hybrid_method = next(m for m in rq1.methods if "Hybrid" in m.method_name)
    static_method = next(m for m in rq1.methods if "Static" in m.method_name)
    llm_method = next(m for m in rq1.methods if "LLM" in m.method_name)

    assert hybrid_method.f1_score >= 0.85
    assert hybrid_method.f1_score >= static_method.f1_score
    assert hybrid_method.f1_score >= llm_method.f1_score
    assert hybrid_method.precision > static_method.precision
    assert rq1.f1_improvement_over_static > 0.0
    assert rq1.f1_improvement_over_llm > 0.0

    # 3. RQ2 Verification (Defect Ranking & Pareto Concentration)
    rq2 = result.rq2
    assert rq2.recall_at_top_20_pct_loc >= 70.0
    assert rq2.efficiency_multiplier >= 3.0
    assert len(rq2.pareto_curve) >= 4

    # 4. RQ3 Verification (False-Positive Suppression Rate)
    rq3 = result.rq3
    assert rq3.false_positive_suppression_rate >= 30.0
    assert rq3.genuine_vulnerabilities_total >= 2
    assert rq3.genuine_retention_rate == 100.0
