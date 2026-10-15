"""Spanish identity documents: DNI (citizens) and NIE (foreign residents)."""

import re

from countries.base import InvalidDocumentError

# The control letter is the number modulo 23, used as an index into this table.
CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
DNI = re.compile(r"^\d{8}[A-Z]$")  # 12345678Z
NIE = re.compile(r"^[XYZ]\d{7}[A-Z]$")  # X1234567L
# For the check, the NIE prefix is replaced by a digit: X=0, Y=1, Z=2.
NIE_PREFIX_DIGIT = {"X": "0", "Y": "1", "Z": "2"}


def validate_document(value: str) -> str:
    """Return the normalized DNI/NIE or raise InvalidDocumentError."""
    document = value.upper().replace(" ", "").replace("-", "")

    if DNI.match(document):
        number = document[:8]
    elif NIE.match(document):
        number = NIE_PREFIX_DIGIT[document[0]] + document[1:8]
    else:
        raise InvalidDocumentError(
            "Invalid format: expected a DNI (8 digits + letter) "
            "or a NIE (X/Y/Z + 7 digits + letter)."
        )

    if CONTROL_LETTERS[int(number) % 23] != document[-1]:
        raise InvalidDocumentError("Invalid control letter.")
    return document
