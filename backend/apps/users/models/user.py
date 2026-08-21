"""Custom user entity and stable institutional roles."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UserRole(models.TextChoices):
    PORTFOLIO_MANAGER = "portfolio_manager", "Portfolio Manager"
    INVESTMENT_ANALYST = "investment_analyst", "Investment Analyst"
    RESEARCH_ANALYST = "research_analyst", "Research Analyst"
    RISK_OFFICER = "risk_officer", "Risk Officer"
    COMPLIANCE_REVIEWER = "compliance_reviewer", "Compliance Reviewer"
    SYSTEM_ADMINISTRATOR = "system_administrator", "System Administrator"


class PlatformUserManager(UserManager["User"]):
    """Normalize email consistently for human and service-account creation."""

    def _create_user(self, username: str, email: str | None, password: str | None, **extra):
        email = self.normalize_email(email or "")
        return super()._create_user(username, email, password, **extra)


class User(AbstractUser):
    """UUID-backed user with a primary business role.

    Django groups and django-guardian permissions remain available for
    additional or object-specific authorization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.RESEARCH_ANALYST,
        db_index=True,
    )
    job_title = models.CharField(max_length=120, blank=True)

    objects = PlatformUserManager()

    class Meta:
        ordering = ("username",)
        indexes = [models.Index(fields=("role", "is_active"))]

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    @property
    def can_access_portfolio_data(self) -> bool:
        return self.is_superuser or self.role in {
            UserRole.PORTFOLIO_MANAGER,
            UserRole.RISK_OFFICER,
            UserRole.COMPLIANCE_REVIEWER,
            UserRole.SYSTEM_ADMINISTRATOR,
        }

    @property
    def can_manage_users(self) -> bool:
        return self.is_superuser or self.role == UserRole.SYSTEM_ADMINISTRATOR
