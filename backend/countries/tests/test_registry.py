import pytest

from countries.registry import UnknownCountryError, get_plugin


@pytest.mark.parametrize(("code", "currency"), [("ES", "EUR"), ("MX", "MXN")])
def test_enabled_country_returns_its_plugin(code, currency):
    plugin = get_plugin(code)

    assert plugin.code == code
    assert plugin.currency == currency


def test_unknown_country_raises_a_clear_error():
    with pytest.raises(UnknownCountryError, match="'XX' is not enabled. Enabled: ES, MX"):
        get_plugin("XX")
