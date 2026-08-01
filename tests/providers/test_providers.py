"""Unit tests for Phase 28: SCM Provider Platform."""

from app.providers.factory import ProviderFactory


def test_scm_provider_factory() -> None:
    factory = ProviderFactory()

    gh = factory.get_provider("github")
    assert gh.provider_type == "github"

    gl = factory.get_provider("gitlab")
    assert gl.provider_type == "gitlab"

    bb = factory.get_provider("bitbucket")
    assert bb.provider_type == "bitbucket"

    az = factory.get_provider("azure_devops")
    assert az.provider_type == "azure_devops"

    diff = gh.get_pull_request_diff("org/repo", 42)
    assert "github patch" in diff
