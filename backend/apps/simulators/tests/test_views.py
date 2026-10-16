import pytest


@pytest.fixture
def ask_spanish_bank(client):
    def ask(dni):
        return client.post("/simulators/es/bank-profile", {"dni": dni}, "application/json").json()

    return ask


def test_spanish_bank_answers_the_same_for_the_same_document(ask_spanish_bank):
    assert ask_spanish_bank("12345678Z") == ask_spanish_bank("12345678Z")
    assert ask_spanish_bank("12345678Z") != ask_spanish_bank("87654321X")
