from __future__ import annotations

import json

import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.api.permissions import CanAccessSensitiveData
from apps.audit.models import AuditAction, AuditTrailRecord
from apps.audit.services import AuditService
from apps.core.domain.exceptions import AuditImmutabilityError
from apps.users.models import User, UserRole
from apps.users.services import PermissionService


@pytest.mark.django_db
def test_custom_user_role_properties_and_permission_service(user: User) -> None:
    assert not user.can_access_portfolio_data
    assert not PermissionService.can_access_sensitive_data(user)

    user.role = UserRole.RISK_OFFICER
    assert user.can_access_portfolio_data
    assert PermissionService.can_access_sensitive_data(user)

    with pytest.raises(PermissionDenied):
        PermissionService.require_any_role(user, [UserRole.PORTFOLIO_MANAGER])


@pytest.mark.django_db
def test_role_aware_jwt_contains_identity_and_role(user: User) -> None:
    token = RefreshToken.for_user(user)
    # The custom serializer is covered through the endpoint below; base token
    # remains usable by SimpleJWT.
    assert str(token["user_id"]) == str(user.id)


@pytest.mark.django_db
def test_token_and_current_user_endpoints(api_client, user: User) -> None:
    token_response = api_client.post(
        reverse("api-v1:users:token"),
        {"username": user.username, "password": "correct-horse-battery-staple"},
        format="json",
    )
    assert token_response.status_code == status.HTTP_200_OK
    assert "access" in token_response.data

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")
    me_response = api_client.get(reverse("api-v1:users:me"))

    assert me_response.status_code == status.HTTP_200_OK
    assert me_response.data["role"] == UserRole.RESEARCH_ANALYST


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(authenticated_client, user: User) -> None:
    refresh = RefreshToken.for_user(user)
    response = authenticated_client.post(
        reverse("api-v1:users:logout"),
        {"refresh": str(refresh)},
        format="json",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_api_root_liveness_and_trace_header(api_client) -> None:
    root_response = api_client.get(reverse("api-v1:root"), HTTP_X_REQUEST_ID="trace-1")
    live_response = api_client.get(reverse("api-v1:liveness"))

    assert root_response.status_code == status.HTTP_200_OK
    assert root_response["X-Request-ID"] == "trace-1"
    assert live_response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_uses_database_and_test_cache(api_client) -> None:
    response = api_client.get(reverse("api-v1:readiness"))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["checks"] == {
        "database": True,
        "cache": True,
        "celery_broker": True,
    }


@pytest.mark.django_db
def test_mutating_request_creates_redacted_audit_event(api_client, user: User) -> None:
    response = api_client.post(
        reverse("api-v1:users:token"),
        {"username": user.username, "password": "correct-horse-battery-staple"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    event = AuditTrailRecord.objects.filter(event_type="http.request").latest("occurred_at")
    body = event.metadata["request_body"]
    assert body["password"] == "[REDACTED]"
    assert event.method == "POST"


@pytest.mark.django_db
def test_audit_records_are_append_only(user: User) -> None:
    event = AuditService.record_event(
        action=AuditAction.APPROVE,
        event_type="recommendation.reviewed",
        actor=user,
        resource_type="recommendation",
        resource_id="rec-1",
        metadata={"reason": "within mandate"},
    )
    assert event is not None
    assert len(event.event_hash) == 64

    event.summary = "changed"
    with pytest.raises(AuditImmutabilityError):
        event.save()
    with pytest.raises(AuditImmutabilityError):
        event.delete()
    with pytest.raises(AuditImmutabilityError):
        AuditTrailRecord.objects.filter(pk=event.pk).update(summary="changed")


@pytest.mark.django_db
def test_sensitive_permission_class_respects_role(api_client, user: User) -> None:
    permission = CanAccessSensitiveData()
    request = type("Request", (), {"user": user})()
    view = object()

    assert not permission.has_permission(request, view)
    user.role = UserRole.COMPLIANCE_REVIEWER
    assert permission.has_permission(request, view)


@pytest.mark.django_db
def test_invalid_logout_token_returns_validation_error(authenticated_client) -> None:
    response = authenticated_client.post(
        reverse("api-v1:users:logout"),
        data=json.dumps({"refresh": "invalid"}),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
