"""Deterministic Local LLM Reviewer for testing, CI/CD, and zero-key demonstrations.

Implements hybrid triangulation logic (false positive suppression, defect risk escalation,
and suggested patch synthesis) without requiring external API access or credentials.
"""

from typing import Any

from app.api.v1.schemas.review import (
    CodeReviewFinding,
    FindingCategoryEnum,
    PullRequestReviewOutput,
    SeverityEnum,
    SuggestedDiff,
    TriangulationStatusEnum,
)
from app.infrastructure.llm.base import BaseLLMClient


class MockLLMReviewer(BaseLLMClient):
    """Deterministic, rule-and-heuristic-guided LLM emulator for code reviews."""

    async def review_code(self, context_pack: dict[str, Any]) -> PullRequestReviewOutput:
        file_path = context_pack.get("file_path", "unknown")
        code = context_pack.get("code_content", "")
        static_issues = context_pack.get("static_issues", [])
        defect_prob = float(context_pack.get("defect_probability", 0.10))

        findings: list[CodeReviewFinding] = []

        # 1. Triangulate Static Analysis Findings
        for issue in static_issues:
            rule_id = issue.get("rule_id", "")
            line = int(issue.get("line_start", 1))

            # False Positive Filter: Test file secrets or mock fixtures
            is_test_file = any(t in file_path.lower() for t in ["test", "fixture", "mock", "sample"])
            if rule_id in ("SEC-HARDCODED-SECRET", "SEC-PWD-HARDCODED") and is_test_file:
                findings.append(
                    CodeReviewFinding(
                        title=f"Suppressed False Alarm: Test Credential in {file_path}",
                        category=FindingCategoryEnum.FALSE_POSITIVE_OVERRIDE,
                        severity=SeverityEnum.INFO,
                        confidence_score=0.95,
                        file_path=file_path,
                        line_start=line,
                        line_end=line,
                        ast_symbol="test_fixture",
                        issue_description="Static scanner flagged hardcoded string assignment in test context.",
                        remediation_advice="No action required. Credential is a simulated test fixture never deployed to production.",
                        triangulation_status=TriangulationStatusEnum.FALSE_POSITIVE_SUPPRESSED,
                        triangulation_rationale="Evaluated enclosing scope: file is within test directory; suppressed to eliminate alert fatigue.",
                    )
                )
            elif rule_id in ("SEC-SQL-INJECTION", "SEC-SQLI"):
                # Confirmed Vulnerability with Actionable Fix
                findings.append(
                    CodeReviewFinding(
                        title=f"SQL Injection via Unsanitized Formatting in {file_path}",
                        category=FindingCategoryEnum.SECURITY_VULNERABILITY,
                        severity=SeverityEnum.CRITICAL,
                        confidence_score=0.98,
                        file_path=file_path,
                        line_start=line,
                        line_end=line + 2,
                        ast_symbol="query_executor",
                        issue_description="Dynamic string formatting passes untrusted inputs directly into raw SQL query execution.",
                        remediation_advice="Use parameterized queries with bind variables or an ORM query builder.",
                        suggested_fix=SuggestedDiff(
                            file_path=file_path,
                            line_start=line,
                            line_end=line + 2,
                            original_code='cursor.execute(f"SELECT * FROM users WHERE username = \'{user_id}\'")',
                            replacement_code='cursor.execute("SELECT * FROM users WHERE username = %s", (user_id,))',
                            unified_diff=(
                                '--- a/' + file_path + '\n+++ b/' + file_path + '\n'
                                '@@ -' + str(line) + ',1 +' + str(line) + ',1 @@\n'
                                '-cursor.execute(f"SELECT * FROM users WHERE username = \'{user_id}\'")\n'
                                '+cursor.execute("SELECT * FROM users WHERE username = %s", (user_id,))'
                            ),
                            explanation="Switches formatted string interpolation to parameterized binding, neutralizing CWE-89 injection.",
                        ),
                        triangulation_status=TriangulationStatusEnum.CONFIRMED,
                        triangulation_rationale="Static scanner alert confirmed by semantic AST taint analysis; high risk of exploitation.",
                    )
                )
            elif rule_id == "SEC-DESERIALIZATION-PICKLE":
                findings.append(
                    CodeReviewFinding(
                        title="Unsafe Deserialization via Pickle/Yaml",
                        category=FindingCategoryEnum.SECURITY_VULNERABILITY,
                        severity=SeverityEnum.CRITICAL,
                        confidence_score=0.94,
                        file_path=file_path,
                        line_start=line,
                        line_end=line,
                        issue_description="Arbitrary code execution risk through unauthenticated deserialization.",
                        remediation_advice="Use safe serialization formats like JSON, or enforce yaml.safe_load().",
                        suggested_fix=SuggestedDiff(
                            file_path=file_path,
                            line_start=line,
                            line_end=line,
                            original_code="yaml.load(payload)",
                            replacement_code="yaml.safe_load(payload)",
                            unified_diff="@@ -1,1 +1,1 @@\n-yaml.load(payload)\n+yaml.safe_load(payload)",
                            explanation="Enforces SafeLoader to prevent arbitrary Python object instantiation.",
                        ),
                        triangulation_status=TriangulationStatusEnum.CONFIRMED,
                        triangulation_rationale="Confirmed CWE-502 vulnerability across API endpoint boundary.",
                    )
                )

        # 2. Defect Risk Escalation (Phase 4 Triangulation)
        if defect_prob >= 0.70 and not any(f.severity == SeverityEnum.CRITICAL for f in findings):
            findings.append(
                CodeReviewFinding(
                    title=f"High Defect Risk: Complex Control Flow & Churn in {file_path}",
                    category=FindingCategoryEnum.LOGIC_BUG,
                    severity=SeverityEnum.MAJOR,
                    confidence_score=0.88,
                    file_path=file_path,
                    line_start=1,
                    line_end=min(40, len(code.splitlines()) or 1),
                    ast_symbol="core_module",
                    issue_description=(
                        f"Phase 4 ML predictor flagged module with {int(defect_prob * 100)}% defect probability. "
                        "High cyclomatic complexity and elevated Halstead effort create dense cognitive friction prone to regression."
                    ),
                    remediation_advice="Decompose nested conditionals into early-return guard clauses or extract helper strategy classes.",
                    suggested_fix=SuggestedDiff(
                        file_path=file_path,
                        line_start=1,
                        line_end=10,
                        original_code="# Nested monolithic branching block",
                        replacement_code="# Decomposed guard clauses with early returns",
                        unified_diff="@@ -1,1 +1,1 @@\n-# Monolithic block\n+# Refactored guard clauses",
                        explanation="Flattens nesting to reduce cyclomatic complexity and risk probability.",
                    ),
                    triangulation_status=TriangulationStatusEnum.NEW_SEMANTIC_FINDING,
                    triangulation_rationale="Escalated by TreeSHAP risk profile despite clean static baseline.",
                )
            )

        # 3. Formulate Overall Assessment
        active_findings = [f for f in findings if f.category != FindingCategoryEnum.FALSE_POSITIVE_OVERRIDE]
        if any(f.severity == SeverityEnum.CRITICAL for f in active_findings) or defect_prob >= 0.75:
            overall_assessment = "Critical security or defect risks identified requiring mandatory developer remediation."
            risk_level = "CRITICAL"
        elif active_findings:
            overall_assessment = "Code has actionable maintainability or logic concerns that should be addressed."
            risk_level = "HIGH" if defect_prob >= 0.50 else "MODERATE"
        else:
            overall_assessment = "Module exhibits sound architectural structure, low defect risk, and clean static compliance."
            risk_level = "LOW"

        summary = (
            f"Automated Code Review for {file_path}: {len(active_findings)} active finding(s), "
            f"{len(findings) - len(active_findings)} suppressed false alarm(s). Overall Risk: {risk_level}."
        )

        return PullRequestReviewOutput(
            summary=summary,
            overall_quality_assessment=overall_assessment,
            predicted_risk_level=risk_level,
            findings=findings,
        )
