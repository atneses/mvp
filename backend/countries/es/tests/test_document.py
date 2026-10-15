import pytest

from countries.base import InvalidDocumentError
from countries.es.document import validate_document


@pytest.mark.parametrize(
    ("value", "normalized"),
    [
        ("12345678Z", "12345678Z"),  # DNI
        ("12345678-z", "12345678Z"),  # DNI typed with a dash and lowercase
        ("X1234567L", "X1234567L"),  # NIE with each prefix
        ("Y1234567X", "Y1234567X"),
        ("Z1234567R", "Z1234567R"),
    ],
)
def test_valid_documents_are_normalized(value, normalized):
    assert validate_document(value) == normalized


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("12345678A", "control letter"),  # right format, wrong letter
        ("X1234567A", "control letter"),
        ("1234567Z", "format"),  # 7 digits
        ("W1234567L", "format"),  # unknown NIE prefix
    ],
)
def test_invalid_documents_are_rejected(value, reason):
    with pytest.raises(InvalidDocumentError, match=reason) as error:
        validate_document(value)

    # The error must never echo the document (PII).
    assert value not in str(error.value)
