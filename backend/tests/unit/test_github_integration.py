"""Unit tests for GitHub Webhook Signature Verification and PR Commenter."""

import hashlib
import hmac

import pytest

from app.infrastructure.github.pr_commenter import MockGitHubPRClient
from app.infrastructure.github.webhook_handler import GitHubWebhookHandler


def test_webhook_signature_verification_success():
    secret = "super-secret-token-key"
    handler = GitHubWebhookHandler(secret=secret)
    body = b'{"action": "opened", "pull_request": {"number": 42}}'

    # Compute genuine signature
    expected_hash = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    valid_header = f"sha256={expected_hash}"

    assert handler.verify_signature(body, valid_header) is True


def test_webhook_signature_verification_failure_tampered():
    secret = "super-secret-token-key"
    handler = GitHubWebhookHandler(secret=secret)
    body = b'{"action": "opened", "pull_request": {"number": 42}}'
    tampered_body = b'{"action": "opened", "pull_request": {"number": 999}}'

    expected_hash = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    valid_header = f"sha256={expected_hash}"

    assert handler.verify_signature(tampered_body, valid_header) is False
    assert handler.verify_signature(body, "sha256=invalidhash123") is False
    assert handler.verify_signature(body, None) is False


@pytest.mark.asyncio
async def test_mock_github_pr_commenter():
    client = MockGitHubPRClient()

    summary_res = await client.post_pr_summary(
        repo_full_name="octocat/Hello-World",
        pr_number=12,
        markdown_body="## Quality Analysis\nGrade A",
    )
    assert summary_res["status"] == "success"
    assert len(client.posted_summaries) == 1
    assert "Grade A" in client.posted_summaries[0]["body"]

    review_res = await client.post_inline_review(
        repo_full_name="octocat/Hello-World",
        pr_number=12,
        commit_sha="a1b2c3d4e5",
        summary_body="Review comments",
        comments=[
            {"path": "src/main.py", "line": 10, "body": "Suggested fix: use parameterized query"}
        ],
    )
    assert review_res["status"] == "success"
    assert len(client.posted_reviews) == 1
    assert len(client.posted_reviews[0]["comments"]) == 1
