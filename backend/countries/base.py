"""Contract every country plugin must fulfil.

The core (API, orchestrator, agents) only talks to this interface, so adding a
country means adding a plugin, not changing the core. More members are added
as each piece is built (bank provider, rules, state extension...).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class CountryPlugin(Protocol):
    code: str  # ISO 3166-1 alpha-2, e.g. "ES"
    currency: str  # ISO 4217, e.g. "EUR"

    def validate_document(self, value: str) -> str:
        """Return the normalized document or raise InvalidDocumentError."""
        pass


class InvalidDocumentError(ValueError):
    """The identity document is not valid. The message never includes the document (PII)."""
