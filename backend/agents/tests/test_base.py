from types import SimpleNamespace

import pytest

from agents.base import AgentContext, FieldNotAllowedError


def test_agent_cannot_read_fields_outside_its_policy():
    application = SimpleNamespace(country="ES", amount=15000, document="12345678Z")

    context = AgentContext(application, frozenset({"country", "amount"}))

    assert context["amount"] == 15000
    with pytest.raises(FieldNotAllowedError):
        context["document"]
