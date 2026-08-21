"""Central authorization service for business-role and object permissions."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.core.exceptions import PermissionDenied
from guardian.shortcuts import assign_perm, get_perms, remove_perm

from apps.users.models import User, UserRole


class PermissionService:
    SENSITIVE_ROLES = frozenset(
        {
            UserRole.PORTFOLIO_MANAGER,
            UserRole.RISK_OFFICER,
            UserRole.COMPLIANCE_REVIEWER,
            UserRole.SYSTEM_ADMINISTRATOR,
        }
    )

    @staticmethod
    def has_any_role(user: User, roles: Iterable[str]) -> bool:
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (user.is_superuser or user.role in set(roles))
        )

    @classmethod
    def require_any_role(cls, user: User, roles: Iterable[str]) -> None:
        if not cls.has_any_role(user, roles):
            raise PermissionDenied("Your role is not authorized for this action.")

    @classmethod
    def can_access_sensitive_data(cls, user: User) -> bool:
        return cls.has_any_role(user, cls.SENSITIVE_ROLES)

    @staticmethod
    def grant_object_permission(user: User, permission: str, obj: Any) -> None:
        assign_perm(permission, user, obj)

    @staticmethod
    def revoke_object_permission(user: User, permission: str, obj: Any) -> None:
        remove_perm(permission, user, obj)

    @staticmethod
    def object_permissions(user: User, obj: Any) -> frozenset[str]:
        return frozenset(get_perms(user, obj))
