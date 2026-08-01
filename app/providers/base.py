"""Base SCM Provider interface abstracting Git platform interactions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseSCMProvider(ABC):
    """Abstract base class for all SCM providers (GitHub, GitLab, Bitbucket, Azure DevOps)."""

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """SCM Provider type string identifier."""
        pass

    @abstractmethod
    def get_repository_details(self, repo_identifier: str) -> Dict[str, Any]:
        """Retrieve repository metadata details."""
        pass

    @abstractmethod
    def get_pull_request_diff(self, repo_identifier: str, pr_number: int) -> str:
        """Retrieve raw unified diff for a Pull Request."""
        pass

    @abstractmethod
    def post_inline_comment(
        self, repo_identifier: str, pr_number: int, file_path: str, line: int, comment: str
    ) -> Dict[str, Any]:
        """Post an inline review comment on a Pull Request diff line."""
        pass
