"""GitHub Webhook Signature Verification and Event Handling."""

import hashlib
import hmac
import os
from typing import Any

from app.api.v1.schemas.export import GitHubWebhookPayload
from app.core.logging import logger


class GitHubWebhookHandler:
    """Validates and processes GitHub Webhook events with constant-time HMAC comparison."""

    def __init__(self, secret: str | None = None) -> None:
        self.secret = secret or os.environ.get("GITHUB_WEBHOOK_SECRET", "test-secret-key-123")

    def verify_signature(self, raw_payload: bytes, signature_header: str | None) -> bool:
        """Verifies the X-Hub-Signature-256 header using constant-time comparison to prevent timing attacks."""
        if not signature_header:
            logger.warning("Missing X-Hub-Signature-256 header")
            return False

        if not self.secret:
            logger.warning("No GITHUB_WEBHOOK_SECRET configured; rejecting webhook")
            return False

        # GitHub signature header format is 'sha256=<hex_digest>'
        expected_hash = hmac.new(
            self.secret.encode("utf-8"),
            raw_payload,
            hashlib.sha256,
        ).hexdigest()
        expected_signature = f"sha256={expected_hash}"

        return hmac.compare_digest(expected_signature, signature_header)

    def parse_payload(self, raw_data: dict[str, Any]) -> GitHubWebhookPayload:
        """Parses and validates incoming GitHub webhook JSON payload."""
        return GitHubWebhookPayload.model_validate(raw_data)


# Global singleton instance
github_webhook_handler = GitHubWebhookHandler()
