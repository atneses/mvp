"""Contract every country plugin must fulfil.

The core (API, orchestrator, agents) only talks to this interface, so adding a
country means adding a plugin, not changing the core. More members are added
as each piece is built (bank provider, rules...).
"""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class CountryPlugin(Protocol):
    code: str  # ISO 3166-1 alpha-2, e.g. "ES"
    currency: str  # ISO 4217, e.g. "EUR"
    # Extra status transitions on top of the base flow, e.g. {"A": {"B"}}.
    state_extension: Mapping[str, set[str]]

    def validate_document(self, value: str) -> str:
        """Return the normalized document or raise InvalidDocumentError."""
        pass

    def fetch_bank_profile(self, document: str) -> dict:
        """Common format for every bank: {"monthly_debt_payments": "<decimal as text>"}."""
        pass


class InvalidDocumentError(ValueError):
    """The identity document is not valid. The message never includes the document (PII)."""
