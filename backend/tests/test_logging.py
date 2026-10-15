import json
import logging

import pytest
import structlog

from core.logging import REDACTED, redact_pii


def test_dni_in_free_text_is_redacted():
    event = redact_pii(None, "info", {"event": "invalid application for DNI 12345678Z"})

    assert event["event"] == f"invalid application for DNI {REDACTED}"


def test_sensitive_keys_are_redacted_even_when_nested():
    event = redact_pii(
        None,
        "info",
        {"event": "created", "applicant": {"full_name": "Ana Pérez", "country": "ES"}},
    )

    assert event["applicant"] == {"full_name": REDACTED, "country": "ES"}


def test_nie_and_curp_are_redacted():
    event = redact_pii(None, "info", {"event": "X1234567L and GODE561231HDFRRN09"})

    assert event["event"] == f"{REDACTED} and {REDACTED}"


def test_log_line_is_json_without_the_dni(caplog_json):
    structlog.get_logger("test").info("lookup", document="12345678Z", note="DNI 12345678Z")

    line = json.loads(caplog_json())
    assert line["document"] == REDACTED
    assert line["note"] == f"DNI {REDACTED}"
    assert "12345678Z" not in caplog_json()


def test_response_has_a_generated_correlation_id(client):
    response = client.get("/healthz")

    assert len(response["X-Correlation-ID"]) == 36  # uuid4


def test_incoming_correlation_id_is_kept(client):
    response = client.get("/healthz", headers={"X-Correlation-ID": "abc-123"})

    assert response["X-Correlation-ID"] == "abc-123"


def test_unsafe_correlation_id_is_replaced(client):
    response = client.get("/healthz", headers={"X-Correlation-ID": "bad\nid"})

    assert response["X-Correlation-ID"] != "bad\nid"


def test_request_log_line_has_the_correlation_id(client, caplog_json):
    client.get("/healthz", headers={"X-Correlation-ID": "abc-123"})

    line = json.loads(caplog_json())
    assert line["event"] == "request_finished"
    assert line["correlation_id"] == "abc-123"
    assert line["status"] == 200


@pytest.fixture
def caplog_json(caplog):
    """Return the last captured log line rendered by the real JSON formatter."""
    caplog.set_level(logging.INFO)
    formatter = logging.getHandlerByName("console").formatter

    def last_line():
        return formatter.format(caplog.records[-1])

    return last_line
