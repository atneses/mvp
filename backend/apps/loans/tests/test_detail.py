from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.loans.models import AuditEvent, LoanApplication


@pytest.fixture
def application_es(db):
    return LoanApplication.objects.create(
        country="ES",
        amount=Decimal("15000"),
        currency="EUR",
        monthly_income=Decimal("3000"),
        full_name="Ana Pérez",
        document="12345678Z",
        created_by=User.objects.create_user(username="creator"),
    )


def _client(username, role=User.Role.ANALYST, countries=("ES",)):
    client = APIClient()
    user = User.objects.create_user(username=username, role=role, allowed_countries=countries)
    client.force_authenticate(user)
    return client


def _url(application):
    return f"/api/loan-applications/{application.id}"


def test_analyst_sees_masked_pii(application_es):
    body = _client("analyst_es").get(_url(application_es)).json()

    assert body["document"] == "****5678Z"
    assert body["full_name"] == "A. P."


def test_admin_sees_full_pii_and_the_access_is_logged(application_es):
    admin = _client("admin", role=User.Role.ADMIN, countries=("ES", "MX"))

    body = admin.get(_url(application_es)).json()

    assert body["document"] == "12345678Z"
    assert body["full_name"] == "Ana Pérez"
    assert AuditEvent.objects.filter(event="pii_access", application_id=application_es.id).exists()


def test_application_of_another_country_does_not_exist_for_the_user(application_es):
    response = _client("analyst_mx", countries=("MX",)).get(_url(application_es))

    assert response.status_code == 404
