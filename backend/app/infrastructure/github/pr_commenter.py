"""GitHub Pull Request Review Commenter Adapter."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.logging import logger


class BaseGitHubPRClient(ABC):
    """Abstract interface for GitHub PR commenting."""

    @abstractmethod
    async def post_pr_summary(
        self,
        repo_full_name: str,
        pr_number: int,
        markdown_body: str,
    ) -> dict[str, Any]:
        """Posts a top-level summary comment on a pull request."""
        pass

    @abstractmethod
    async def post_inline_review(
        self,
        repo_full_name: str,
        pr_number: int,
        commit_sha: str,
        summary_body: str,
        comments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Posts a structured PR review containing inline diff comments and suggested fixes."""
        pass


class MockGitHubPRClient(BaseGitHubPRClient):
    """In-memory mock GitHub client for tests and offline demonstrations."""

    def __init__(self) -> None:
        self.posted_summaries: list[dict[str, Any]] = []
        self.posted_reviews: list[dict[str, Any]] = []

    async def post_pr_summary(
        self,
        repo_full_name: str,
        pr_number: int,
        markdown_body: str,
    ) -> dict[str, Any]:
        record = {
            "id": len(self.posted_summaries) + 1,
            "repo_full_name": repo_full_name,
            "pr_number": pr_number,
            "body": markdown_body,
            "status": "success",
        }
        self.posted_summaries.append(record)
        logger.info(f"[MockGitHub] Posted summary comment to PR #{pr_number} on {repo_full_name}")
        return record

    async def post_inline_review(
        self,
        repo_full_name: str,
        pr_number: int,
        commit_sha: str,
        summary_body: str,
        comments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        record = {
            "id": len(self.posted_reviews) + 1,
            "repo_full_name": repo_full_name,
            "pr_number": pr_number,
            "commit_sha": commit_sha,
            "body": summary_body,
            "comments": comments,
            "status": "success",
        }
        self.posted_reviews.append(record)
        logger.info(
            f"[MockGitHub] Posted review with {len(comments)} inline comments on PR #{pr_number}"
        )
        return record


class RESTGitHubPRClient(BaseGitHubPRClient):
    """Live GitHub REST API client using token authentication."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Software-Quality-Platform",
        }

    async def post_pr_summary(
        self,
        repo_full_name: str,
        pr_number: int,
        markdown_body: str,
    ) -> dict[str, Any]:
        import httpx

        url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self.headers, json={"body": markdown_body})
            res.raise_for_status()
            data = res.json()
            return data if isinstance(data, dict) else {"response": data}

    async def post_inline_review(
        self,
        repo_full_name: str,
        pr_number: int,
        commit_sha: str,
        summary_body: str,
        comments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        import httpx

        url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews"
        payload = {
            "commit_id": commit_sha,
            "body": summary_body,
            "event": "COMMENT",
            "comments": comments,
        }
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self.headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return data if isinstance(data, dict) else {"response": data}


# Global default client
default_github_pr_client: BaseGitHubPRClient = MockGitHubPRClient()
