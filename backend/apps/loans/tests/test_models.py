from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.accounts.models import User
from apps.loans.models import LoanApplication


@pytest.fixture
def new_application(db):
    user = User.objects.create_user(username="ana", password="x")

    def create(**fields):
        return LoanApplication.objects.create(
            country="ES",
            amount=Decimal("10000"),
            currency="EUR",
            monthly_income=Decimal("3000"),
            full_name="Ana Pérez",
            document="12345678Z",
            created_by=user,
            **fields,
        )

    return create


def test_only_one_active_application_per_document(new_application):
    new_application()

    with pytest.raises(IntegrityError):
        new_application()


def test_new_application_allowed_once_the_previous_one_is_closed(new_application):
    new_application(status=LoanApplication.Status.REJECTED)

    assert new_application().status == LoanApplication.Status.CREATED
