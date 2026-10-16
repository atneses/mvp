import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.loans.models import LoanApplication

URL = "/api/loan-applications"


@pytest.fixture
def analyst_es(db):
    client = APIClient()
    client.force_authenticate(User.objects.create_user(username="es", allowed_countries=["ES"]))
    return client


def _payload(**overrides):
    return {
        "country": "ES",
        "amount": "15000.00",
        "monthly_income": "3000.00",
        "full_name": "Ana Pérez",
        "document": "12345678-z",
        **overrides,
    }


def test_create_application(analyst_es):
    # The client tries to choose the currency; the server ignores it.
    response = analyst_es.post(URL, _payload(currency="MXN"), format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "CREATED"
    assert body["currency"] == "EUR"
    assert "document" not in body and "full_name" not in body
    assert LoanApplication.objects.get(id=body["id"]).document == "12345678Z"  # normalized


def test_invalid_document_points_to_the_field(analyst_es):
    response = analyst_es.post(URL, _payload(document="12345678A"), format="json")

    assert response.status_code == 400
    assert "document" in response.json()
    assert "12345678A" not in response.content.decode()


def test_cannot_create_in_a_country_outside_allowed(analyst_es):
    response = analyst_es.post(URL, _payload(country="MX"), format="json")

    assert response.status_code == 403


def test_second_active_application_for_the_same_document_is_a_conflict(analyst_es):
    analyst_es.post(URL, _payload(document="12345678-z"), format="json")

    # Same document written in its normalized form.
    response = analyst_es.post(URL, _payload(document="12345678Z"), format="json")

    assert response.status_code == 409
    assert response.json()["detail"] == "There is already an active application for this document."
