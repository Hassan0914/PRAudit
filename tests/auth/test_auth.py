"""Unit tests for Phase 27: Authentication, Organizations, and RBAC."""

from app.auth.models import Permission, Role, User
from app.auth.service import AuthenticationService, AuthorizationService, OrganizationService


def test_authentication_service() -> None:
    auth_service = AuthenticationService()
    tokens = auth_service.authenticate_user("admin", "admin")
    assert tokens.access_token.startswith("jwt_access_")


def test_authorization_service() -> None:
    authz_service = AuthorizationService()
    admin_user = User("u1", "admin", "admin@praudit.io", "Admin", Role.ADMIN)
    guest_user = User("u2", "guest", "guest@praudit.io", "Guest", Role.GUEST)

    assert authz_service.has_permission(admin_user, Permission.MANAGE_RULES)
    assert not authz_service.has_permission(guest_user, Permission.MANAGE_RULES)


def test_organization_service() -> None:
    org_service = OrganizationService()
    org = org_service.create_organization("Acme Corp", "acme.com")
    assert org.org_id is not None
    assert len(org_service.list_organizations()) == 1
