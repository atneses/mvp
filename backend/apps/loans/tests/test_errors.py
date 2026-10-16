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


def _client(username, role=User.Role.ANALYST, countries=("ES",)):
    client = APIClient()
    user = User.objects.create_user(username=username, role=role, allowed_countries=countries)
    client.force_authenticate(user)
    return client


def test_every_error_has_the_same_format(application):
    detail = f"/api/loan-applications/{application.id}"
    status_change = {"to": "VALIDATING", "reason": "check", "expected_version": 2}
    invalid_document = {
        "country": "ES",
        "amount": "1000",
        "monthly_income": "3000",
        "full_name": "Ana",
        "document": "12345678A",
    }
    responses = {
        400: _client("es").post("/api/loan-applications", invalid_document, format="json"),
        401: APIClient().get(detail),
        403: _client("es2").patch(detail + "/status", status_change, format="json"),
        404: _client("mx", countries=("MX",)).get(detail),
        409: _client("admin", role=User.Role.ADMIN).patch(
            detail + "/status", status_change, format="json"
        ),
    }

    for expected_status, response in responses.items():
        body = response.json()
        assert response.status_code == expected_status
        assert body.keys() == {"code", "message", "details", "correlation_id"}
        assert body["correlation_id"] == response["X-Correlation-ID"]

    assert responses[400].json()["details"].keys() == {"document"}
    assert "LoanApplication" not in responses[404].json()["message"]
