import pytest

from countries.base import InvalidDocumentError
from countries.mx.document import validate_document


@pytest.mark.parametrize(
    ("value", "normalized"),
    [
        ("HEGG560427MVZRRL04", "HEGG560427MVZRRL04"),  # official RENAPO example
        ("pega050715mjcrrna9", "PEGA050715MJCRRNA9"),  # born from 2000 (letter), lowercase
    ],
)
def test_valid_curp_is_normalized(value, normalized):
    assert validate_document(value) == normalized


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("HEGG560427MVZRRL05", "check digit"),  # right format, wrong digit
        ("HEGG560427MVZRRL0", "format"),  # 17 characters
        ("HEGG561327MVZRRL04", "format"),  # month 13
        ("HEGG560427MXXRRL04", "format"),  # unknown state
    ],
)
def test_invalid_curp_is_rejected(value, reason):
    with pytest.raises(InvalidDocumentError, match=reason) as error:
        validate_document(value)

    # The error must never echo the document (PII).
    assert value not in str(error.value)
