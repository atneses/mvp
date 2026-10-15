import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_new_user_has_least_privilege():
    user = User.objects.create_user(username="ana", password="x")

    assert user.role == User.Role.ANALYST
    assert user.allowed_countries == []
