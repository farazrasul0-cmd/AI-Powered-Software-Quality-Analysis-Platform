"""Hybrid Triangulation Code Review Service.

Reconciles deterministic static analysis alerts (CWEs, smells) with
statistical ML defect risk (TreeSHAP) and LLM semantic reasoning
to eliminate false positives and produce actionable code reviews.
"""

from typing import Any

from app.api.v1.schemas.review import (
    FindingCategoryEnum,
    PullRequestReviewOutput,
    SeverityEnum,
)
from app.domain.enums import CommentStatus
from app.infrastructure.db.models.defect_prediction import DefectPrediction
from app.infrastructure.db.models.issue import Issue
from app.infrastructure.db.models.review_comment import ReviewComment
from app.infrastructure.llm.base import BaseLLMClient
from app.infrastructure.llm.factory import default_llm_reviewer
from app.infrastructure.rag.chunker import UnifiedSemanticChunker
from app.infrastructure.rag.retriever import ContextRetriever
from app.infrastructure.rag.vector_store import VectorStore, vector_store

SEVERITY_WEIGHTS: dict[SeverityEnum, float] = {
    SeverityEnum.CRITICAL: 1.0,
    SeverityEnum.MAJOR: 0.7,
    SeverityEnum.MINOR: 0.4,
    SeverityEnum.INFO: 0.1,
}


def calculate_rank_score(severity: SeverityEnum, defect_prob: float, confidence: float) -> float:
    """Computes composite prioritization score for code review findings.

    Formula: RankScore = 0.45 * SevWeight + 0.30 * P(defect) + 0.25 * Confidence
    """
    w_sev = SEVERITY_WEIGHTS.get(severity, 0.4)
    p_def = max(0.0, min(1.0, defect_prob))
    conf = max(0.0, min(1.0, confidence))
    return round((0.45 * w_sev) + (0.30 * p_def) + (0.25 * conf), 4)


class HybridReviewService:
    """Orchestrates hybrid code review combining static AST, ML defect risk, and LLMs."""

    def __init__(
        self,
        llm_client: BaseLLMClient | None = None,
        store: VectorStore | None = None,
    ) -> None:
        self.llm = llm_client or default_llm_reviewer
        self.store = store or vector_store
        self.retriever = ContextRetriever(self.store)

    async def review_file(
        self,
        repository_id: str,
        file_path: str,
        code_content: str,
        static_issues: list[Issue] | list[dict[str, Any]],
        defect_prediction: DefectPrediction | dict[str, Any] | None = None,
        report_id: str = "",
    ) -> tuple[list[ReviewComment], PullRequestReviewOutput]:
        """Performs hybrid code review on a single file."""
        # 1. Extract semantic chunks and index into vector store
        chunks = UnifiedSemanticChunker.chunk_file(file_path, code_content)
        await self.store.index_chunks(repository_id, chunks)

        # 2. Gather RAG context from primary chunk
        primary_chunk = chunks[0] if chunks else None
        rag_context = ""
        if primary_chunk:
            related_chunks = await self.retriever.retrieve_context_for_chunk(
                repository_id, primary_chunk, limit=3
            )
            rag_context = self.retriever.format_context_for_prompt(related_chunks)

        # 3. Extract defect risk
        defect_prob = 0.10
        risk_tier = "LOW"
        shap_factors: dict[str, Any] = {}
        if defect_prediction:
            defect_prob = float(
                getattr(defect_prediction, "defect_probability", 0.10)
                if hasattr(defect_prediction, "defect_probability")
                else defect_prediction.get("defect_probability", 0.10)
            )
            risk_tier = str(
                getattr(defect_prediction, "risk_tier", "LOW")
                if hasattr(defect_prediction, "risk_tier")
                else defect_prediction.get("risk_tier", "LOW")
            )
            shap_factors = (
                getattr(defect_prediction, "shap_factors", {})
                if hasattr(defect_prediction, "shap_factors")
                else defect_prediction.get("shap_factors", {})
            ) or {}

        # 4. Normalize static issues
        formatted_issues: list[dict[str, Any]] = []
        for iss in static_issues:
            if isinstance(iss, Issue):
                formatted_issues.append({
                    "rule_id": iss.rule_id,
                    "title": iss.title,
                    "category": str(iss.category),
                    "severity": str(iss.severity),
                    "line_start": iss.line_start,
                    "line_end": iss.line_end,
                    "description": iss.description,
                })
            elif isinstance(iss, dict):
                formatted_issues.append(iss)

        # 5. Assemble Context Pack
        context_pack = {
            "repository_id": repository_id,
            "file_path": file_path,
            "code_content": code_content,
            "static_issues": formatted_issues,
            "defect_probability": defect_prob,
            "risk_tier": risk_tier,
            "shap_factors": shap_factors,
            "rag_context": rag_context,
        }

        # 6. Execute LLM Review with Hybrid Triangulation
        review_output = await self.llm.review_code(context_pack)

        # 7. Convert confirmed findings into persistent ReviewComment models
        comments: list[ReviewComment] = []
        for finding in review_output.findings:
            # Skip suppressed false positive overrides
            if finding.category == FindingCategoryEnum.FALSE_POSITIVE_OVERRIDE:
                continue

            rank_score = calculate_rank_score(
                finding.severity, defect_prob, finding.confidence_score
            )

            # Build rich comment body
            comment_body = (
                f"**[{finding.severity}] {finding.title}**\n\n"
                f"{finding.issue_description}\n\n"
                f"💡 **Remediation:** {finding.remediation_advice}\n\n"
                f"*Triangulation Status:* `{finding.triangulation_status}` | "
                f"*Confidence:* {int(finding.confidence_score * 100)}% | "
                f"*Priority Score:* {rank_score}"
            )

            suggested_patch = (
                finding.suggested_fix.unified_diff if finding.suggested_fix else None
            )

            comment = ReviewComment(
                report_id=report_id,
                file_path=finding.file_path,
                line_number=finding.line_start,
                comment=comment_body,
                suggested_patch=suggested_patch,
                status=CommentStatus.PENDING,
            )
            comments.append(comment)

        return comments, review_output


# Global Service Instance
hybrid_review_service = HybridReviewService()
