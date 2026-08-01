"""Data models for Authentication, Organizations, Teams, and RBAC roles."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Role(str, Enum):
    """Role-based access control (RBAC) roles."""

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MAINTAINER = "MAINTAINER"
    REVIEWER = "REVIEWER"
    DEVELOPER = "DEVELOPER"
    GUEST = "GUEST"


class Permission(str, Enum):
    """Granular system permissions."""

    READ_REPO = "READ_REPO"
    WRITE_REPO = "WRITE_REPO"
    TRIGGER_REVIEW = "TRIGGER_REVIEW"
    MANAGE_RULES = "MANAGE_RULES"
    ADMIN_ORG = "ADMIN_ORG"


@dataclass
class User:
    """Represents a system user."""

    user_id: str
    username: str
    email: str
    full_name: str
    role: Role = Role.DEVELOPER
    is_active: bool = True


@dataclass
class Team:
    """Represents an organizational team."""

    team_id: str
    name: str
    organization_id: str
    members: List[User] = field(default_factory=list)


@dataclass
class Organization:
    """Represents an enterprise organization."""

    org_id: str
    name: str
    domain: str
    teams: List[Team] = field(default_factory=list)


@dataclass
class TokenResponse:
    """JWT Access and Refresh Token container."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
