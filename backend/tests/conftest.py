from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.users.models import User, UserRole


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(
        username="analyst",
        email="analyst@example.com",
        password="correct-horse-battery-staple",
        role=UserRole.RESEARCH_ANALYST,
    )


@pytest.fixture
def authenticated_client(api_client: APIClient, user: User) -> APIClient:
    api_client.force_authenticate(user)
    return api_client
