import pytest

from countries.mx.bank import fetch_bank_profile


@pytest.mark.django_db(transaction=True)
def test_mexican_bank_format_is_translated_to_the_common_profile(live_server, settings):
    settings.MX_BANK_URL = f"{live_server.url}/simulators/mx/bank-profile"

    profile = fetch_bank_profile("HEGG560427MVZRRL04")

    # Cents in the provider's format, a decimal amount in ours; same answer every time.
    assert list(profile) == ["monthly_debt_payments"]
    assert profile == fetch_bank_profile("HEGG560427MVZRRL04")
    assert "." in profile["monthly_debt_payments"]
