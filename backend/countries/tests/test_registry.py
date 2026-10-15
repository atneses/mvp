import pytest

from countries.registry import UnknownCountryError, get_plugin


@pytest.mark.parametrize(
    ("code", "currency", "document"),
    [("ES", "EUR", "12345678Z"), ("MX", "MXN", "HEGG560427MVZRRL04")],
)
def test_enabled_country_returns_its_plugin(code, currency, document):
    plugin = get_plugin(code)

    assert plugin.code == code
    assert plugin.currency == currency
    # Each country validates its own document type.
    assert plugin.validate_document(document) == document


def test_unknown_country_raises_a_clear_error():
    with pytest.raises(UnknownCountryError, match="'XX' is not enabled. Enabled: ES, MX"):
        get_plugin("XX")
