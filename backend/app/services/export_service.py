"""Report Export Engine: SARIF v2.1.0, Markdown PR Summary, and Printable HTML Exporter."""

import html

from app.api.v1.schemas.export import (
    SarifArtifactChange,
    SarifArtifactLocation,
    SarifFix,
    SarifLocation,
    SarifLog,
    SarifMessage,
    SarifPhysicalLocation,
    SarifRegion,
    SarifReplacement,
    SarifReportingDescriptor,
    SarifResult,
    SarifRun,
    SarifTool,
    SarifToolComponent,
)
from app.domain.enums import CommentStatus, FindingSeverity
from app.infrastructure.db.models.analysis_report import AnalysisReport
from app.infrastructure.db.models.defect_prediction import DefectPrediction
from app.infrastructure.db.models.issue import Issue
from app.infrastructure.db.models.review_comment import ReviewComment
from app.services.scoring_service import QualityScorecard, ScoringService


class SarifExporter:
    """Builder for OASIS SARIF v2.1.0 log files."""

    @classmethod
    def export(cls, report: AnalysisReport, scorecard: QualityScorecard | None = None) -> SarifLog:
        """Serializes static findings, ML predictions, and review suggestions into OASIS SARIF v2.1.0."""
        rules_map: dict[str, SarifReportingDescriptor] = {}
        results: list[SarifResult] = []

        # 1. Map Static Analysis Issues
        for issue in report.issues:
            cls._map_issue(issue, rules_map, results)

        # 2. Map ML Defect Predictions (High and Critical risk tiers)
        for dp in report.defect_predictions:
            cls._map_defect_prediction(dp, rules_map, results)

        # 3. Map Confirmed Hybrid AI Review Comments & Suggested Patches
        for rev in report.review_comments or []:
            cls._map_review_comment(rev, rules_map, results)

        tool = SarifTool(
            driver=SarifToolComponent(
                name="CodeSentinel AI",
                version="1.0.0",
                rules=list(rules_map.values()),
            )
        )

        return SarifLog(runs=[SarifRun(tool=tool, results=results)])

    @staticmethod
    def _map_issue(
        issue: Issue,
        rules_map: dict[str, SarifReportingDescriptor],
        results: list[SarifResult],
    ) -> None:
        rule_id = issue.rule_id or f"RULE-{issue.category}"
        if rule_id not in rules_map:
            rules_map[rule_id] = SarifReportingDescriptor(
                id=rule_id,
                name=issue.title,
                shortDescription=SarifMessage(text=issue.title),
                fullDescription=SarifMessage(text=issue.description or issue.title),
                helpUri=f"https://cwe.mitre.org/data/definitions/{issue.cwe_id.replace('CWE-', '')}.html"
                if issue.cwe_id
                else None,
                defaultConfiguration={
                    "level": "error"
                    if issue.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)
                    else "warning"
                },
            )

        level = (
            "error"
            if issue.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)
            else ("warning" if issue.severity == FindingSeverity.MEDIUM else "note")
        )

        results.append(
            SarifResult(
                ruleId=rule_id,
                level=level,  # type: ignore[arg-type]
                message=SarifMessage(text=f"[{issue.severity}] {issue.title}: {issue.description}"),
                locations=[
                    SarifLocation(
                        physicalLocation=SarifPhysicalLocation(
                            artifactLocation=SarifArtifactLocation(uri=issue.file_path),
                            region=SarifRegion(
                                startLine=max(1, issue.line_start),
                                endLine=max(issue.line_start, issue.line_end),
                            ),
                        )
                    )
                ],
            )
        )

    @staticmethod
    def _map_defect_prediction(
        dp: DefectPrediction,
        rules_map: dict[str, SarifReportingDescriptor],
        results: list[SarifResult],
    ) -> None:
        prob = float(dp.defect_probability or 0.0)
        tier = str(dp.risk_tier)
        if tier not in ("CRITICAL", "HIGH") and prob < 0.65:
            return

        rule_id = "ML-DEFECT-PROBABILITY-HIGH"
        if rule_id not in rules_map:
            rules_map[rule_id] = SarifReportingDescriptor(
                id=rule_id,
                name="High Defect Probability",
                shortDescription=SarifMessage(text="High Defect Probability Predicted by ML"),
                fullDescription=SarifMessage(
                    text="The module has high complexity and change churn, indicating high likelihood of containing software defects."
                ),
                defaultConfiguration={"level": "warning"},
            )

        results.append(
            SarifResult(
                ruleId=rule_id,
                level="error" if tier == "CRITICAL" else "warning",
                message=SarifMessage(
                    text=f"TreeSHAP Defect Predictor: {prob:.0%} defect probability (Risk Tier: {tier})."
                ),
                locations=[
                    SarifLocation(
                        physicalLocation=SarifPhysicalLocation(
                            artifactLocation=SarifArtifactLocation(uri=dp.file_path),
                            region=SarifRegion(startLine=1, endLine=1),
                        )
                    )
                ],
            )
        )

    @staticmethod
    def _map_review_comment(
        rev: ReviewComment,
        rules_map: dict[str, SarifReportingDescriptor],
        results: list[SarifResult],
    ) -> None:
        if rev.status == CommentStatus.DISMISSED or "FALSE_POSITIVE" in (rev.comment or ""):
            return

        rule_id = "AI-HYBRID-CODE-REVIEW"
        if rule_id not in rules_map:
            rules_map[rule_id] = SarifReportingDescriptor(
                id=rule_id,
                name="AI Code Review Finding",
                shortDescription=SarifMessage(text="Triangulated AI Code Review Finding"),
                fullDescription=SarifMessage(
                    text="Identified by hybrid AST, ML risk, and LLM semantic triangulation."
                ),
                defaultConfiguration={"level": "warning"},
            )

        fixes = None
        if rev.suggested_patch:
            fixes = [
                SarifFix(
                    description=SarifMessage(text="Suggested code patch from hybrid review"),
                    artifactChanges=[
                        SarifArtifactChange(
                            artifactLocation=SarifArtifactLocation(uri=rev.file_path),
                            replacements=[
                                SarifReplacement(
                                    deletedRegion=SarifRegion(
                                        startLine=max(1, rev.line_number),
                                        endLine=max(1, rev.line_number),
                                    ),
                                    insertedContent=SarifMessage(text=rev.suggested_patch),
                                )
                            ],
                        )
                    ],
                )
            ]

        results.append(
            SarifResult(
                ruleId=rule_id,
                level="warning",
                message=SarifMessage(text=rev.comment[:500]),
                locations=[
                    SarifLocation(
                        physicalLocation=SarifPhysicalLocation(
                            artifactLocation=SarifArtifactLocation(uri=rev.file_path),
                            region=SarifRegion(
                                startLine=max(1, rev.line_number),
                                endLine=max(1, rev.line_number),
                            ),
                        )
                    )
                ],
                fixes=fixes,
            )
        )


