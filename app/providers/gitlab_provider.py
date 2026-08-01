"""GitLab SCM Provider implementation."""

from typing import Any, Dict
from app.core.logging import setup_logger
from app.providers.base import BaseSCMProvider

logger = setup_logger("providers.gitlab")


class GitLabProvider(BaseSCMProvider):
    """GitLab SCM provider."""

    @property
    def provider_type(self) -> str:
        return "gitlab"

    def get_repository_details(self, repo_identifier: str) -> Dict[str, Any]:
        return {"provider": self.provider_type, "repository": repo_identifier, "default_branch": "main"}

    def get_pull_request_diff(self, repo_identifier: str, pr_number: int) -> str:
        return f"diff --git a/src/main.py b/src/main.py\n--- a/src/main.py\n+++ b/src/main.py\n@@ -1,3 +1,4 @@\n+# gitlab patch\n"

    def post_inline_comment(
        self, repo_identifier: str, pr_number: int, file_path: str, line: int, comment: str
    ) -> Dict[str, Any]:
        logger.info("Posted GitLab comment on %s MR #%d (%s:%d)", repo_identifier, pr_number, file_path, line)
        return {"status": "posted", "provider": self.provider_type, "id": 202}
