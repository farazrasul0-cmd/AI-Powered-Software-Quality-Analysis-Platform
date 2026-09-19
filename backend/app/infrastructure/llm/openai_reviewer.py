"""OpenAI and Anthropic Live LLM Reviewer Adapter.

Connects to commercial foundational model APIs using Pydantic JSON schemas
with automatic error recovery and local mock fallback.
"""

import json
from typing import Any

from app.api.v1.schemas.review import PullRequestReviewOutput
from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.llm.base import BaseLLMClient
from app.infrastructure.llm.mock_reviewer import MockLLMReviewer


class OpenAILLMReviewer(BaseLLMClient):
    """Live LLM reviewer utilizing OpenAI Chat Completions API with structured output."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.LLM_MODEL
        self.fallback = MockLLMReviewer()

    async def review_code(self, context_pack: dict[str, Any]) -> PullRequestReviewOutput:
        if not self.api_key:
            return await self.fallback.review_code(context_pack)

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            system_prompt = (
                "You are a Principal Staff Software Engineer & Security Auditor conducting an automated code review.\n"
                "Analyze the provided code diff, AST context, static analyzer findings, and ML defect risk factors.\n"
                "Triangulate inputs to:\n"
                "1. Suppress false alarms from static scanners (emit category FALSE_POSITIVE_OVERRIDE with rationale).\n"
                "2. Escalate genuine security vulnerabilities and high-risk logic flaws with unified git diff patches.\n"
                "Output strictly in valid JSON matching the PullRequestReviewOutput schema."
            )

            user_prompt = f"Code Context Pack:\n{json.dumps(context_pack, indent=2)}"

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.LLM_TEMPERATURE,
                response_format={"type": "json_object"},
            )

            raw_json = response.choices[0].message.content or "{}"
            parsed = json.loads(raw_json)
            return PullRequestReviewOutput.model_validate(parsed)
        except Exception as e:
            logger.warning("OpenAI API review failed: %s; falling back to local reviewer", e)
            return await self.fallback.review_code(context_pack)