class MarkdownSummaryExporter:
    """Builder for GitHub PR Markdown summaries."""

    @classmethod
    def export(
        cls,
        report: AnalysisReport,
        scorecard: QualityScorecard | None = None,
        repo_name: str = "Repository",
    ) -> str:
        sc = scorecard or ScoringService.calculate_scores(
            file_metrics=report.file_metrics,
            issues=report.issues,
            reviews=report.review_comments,
            defect_predictions=report.defect_predictions,
        )

        grade_badge = f"**Grade {sc.grade}** (`{sc.overall_score:.1f} / 100`)"

        lines = [
            f"# 🛡️ Software Quality Analysis: {repo_name}",
            "",
            f"**Overall Quality Score:** {grade_badge} &nbsp;|&nbsp; **Technical Debt:** `{sc.technical_debt_minutes}` mins",
            "",
            "### 📊 Multi-Pillar Quality Breakdown",
            "",
            "| Quality Pillar | Score | Weight | Grade | Status |",
            "| :--- | :---: | :---: | :---: | :--- |",
        ]

        for p in sc.pillars:
            lines.append(
                f"| **{p['name']}** | {p['score']:.1f} / 100 | {int(p['weight']*100)}% | `{p['grade']}` | {p['summary']} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "### 🚀 Prioritized Actionable Roadmap",
            "",
        ])

        if sc.recommendations:
            for rec in sc.recommendations:
                lines.append(
                    f"- **[Rank #{rec['rank']}] {rec['title']}** (+{rec['potential_score_impact']} pts | ~{rec['effort_minutes']} mins)"
                )
                lines.append(f"  *{rec['description']}*")
        else:
            lines.append("- *No critical refactoring required. Codebase meets quality thresholds.*")

        if sc.false_positives_suppressed > 0:
            lines.extend([
                "",
                f"> 💡 **Triangulation Engine Note:** Suppressed `{sc.false_positives_suppressed}` false alarms on non-production test fixtures to prevent alert fatigue.",
            ])

        lines.extend([
            "",
            "---",
            "*Report generated automatically by [CodeSentinel AI](https://github.com/farazrasul0-cmd/CodeSentinel-AI).* "
            "Ingest SARIF log for detailed GitHub Code Scanning annotations.",
        ])

        return "\n".join(lines)


