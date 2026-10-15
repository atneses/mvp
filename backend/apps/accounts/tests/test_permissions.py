from types import SimpleNamespace

import pytest

from apps.accounts.models import User
from apps.accounts.permissions import CountryScoped, IsAdmin


def _request(user, data=None):
    return SimpleNamespace(user=user, data=data or {})


@pytest.mark.parametrize(("role", "allowed"), [(User.Role.ANALYST, False), (User.Role.ADMIN, True)])
def test_only_admins_pass_is_admin(role, allowed):
    request = _request(User(role=role))

    assert IsAdmin().has_permission(request, view=None) is allowed


@pytest.mark.parametrize(("country", "allowed"), [("ES", True), ("MX", False)])
def test_spanish_analyst_only_accesses_spain(country, allowed):
    analyst_es = User(role=User.Role.ANALYST, allowed_countries=["ES"])
    permission = CountryScoped()

    # Creating an application in that country...
    assert permission.has_permission(_request(analyst_es, {"country": country}), None) is allowed
    # ...and acting on an existing one.
    obj = SimpleNamespace(country=country)
    assert permission.has_object_permission(_request(analyst_es), None, obj) is allowed
