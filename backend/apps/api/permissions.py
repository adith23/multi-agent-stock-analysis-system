"""Reusable DRF role permissions."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.users.models import UserRole
from apps.users.services import PermissionService


class HasAnyRole(BasePermission):
    allowed_roles: frozenset[str] = frozenset()
    message = "Your role is not authorized for this resource."

    def has_permission(self, request, view) -> bool:
        roles = getattr(view, "allowed_roles", self.allowed_roles)
        return PermissionService.has_any_role(request.user, roles)


class CanAccessSensitiveData(HasAnyRole):
    allowed_roles = PermissionService.SENSITIVE_ROLES


class IsPortfolioManager(HasAnyRole):
    allowed_roles = frozenset({UserRole.PORTFOLIO_MANAGER, UserRole.SYSTEM_ADMINISTRATOR})


class IsRiskOfficer(HasAnyRole):
    allowed_roles = frozenset({UserRole.RISK_OFFICER, UserRole.SYSTEM_ADMINISTRATOR})


class IsComplianceReviewer(HasAnyRole):
    allowed_roles = frozenset({UserRole.COMPLIANCE_REVIEWER, UserRole.SYSTEM_ADMINISTRATOR})
