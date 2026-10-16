"""PII helpers shared by the API and the agents."""

VISIBLE_CHARS = 5


def mask_document(document: str) -> str:
    """What an analyst sees: only the last characters ("****5678Z")."""
    return "****" + document[-VISIBLE_CHARS:]


def mask_name(full_name: str) -> str:
    """Initials only: "Ana Pérez" -> "A. P."."""
    return " ".join(f"{word[0]}." for word in full_name.split())
