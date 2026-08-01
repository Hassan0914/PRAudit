"""Provider Factory instantiating SCM provider adapters."""

from typing import Dict, Optional
from app.core.exceptions import PRAuditError
from app.providers.azure_provider import AzureDevOpsProvider
from app.providers.base import BaseSCMProvider
from app.providers.bitbucket_provider import BitbucketProvider
from app.providers.github_provider import GitHubProvider
from app.providers.gitlab_provider import GitLabProvider


class ProviderFactory:
    """Factory creating SCM provider instances."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseSCMProvider] = {
            "github": GitHubProvider(),
            "gitlab": GitLabProvider(),
            "bitbucket": BitbucketProvider(),
            "azure_devops": AzureDevOpsProvider(),
        }

    def get_provider(self, provider_type: str = "github") -> BaseSCMProvider:
        """Get an SCM provider instance by type string identifier.

        Args:
            provider_type: 'github', 'gitlab', 'bitbucket', or 'azure_devops'.

        Returns:
            BaseSCMProvider instance.
        """
        p_type = provider_type.lower()
        if p_type not in self._providers:
            raise PRAuditError(f"Unsupported SCM provider type '{provider_type}'.")
        return self._providers[p_type]