class HtmlReportExporter:
    """Builder for standalone printable executive HTML reports."""

    @classmethod
    def export(
        cls,
        report: AnalysisReport,
        scorecard: QualityScorecard | None = None,
        repo_name: str = "Repository",
    ) -> str:
        sc = scorecard or ScoringService.calculate_scores(
            file_metrics=report.file_metrics,
            issues=report.issues,
            reviews=report.review_comments,
            defect_predictions=report.defect_predictions,
        )

        title = html.escape(repo_name)
        grade = html.escape(sc.grade)
        overall = sc.overall_score

        pillars_html = "".join(
            f"""
            <div class="card">
                <div class="card-header">
                    <span class="pillar-title">{html.escape(p['name'])}</span>
                    <span class="grade-badge grade-{p['grade']}">{p['grade']}</span>
                </div>
                <div class="score-large">{p['score']:.1f}<span class="score-max">/100</span></div>
                <div class="score-sub">Weight: {int(p['weight']*100)}% ({p['weighted_contribution']:.1f} pts)</div>
                <div class="summary-text">{html.escape(p['summary'])}</div>
            </div>
            """
            for p in sc.pillars
        )

        recs_html = "".join(
            f"""
            <div class="rec-card">
                <div class="rec-badge">Rank #{r['rank']} &bull; +{r['potential_score_impact']} pts &bull; ~{r['effort_minutes']}m effort</div>
                <div class="rec-title">{html.escape(r['title'])}</div>
                <div class="rec-desc">{html.escape(r['description'])}</div>
            </div>
            """
            for r in sc.recommendations
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Software Quality Executive Report - {title}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #6366f1;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        @media print {{
            body {{ background: #ffffff !important; color: #0f172a !important; font-size: 12pt; }}
            .card, .rec-card {{ background: #f8fafc !important; border: 1px solid #cbd5e1 !important; page-break-inside: avoid; }}
            .no-print {{ display: none !important; }}
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background: var(--bg); color: var(--text-main); padding: 2rem; line-height: 1.5; }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--surface-border); padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        .title-h1 {{ font-size: 1.75rem; font-weight: 800; }}
        .meta-sub {{ font-size: 0.875rem; color: var(--text-muted); margin-top: 0.25rem; }}
        .hero-banner {{ display: flex; align-items: center; justify-content: space-between; background: var(--surface); border: 1px solid var(--surface-border); border-radius: 0.75rem; padding: 1.5rem 2rem; margin-bottom: 2rem; }}
        .overall-score {{ font-size: 3rem; font-weight: 900; color: var(--success); }}
        .grade-badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 0.375rem; font-weight: 800; font-size: 1rem; }}
        .grade-A {{ background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }}
        .grade-B {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }}
        .grade-C {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }}
        .grade-D {{ background: rgba(249, 115, 22, 0.2); color: #f97316; border: 1px solid #f97316; }}
        .grade-F {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }}
        .grid-4 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: var(--surface); border: 1px solid var(--surface-border); border-radius: 0.5rem; padding: 1.25rem; }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }}
        .pillar-title {{ font-weight: 700; font-size: 0.95rem; }}
        .score-large {{ font-size: 1.8rem; font-weight: 800; color: #fff; }}
        .score-max {{ font-size: 0.85rem; color: var(--text-muted); font-weight: 400; }}
        .score-sub {{ font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem; }}
        .summary-text {{ font-size: 0.8rem; color: #cbd5e1; }}
        .rec-card {{ background: var(--surface); border: 1px solid var(--surface-border); border-radius: 0.5rem; padding: 1rem; margin-bottom: 0.75rem; }}
        .rec-badge {{ font-size: 0.75rem; color: var(--warning); font-weight: 600; text-transform: uppercase; margin-bottom: 0.25rem; }}
        .rec-title {{ font-size: 0.95rem; font-weight: 700; color: #fff; }}
        .rec-desc {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem; }}
        .btn-print {{ background: var(--primary); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 class="title-h1">Quality Assessment Report</h1>
                <p class="meta-sub">Repository: <strong>{title}</strong> &bull; Total SLOC: {report.total_lines_of_code} &bull; Tech Debt: {sc.technical_debt_minutes} mins</p>
            </div>
            <button class="btn-print no-print" onclick="window.print()">Print / Save PDF</button>
        </div>

        <div class="hero-banner">
            <div>
                <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.25rem;">Repository Quality Index (RQI)</div>
                <div class="overall-score">{overall:.1f} <span style="font-size: 1.25rem; color: var(--text-muted); font-weight: 400;">/ 100</span></div>
            </div>
            <div style="text-align: right;">
                <div class="grade-badge grade-{grade}" style="font-size: 2rem; padding: 0.5rem 1.5rem;">Grade {grade}</div>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">{sc.false_positives_suppressed} False Alarm(s) Suppressed</div>
            </div>
        </div>

        <h2 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem;">Multi-Pillar Scores</h2>
        <div class="grid-4">
            {pillars_html}
        </div>

        <h2 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem;">Prioritized Actionable Roadmap</h2>
        <div>
            {recs_html}
        </div>
    </div>
</body>
</html>
"""


class ExportService:
    """Standardized report export facade conforming to SARIF v2.1.0 and print standards."""

    @staticmethod
    def generate_sarif(
        report: AnalysisReport,
        scorecard: QualityScorecard | None = None,
    ) -> SarifLog:
        """Serializes static findings, ML predictions, and review suggestions into OASIS SARIF v2.1.0."""
        return SarifExporter.export(report, scorecard)

    @staticmethod
    def generate_markdown_summary(
        report: AnalysisReport,
        scorecard: QualityScorecard | None = None,
        repo_name: str = "Repository",
    ) -> str:
        """Produces a structured GitHub PR review comment in standard markdown."""
        return MarkdownSummaryExporter.export(report, scorecard, repo_name)

    @staticmethod
    def generate_printable_html(
        report: AnalysisReport,
        scorecard: QualityScorecard | None = None,
        repo_name: str = "Repository",
    ) -> str:
        """Generates self-contained, standalone printable HTML executive report."""
        return HtmlReportExporter.export(report, scorecard, repo_name)
