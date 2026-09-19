"""SQALE-Inspired Technical Debt Estimator."""

from dataclasses import dataclass

from app.domain.enums import FindingCategory, FindingSeverity
from app.infrastructure.db.models.issue import Issue


@dataclass
class DebtBreakdown:
    total_minutes: int
    total_hours: float
    by_category: dict[str, int]
    by_severity: dict[str, int]


# Standard remediation effort matrix (in minutes)
REMEDIATION_COST_MATRIX: dict[tuple[FindingCategory, FindingSeverity], int] = {
    (FindingCategory.SECURITY, FindingSeverity.CRITICAL): 180,
    (FindingCategory.SECURITY, FindingSeverity.HIGH): 90,
    (FindingCategory.SECURITY, FindingSeverity.MEDIUM): 45,
    (FindingCategory.SECURITY, FindingSeverity.LOW): 15,
    (FindingCategory.ARCHITECTURE, FindingSeverity.HIGH): 120,
    (FindingCategory.ARCHITECTURE, FindingSeverity.MEDIUM): 60,
    (FindingCategory.MAINTAINABILITY, FindingSeverity.HIGH): 60,
    (FindingCategory.MAINTAINABILITY, FindingSeverity.MEDIUM): 30,
    (FindingCategory.MAINTAINABILITY, FindingSeverity.LOW): 15,
    (FindingCategory.CODE_SMELL, FindingSeverity.HIGH): 45,
    (FindingCategory.CODE_SMELL, FindingSeverity.MEDIUM): 30,
    (FindingCategory.CODE_SMELL, FindingSeverity.LOW): 15,
    (FindingCategory.CODE_SMELL, FindingSeverity.INFO): 5,
}


class TechnicalDebtEstimator:
    @staticmethod
    def estimate_issue_effort(issue: Issue) -> int:
        """Returns the estimated remediation time in minutes for an issue."""
        key = (issue.category, issue.severity)
        return REMEDIATION_COST_MATRIX.get(key, 30)

    @classmethod
    def calculate_total_debt(cls, issues: list[Issue]) -> DebtBreakdown:
        total = 0
        by_cat: dict[str, int] = {}
        by_sev: dict[str, int] = {}

        for issue in issues:
            effort = cls.estimate_issue_effort(issue)
            total += effort

            cat_name = issue.category.value
            by_cat[cat_name] = by_cat.get(cat_name, 0) + effort

            sev_name = issue.severity.value
            by_sev[sev_name] = by_sev.get(sev_name, 0) + effort

        return DebtBreakdown(
            total_minutes=total,
            total_hours=round(total / 60.0, 1),
            by_category=by_cat,
            by_severity=by_sev,
        )
