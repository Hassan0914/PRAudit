"""Authentication, Authorization, and Organization management services."""

import time
from typing import Dict, List, Optional
from app.auth.models import Organization, Permission, Role, Team, TokenResponse, User
from app.core.exceptions import PRAuditError
from app.core.logging import setup_logger

logger = setup_logger("auth.service")


class AuthenticationService:
    """Service providing user authentication and JWT token generation."""

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._tokens: Dict[str, str] = {}
        self._register_default_users()

    def _register_default_users(self) -> None:
        default_admin = User(
            user_id="usr_admin_1",
            username="admin",
            email="admin@praudit.io",
            full_name="System Administrator",
            role=Role.ADMIN,
        )
        self._users[default_admin.username] = default_admin

    def authenticate_user(self, username: str, password: str) -> TokenResponse:
        """Authenticate user and issue JWT access/refresh tokens.

        Args:
            username: Username.
            password: User password.

        Returns:
            TokenResponse object.
        """
        user = self._users.get(username)
        if not user or not user.is_active:
            raise PRAuditError("Invalid credentials or user inactive.")

        acc_token = f"jwt_access_{user.user_id}_{int(time.time())}"
        ref_token = f"jwt_refresh_{user.user_id}_{int(time.time())}"
        self._tokens[acc_token] = user.user_id

        logger.info("Authenticated user '%s' (Role: %s)", username, user.role.value)
        return TokenResponse(access_token=acc_token, refresh_token=ref_token)


class AuthorizationService:
    """Service providing Role-Based Access Control (RBAC) permission checks."""

    ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
        Role.OWNER: list(Permission),
        Role.ADMIN: [Permission.READ_REPO, Permission.WRITE_REPO, Permission.TRIGGER_REVIEW, Permission.MANAGE_RULES, Permission.ADMIN_ORG],
        Role.MAINTAINER: [Permission.READ_REPO, Permission.WRITE_REPO, Permission.TRIGGER_REVIEW, Permission.MANAGE_RULES],
        Role.REVIEWER: [Permission.READ_REPO, Permission.TRIGGER_REVIEW],
        Role.DEVELOPER: [Permission.READ_REPO, Permission.TRIGGER_REVIEW],
        Role.GUEST: [Permission.READ_REPO],
    }

    def has_permission(self, user: User, permission: Permission) -> bool:
        """Check if a user has a specific permission based on their RBAC role."""
        allowed = self.ROLE_PERMISSIONS.get(user.role, [])
        return permission in allowed


class OrganizationService:
    """Service providing organization and team hierarchy management."""

    def __init__(self) -> None:
        self._orgs: Dict[str, Organization] = {}

    def create_organization(self, name: str, domain: str) -> Organization:
        """Create a new enterprise organization."""
        org_id = f"org_{len(self._orgs) + 1}"
        org = Organization(org_id=org_id, name=name, domain=domain)
        self._orgs[org_id] = org
        logger.info("Created Organization '%s' (Domain: %s)", name, domain)
        return org

    def list_organizations(self) -> List[Organization]:
        """List all registered organizations."""
        return list(self._orgs.values())
