import pytest

from apps.accounts.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="ana", password="correct-password")


def test_login_with_valid_credentials_returns_tokens(client, user):
    response = client.post("/api/auth/token", {"username": "ana", "password": "correct-password"})

    assert response.status_code == 200
    assert {"access", "refresh"} <= response.json().keys()


def test_login_with_wrong_password_is_rejected(client, user):
    response = client.post("/api/auth/token", {"username": "ana", "password": "wrong"})

    assert response.status_code == 401


def test_refresh_token_cannot_be_reused_after_rotation(client, user):
    login = client.post("/api/auth/token", {"username": "ana", "password": "correct-password"})
    refresh = login.json()["refresh"]

    first = client.post("/api/auth/refresh", {"refresh": refresh})
    second = client.post("/api/auth/refresh", {"refresh": refresh})

    assert first.status_code == 200
    assert second.status_code == 401
