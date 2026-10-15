import json
import logging

import pytest
import structlog

from core.logging import REDACTED, redact_pii


def test_log_line_has_no_pii(caplog):
    caplog.set_level(logging.INFO)

    structlog.get_logger("test").info(
        "lookup",
        document="12345678Z",
        applicant={"full_name": "Ana Pérez", "country": "ES"},
        note="DNI 12345678Z",
    )

    # Render the record with the real JSON formatter configured in settings.
    formatter = logging.getHandlerByName("console").formatter
    output = formatter.format(caplog.records[-1])
    line = json.loads(output)
    assert line["document"] == REDACTED
    assert line["applicant"] == {"full_name": REDACTED, "country": "ES"}
    assert line["note"] == f"DNI {REDACTED}"
    assert "12345678Z" not in output
    assert "Ana Pérez" not in output


@pytest.mark.parametrize(
    "document",
    [
        "12345678Z",  # DNI (ES)
        "X1234567L",  # NIE (ES)
        "GODE561231HDFRRN09",  # CURP (MX)
    ],
)
def test_identity_documents_in_text_are_redacted(document):
    event = redact_pii(None, "info", {"event": f"invalid document {document}"})

    assert event["event"] == f"invalid document {REDACTED}"
