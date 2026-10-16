from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.loans.models import LoanApplication


@pytest.fixture
def application(db):
    return LoanApplication.objects.create(
        country="ES",
        amount=Decimal("15000"),
        currency="EUR",
        monthly_income=Decimal("3000"),
        full_name="Ana Pérez",
        document="12345678Z",
        created_by=User.objects.create_user(username="creator"),
    )


def _client(role):
    client = APIClient()
    user = User.objects.create_user(username=role, role=role, allowed_countries=["ES"])
    client.force_authenticate(user)
    return client


def _change(client, application, to, expected_version):
    return client.patch(
        f"/api/loan-applications/{application.id}/status",
        {"to": to, "reason": "manual check", "expected_version": expected_version},
        format="json",
    )


def test_change_with_the_current_version_then_a_stale_one(application):
    admin = _client(User.Role.ADMIN)

    ok = _change(admin, application, "CANCELLED", expected_version=1)
    # A second admin still looking at version 1.
    stale = _change(admin, application, "REJECTED", expected_version=1)

    assert ok.status_code == 200
    assert ok.json()["version"] == 2
    assert stale.status_code == 409
    application.refresh_from_db()
    assert (application.status, application.version) == ("CANCELLED", 2)


def test_illegal_transition_is_rejected(application):
    response = _change(_client(User.Role.ADMIN), application, "APPROVED", expected_version=1)

    assert response.status_code == 400
    assert "to" in response.json()["details"]


def test_analyst_cannot_change_the_status(application):
    response = _change(_client(User.Role.ANALYST), application, "CANCELLED", expected_version=1)

    assert response.status_code == 403
