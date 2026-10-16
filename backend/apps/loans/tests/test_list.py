from datetime import UTC, datetime
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.loans.models import LoanApplication

URL = "/api/loan-applications"
S = LoanApplication.Status


@pytest.fixture
def make_application(db):
    creator = User.objects.create_user(username="creator")
    counter = iter(range(1000))

    def make(**fields):
        return LoanApplication.objects.create(
            **{
                "country": "ES",
                "amount": Decimal("10000"),
                "currency": "EUR",
                "monthly_income": Decimal("3000"),
                "full_name": "Ana Pérez",
                "document": f"DOC{next(counter)}",
                "created_by": creator,
                **fields,
            }
        )

    return make


@pytest.fixture
def analyst_es(db):
    client = APIClient()
    client.force_authenticate(User.objects.create_user(username="es", allowed_countries=["ES"]))
    return client


def _ids(response):
    return [row["id"] for row in response.json()["results"]]


def test_filters_and_country_scope(analyst_es, make_application):
    match = make_application(status=S.MANUAL_REVIEW)
    make_application(status=S.CREATED)  # other status
    make_application(country="MX", status=S.MANUAL_REVIEW)  # country not allowed

    response = analyst_es.get(URL, {"status": "MANUAL_REVIEW"})

    assert _ids(response) == [str(match.id)]


def test_cursor_pages_never_repeat_or_skip_rows(analyst_es, make_application):
    applications = [make_application() for _ in range(5)]
    # Worst case for a cursor: every row created at the very same instant.
    LoanApplication.objects.update(created_at=datetime(2026, 1, 1, tzinfo=UTC))

    seen, url = [], URL + "?page_size=2"
    while url:
        page = analyst_es.get(url).json()
        seen += [row["id"] for row in page["results"]]
        url = page["next"]

    assert sorted(seen) == sorted(str(a.id) for a in applications)
    assert len(seen) == len(set(seen))
