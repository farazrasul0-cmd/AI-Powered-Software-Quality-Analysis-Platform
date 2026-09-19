"""Factory for selecting and instantiating LLM code review providers."""

from app.core.config import settings
from app.infrastructure.llm.base import BaseLLMClient
from app.infrastructure.llm.mock_reviewer import MockLLMReviewer
from app.infrastructure.llm.openai_reviewer import OpenAILLMReviewer


class LLMFactory:
    """Selects live or mock LLM reviewer based on configured environment variables."""

    @classmethod
    def get_reviewer(cls) -> BaseLLMClient:
        if settings.OPENAI_API_KEY:
            return OpenAILLMReviewer(api_key=settings.OPENAI_API_KEY)
        return MockLLMReviewer()


# Default singleton reviewer
default_llm_reviewer: BaseLLMClient = LLMFactory.get_reviewer()
