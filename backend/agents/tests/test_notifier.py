from types import SimpleNamespace
from uuid import uuid7

from agents import notifier
from agents.base import AgentContext
from agents.notifier import NotifierAgent


def test_notification_carries_ids_and_status_but_no_pii(monkeypatch):
    sent = []
    monkeypatch.setattr(notifier, "post_json", lambda url, payload: sent.append(payload))
    application = SimpleNamespace(
        id=uuid7(),
        country="ES",
        status="APPROVED",
        version=4,
        full_name="Ana Pérez",
        document="12345678Z",
    )
    agent = NotifierAgent()

    agent.run(AgentContext(application, agent.fields))

    [payload] = sent
    assert payload["status"] == "APPROVED"
    assert payload["event_id"] == f"{application.id}:4"
    assert "Ana" not in str(payload) and "12345678Z" not in str(payload)
