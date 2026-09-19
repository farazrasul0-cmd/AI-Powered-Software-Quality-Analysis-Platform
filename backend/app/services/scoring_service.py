"""Composite Multi-Dimensional Software Quality Scoring Algorithm.

Calculates Maintainability (30%), Security (35%), Architecture (20%), and Testing (15%)
pillar scores, produces letter grades (A-F), radar coordinates, and prioritized recommendations.
Includes false-positive suppression protection ensuring benign alerts do not penalize security score.
"""

from dataclasses import dataclass, field
from typing import Any

from app.api.v1.schemas.review import CodeReviewFinding, FindingCategoryEnum
from app.domain.enums import CommentStatus, FindingCategory, FindingSeverity
from app.infrastructure.db.models.file_metric import FileMetric
from app.infrastructure.db.models.issue import Issue
from app.infrastructure.db.models.review_comment import ReviewComment


@dataclass
class QualityScorecard:
    overall_score: float
    maintainability_score: float
    security_score: float
    testing_score: float
    architecture_score: float
    technical_debt_minutes: int
    grade: str = "B"
    radar_data: list[dict[str, Any]] = field(default_factory=list)
    pillars: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    false_positives_suppressed: int = 0


class ScoringService:
    """Multi-Dimensional Quality Scoring Engine implementing academic and industry formulas."""

    @staticmethod
    def calculate_scores(
        file_metrics: list[FileMetric],
        issues: list[Issue],
        reviews: list[CodeReviewFinding] | list[ReviewComment] | list[dict[str, Any]] | None = None,
        circular_dependencies: list[list[str]] | None = None,
        defect_predictions: list[Any] | None = None,
    ) -> QualityScorecard:
        """Calculates 4 pillar scores (0-100), composite RQI (0-100), grade, and recommendations."""
        total_files = len(file_metrics)

        # ---------------------------------------------------------------------
        # 1. False-Positive Suppression Tracking
        # ---------------------------------------------------------------------
        suppressed_rules: set[str] = set()
        suppressed_locations: set[tuple[str, int]] = set()
        false_positives_count = 0

        if reviews:
            for rev in reviews:
                if isinstance(rev, dict):
                    cat = rev.get("category")
                    fp_file = rev.get("file_path", "")
                    fp_line = rev.get("line_start", 0)
                    rule_id = rev.get("rule_id", "")
                elif isinstance(rev, ReviewComment):
                    fp_file = rev.file_path
                    fp_line = rev.line_number
                    rule_id = ""
                    cat = (
                        FindingCategoryEnum.FALSE_POSITIVE_OVERRIDE
                        if (
                            "FALSE_POSITIVE" in (rev.comment or "")
                            or rev.status == CommentStatus.DISMISSED
                        )
                        else None
                    )
                else:
                    cat = getattr(rev, "category", None)
                    fp_file = getattr(rev, "file_path", "")
                    fp_line = getattr(rev, "line_start", 0)
                    rule_id = getattr(rev, "rule_id", "")

                if cat == FindingCategoryEnum.FALSE_POSITIVE_OVERRIDE or cat == "FALSE_POSITIVE_OVERRIDE":
                    false_positives_count += 1
                    if rule_id:
                        suppressed_rules.add(rule_id)
                    if fp_file and fp_line:
                        suppressed_locations.add((fp_file, fp_line))

        # ---------------------------------------------------------------------
        # 2. Maintainability Pillar Score (S_maint in [0, 100])
        # Formula: S_maint = max(0, min(100, avg_MI - P_CC - P_Cognitive - P_Halstead))
        # ---------------------------------------------------------------------
        if total_files > 0:
            avg_mi = sum((m.maintainability_index or 100.0) for m in file_metrics) / total_files

            # P_CC: McCabe Cyclomatic Complexity penalty for CC > 10
            excess_cc = sum(max(0, (m.cyclomatic_complexity or 0) - 10) for m in file_metrics)
            p_cc = min(25.0, 2.5 * (excess_cc / total_files))

            # P_Cognitive: Cognitive Complexity nesting penalty for Cog > 12
            excess_cog = sum(max(0, (m.cognitive_complexity or 0) - 12) for m in file_metrics)
            p_cog = min(15.0, 1.5 * (excess_cog / total_files))

            # P_Halstead: Halstead effort penalty
            total_effort = 0.0
            for m in file_metrics:
                hm = m.halstead_metrics or {}
                total_effort += float(hm.get("effort", 0.0) or 0.0)
            p_halstead = min(10.0, total_effort / (1_000_000.0 * total_files))

            maintainability = max(0.0, min(100.0, avg_mi - p_cc - p_cog - p_halstead))
        else:
            maintainability = 85.0

        # ---------------------------------------------------------------------
        # 3. Security Pillar Score (S_sec in [0, 100])
        # Formula: S_sec = max(0, 100 - sum(w_j for validated issues))
        # ---------------------------------------------------------------------
        security = 100.0
        sec_issues = [i for i in issues if i.category == FindingCategory.SECURITY]
        validated_sec_issues: list[Issue] = []

        for issue in sec_issues:
            # Check if this issue was overridden/suppressed by Phase 5 Hybrid Triangulation
            is_suppressed = (
                (issue.rule_id and issue.rule_id in suppressed_rules)
                or ((issue.file_path, issue.line_start) in suppressed_locations)
            )
            if is_suppressed:
                continue

            validated_sec_issues.append(issue)
            if issue.severity == FindingSeverity.CRITICAL:
                security -= 25.0
            elif issue.severity == FindingSeverity.HIGH:
                security -= 15.0
            elif issue.severity == FindingSeverity.MEDIUM:
                security -= 8.0
            elif issue.severity == FindingSeverity.LOW:
                security -= 3.0

        security = max(0.0, security)

        # ---------------------------------------------------------------------
        # 4. Reliability & Architecture Pillar Score (S_arch in [0, 100])
        # Formula: S_arch = max(0, 100 - P_circular - P_coupling - P_defect_risk - P_smells)
        # ---------------------------------------------------------------------
        num_cycles = len(circular_dependencies) if circular_dependencies is not None else 0
        p_circular = 15.0 * num_cycles

        # High coupling modules (high fan-in/fan-out or method bloat)
        high_coupling_count = sum(
            1 for m in file_metrics if ((m.function_count or 0) > 20 or (m.class_count or 0) > 6)
        )
        p_coupling = min(25.0, 3.0 * high_coupling_count)

        # Defect risk penalty from Phase 4 ML Defect Prediction
        p_defect_risk = 0.0
        if defect_predictions and total_files > 0:
            probs: list[float] = []
            critical_risk_count = 0
            for dp in defect_predictions:
                p = float(getattr(dp, "defect_probability", 0.0) if hasattr(dp, "defect_probability") else dp.get("defect_probability", 0.0))
                tier = str(getattr(dp, "risk_tier", "LOW") if hasattr(dp, "risk_tier") else dp.get("risk_tier", "LOW"))
                probs.append(p)
                if tier == "CRITICAL" or p >= 0.70:
                    critical_risk_count += 1
            avg_prob = sum(probs) / len(probs) if probs else 0.0
            p_defect_risk = min(35.0, (30.0 * avg_prob) + (20.0 * (critical_risk_count / total_files)))

        # Architecture & Code smell issues penalty
        arch_issues = [
            i
            for i in issues
            if i.category in (FindingCategory.ARCHITECTURE, FindingCategory.CODE_SMELL)
        ]
        p_smells = 0.0
        for issue in arch_issues:
            if issue.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH):
                p_smells += 8.0
            elif issue.severity == FindingSeverity.MEDIUM:
                p_smells += 3.0
            else:
                p_smells += 1.0
        p_smells = min(30.0, p_smells)

        architecture = max(0.0, 100.0 - p_circular - p_coupling - p_defect_risk - p_smells)

        # ---------------------------------------------------------------------
        # 5. Testing Pillar Score (S_test in [0, 100])
        # Formula: S_test = min(100, max(20, 120 * (TestLOC / TotalLOC) + 40 * (TestFiles / TotalFiles)))
        # ---------------------------------------------------------------------
        test_files = [
            m for m in file_metrics if ("test" in m.file_path.lower() or "spec" in m.file_path.lower())
        ]
        if total_files > 0:
            total_loc = sum((m.sloc or 0) for m in file_metrics)
            test_loc = sum((m.sloc or 0) for m in test_files)
            if total_loc > 0 and len(test_files) > 0:
                loc_ratio = test_loc / total_loc
                file_ratio = len(test_files) / total_files
                testing = min(100.0, max(20.0, (120.0 * loc_ratio) + (40.0 * file_ratio)))
            elif len(test_files) > 0:
                testing = min(100.0, max(30.0, (len(test_files) / total_files) * 300.0))
            else:
                # No test files detected
                testing = 25.0
        else:
            testing = 75.0

        # ---------------------------------------------------------------------
        # 6. Technical Debt calculation (SQALE estimated minutes to remediate)
        # ---------------------------------------------------------------------
        debt_minutes = 0
        for issue in issues:
            # Skip suppressed issues from technical debt penalty
            if (
                (issue.rule_id and issue.rule_id in suppressed_rules)
                or ((issue.file_path, issue.line_start) in suppressed_locations)
            ):
                continue

            if issue.severity == FindingSeverity.CRITICAL:
                debt_minutes += 180
            elif issue.severity == FindingSeverity.HIGH:
                debt_minutes += 90
            elif issue.severity == FindingSeverity.MEDIUM:
                debt_minutes += 45
            else:
                debt_minutes += 15

        # ---------------------------------------------------------------------
        # 7. Composite Quality Index (RQI) and Letter Grade
        # Weights: Security (35%), Maintainability (30%), Architecture (20%), Testing (15%)
        # ---------------------------------------------------------------------
        overall = (
            (0.35 * security)
            + (0.30 * maintainability)
            + (0.20 * architecture)
            + (0.15 * testing)
        )

        grade = ScoringService._assign_grade(overall)

        # ---------------------------------------------------------------------
        # 8. Radar Chart Data & Pillar Breakdown
        # ---------------------------------------------------------------------
        radar_data = [
            {"axis": "Security", "value": round(security, 1), "benchmark_value": 85.0},
            {"axis": "Maintainability", "value": round(maintainability, 1), "benchmark_value": 78.0},
            {"axis": "Architecture", "value": round(architecture, 1), "benchmark_value": 75.0},
            {"axis": "Testing", "value": round(testing, 1), "benchmark_value": 70.0},
            {"axis": "Reliability", "value": round(min(100.0, (security + architecture) / 2.0), 1), "benchmark_value": 80.0},
        ]

        pillars = [
            {
                "name": "Security",
                "score": round(security, 1),
                "weight": 0.35,
                "weighted_contribution": round(0.35 * security, 1),
                "grade": ScoringService._assign_grade(security),
                "benchmark_percentile": ScoringService._calculate_percentile(security, 85.0),
                "summary": f"{len(validated_sec_issues)} active security findings; {false_positives_count} suppressed false alarms.",
            },
            {
                "name": "Maintainability",
                "score": round(maintainability, 1),
                "weight": 0.30,
                "weighted_contribution": round(0.30 * maintainability, 1),
                "grade": ScoringService._assign_grade(maintainability),
                "benchmark_percentile": ScoringService._calculate_percentile(maintainability, 78.0),
                "summary": f"Average MI {avg_mi:.1f} across {total_files} files with cognitive/Halstead penalties." if total_files else "No files analyzed.",
            },
            {
                "name": "Architecture",
                "score": round(architecture, 1),
                "weight": 0.20,
                "weighted_contribution": round(0.20 * architecture, 1),
                "grade": ScoringService._assign_grade(architecture),
                "benchmark_percentile": ScoringService._calculate_percentile(architecture, 75.0),
                "summary": f"{num_cycles} circular import cycles; {high_coupling_count} high-coupling modules.",
            },
            {
                "name": "Testing",
                "score": round(testing, 1),
                "weight": 0.15,
                "weighted_contribution": round(0.15 * testing, 1),
                "grade": ScoringService._assign_grade(testing),
                "benchmark_percentile": ScoringService._calculate_percentile(testing, 70.0),
                "summary": f"{len(test_files)} test files detected in repository.",
            },
        ]

        # ---------------------------------------------------------------------
        # 9. Prioritized Actionable Recommendations (Top 3)
        # ---------------------------------------------------------------------
        recommendations = ScoringService._generate_recommendations(
            validated_sec_issues=validated_sec_issues,
            file_metrics=file_metrics,
            circular_dependencies=circular_dependencies,
            defect_predictions=defect_predictions,
            testing_score=testing,
        )

        return QualityScorecard(
            overall_score=round(overall, 1),
            maintainability_score=round(maintainability, 1),
            security_score=round(security, 1),
            testing_score=round(testing, 1),
            architecture_score=round(architecture, 1),
            technical_debt_minutes=debt_minutes,
            grade=grade,
            radar_data=radar_data,
            pillars=pillars,
            recommendations=recommendations,
            false_positives_suppressed=false_positives_count,
        )

    @staticmethod
    def _assign_grade(score: float) -> str:
        """Translates numeric score [0-100] to standard letter grade."""
        if score >= 90.0:
            return "A"
        if score >= 80.0:
            return "B"
        if score >= 70.0:
            return "C"
        if score >= 60.0:
            return "D"
        return "F"

    @staticmethod
    def _calculate_percentile(score: float, baseline: float) -> float:
        """Calculates approximate percentile ranking against baseline distribution."""
        # Simple logistic approximation centered at baseline
        diff = score - baseline
        percentile = 50.0 + (diff * 1.5)
        return max(5.0, min(99.0, round(percentile, 1)))

    @staticmethod
    def _generate_recommendations(
        validated_sec_issues: list[Issue],
        file_metrics: list[FileMetric],
        circular_dependencies: list[list[str]] | None,
        defect_predictions: list[Any] | None,
        testing_score: float,
    ) -> list[dict[str, Any]]:
        """Synthesizes top 3 high-leverage refactoring actions."""
        candidates: list[dict[str, Any]] = []

        # Candidate A: Critical Security Issues
        crit_sec = [i for i in validated_sec_issues if i.severity == FindingSeverity.CRITICAL]
        high_sec = [i for i in validated_sec_issues if i.severity == FindingSeverity.HIGH]
        if crit_sec or high_sec:
            target_issue = crit_sec[0] if crit_sec else high_sec[0]
            count = len(crit_sec) + len(high_sec)
            candidates.append({
                "pillar": "Security",
                "title": f"Remediate {count} Critical/High Security Vulnerabilities",
                "description": f"Patch security exposure such as {target_issue.title} in {target_issue.file_path}:{target_issue.line_start}.",
                "effort_minutes": 120 * count,
                "potential_score_impact": round(min(25.0, count * 15.0), 1),
                "priority_weight": 100,
            })

        # Candidate B: High ML Defect Risk Files
        if defect_predictions:
            critical_files = [
                dp for dp in defect_predictions
                if (float(getattr(dp, "defect_probability", 0.0) if hasattr(dp, "defect_probability") else dp.get("defect_probability", 0.0)) >= 0.70)
            ]
            if critical_files:
                top_risk = critical_files[0]
                fp = getattr(top_risk, "file_path", "") if hasattr(top_risk, "file_path") else top_risk.get("file_path", "module")
                prob = float(getattr(top_risk, "defect_probability", 0.0) if hasattr(top_risk, "defect_probability") else top_risk.get("defect_probability", 0.0))
                candidates.append({
                    "pillar": "Architecture",
                    "title": f"Refactor Defect-Prone Module ({fp})",
                    "description": f"Targeted refactoring for module with {int(prob * 100)}% defect probability identified by TreeSHAP.",
                    "effort_minutes": 90,
                    "potential_score_impact": 12.0,
                    "priority_weight": 85,
                })

        # Candidate C: Circular Architectural Dependencies
        if circular_dependencies and len(circular_dependencies) > 0:
            cycle = circular_dependencies[0]
            cycle_str = " -> ".join(cycle[:3])
            candidates.append({
                "pillar": "Architecture",
                "title": f"Break {len(circular_dependencies)} Circular Import Cycle(s)",
                "description": f"Decouple cyclic dependency loop: {cycle_str}.",
                "effort_minutes": 150,
                "potential_score_impact": 15.0,
                "priority_weight": 80,
            })

        # Candidate D: High Cyclomatic Complexity
        complex_files = [m for m in file_metrics if (m.cyclomatic_complexity or 0) > 15]
        if complex_files:
            target_f = max(complex_files, key=lambda m: (m.cyclomatic_complexity or 0))
            candidates.append({
                "pillar": "Maintainability",
                "title": f"Decompose Complex Functions (CC={target_f.cyclomatic_complexity})",
                "description": f"Extract sub-routines in {target_f.file_path} to reduce cyclomatic and cognitive complexity.",
                "effort_minutes": 60,
                "potential_score_impact": 8.5,
                "priority_weight": 70,
            })

        # Candidate E: Testing Deficiency
        if testing_score < 60.0:
            candidates.append({
                "pillar": "Testing",
                "title": "Expand Unit & Integration Test Coverage",
                "description": "Increase test-to-code ratio to exceed 30% of total lines of code.",
                "effort_minutes": 180,
                "potential_score_impact": 14.0,
                "priority_weight": 65,
            })

        # Sort by priority_weight descending and take top 3
        candidates.sort(key=lambda x: x["priority_weight"], reverse=True)
        top_recs = candidates[:3]

        # Format with rank
        results: list[dict[str, Any]] = []
        for idx, rec in enumerate(top_recs, start=1):
            results.append({
                "rank": idx,
                "pillar": rec["pillar"],
                "title": rec["title"],
                "description": rec["description"],
                "effort_minutes": rec["effort_minutes"],
                "potential_score_impact": rec["potential_score_impact"],
            })

        return results
