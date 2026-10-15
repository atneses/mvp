"""Mexican identity document: CURP (Clave Única de Registro de Población)."""

import re

from countries.base import InvalidDocumentError

# Official two-letter codes of the 32 states, plus NE (born abroad).
STATES = (
    "AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|"
    "MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE"
)
CURP = re.compile(
    r"^[A-Z][AEIOUX][A-Z]{2}"  # name initials: surname + its first inner vowel + surname + name
    r"\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])"  # birth date YYMMDD
    r"[HM]"  # sex
    rf"({STATES})"  # state of birth
    r"[B-DF-HJ-NP-TV-Z]{3}"  # first inner consonants of surnames and name
    r"[A-Z\d]"  # homonym differentiator: digit before 2000, letter from 2000
    r"\d$"  # check digit
)
# Value of each character for the check digit (note the Ñ after N).
CHECK_ALPHABET = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"


def validate_document(value: str) -> str:
    """Return the normalized CURP or raise InvalidDocumentError."""
    document = value.upper().replace(" ", "")

    if not CURP.match(document):
        raise InvalidDocumentError("Invalid format: expected an 18-character CURP.")
    if _check_digit(document[:17]) != int(document[17]):
        raise InvalidDocumentError("Invalid check digit.")
    return document


def _check_digit(first_17: str) -> int:
    # Each character's value is weighted 18, 17, ... 2; the digit completes the next ten.
    total = sum(CHECK_ALPHABET.index(char) * (18 - i) for i, char in enumerate(first_17))
    return (10 - total % 10) % 10
