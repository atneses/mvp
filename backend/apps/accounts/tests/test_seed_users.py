import pytest
from django.core.management import call_command

from apps.accounts.models import User


@pytest.mark.django_db
def test_seed_users_can_run_twice_without_duplicates(monkeypatch):
    monkeypatch.setenv("SEED_USERS_PASSWORD", "test-password")

    call_command("seed_users")
    call_command("seed_users")

    assert User.objects.count() == 3
    assert User.objects.get(username="analyst_mx").allowed_countries == ["MX"]
