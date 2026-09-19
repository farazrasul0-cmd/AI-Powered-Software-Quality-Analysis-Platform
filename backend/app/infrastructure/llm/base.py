"""Base abstract interface for LLM code reviewers."""

from abc import ABC, abstractmethod
from typing import Any

from app.api.v1.schemas.review import PullRequestReviewOutput


class BaseLLMClient(ABC):
    """Abstract interface for LLM-driven structured code review."""

    @abstractmethod
    async def review_code(self, context_pack: dict[str, Any]) -> PullRequestReviewOutput:
        """Analyzes a context pack and returns structured code review output."""
        pass
