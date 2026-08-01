"""GitHub Webhook Service parsing webhook payloads and verifying HMAC signatures."""

import hmac
import hashlib
from typing import Any, Dict, Optional

from app.core.exceptions import PRAuditError
from app.core.logging import setup_logger
from app.github.models import WebhookEvent

logger = setup_logger("github.webhooks")


class GitHubWebhookService:
    """Service handling GitHub webhook verification and event dispatching."""

    def __init__(self, secret: Optional[str] = None) -> None:
        """Initialize GitHubWebhookService.

        Args:
            secret: Optional HMAC secret key.
        """
        self.secret = secret or "default_secret"

    def verify_signature(self, payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """Verify HMAC SHA-256 signature for incoming webhook HTTP request.

        Args:
            payload_bytes: Raw HTTP request body bytes.
            signature_header: 'X-Hub-Signature-256' header string.

        Returns:
            True if valid signature, False otherwise.
        """
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_sig = signature_header.split("=", 1)[1]
        computed_sig = hmac.new(
            self.secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, computed_sig)

    def parse_event(self, event_type: str, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse raw JSON webhook payload into structured WebhookEvent.

        Args:
            event_type: 'X-GitHub-Event' header value.
            payload: JSON payload dictionary.

        Returns:
            WebhookEvent instance.

        Raises:
            PRAuditError: If payload format is invalid.
        """
        action = payload.get("action", "opened")
        repo_data = payload.get("repository", {})
        repo_name = repo_data.get("name", "unknown_repo")
        pr_data = payload.get("pull_request", {})
        pr_number = pr_data.get("number", payload.get("number", 0))

        logger.info(
            "Received GitHub Webhook: Event='%s', Action='%s', Repo='%s', PR=#%d",
            event_type,
            action,
            repo_name,
            pr_number,
        )

        return WebhookEvent(
            event_type=event_type,
            action=action,
            repository_name=repo_name,
            pr_number=pr_number,
            payload=payload,
        )
