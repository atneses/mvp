from countries.mx import bank, document


class MexicoPlugin:
    code = "MX"
    currency = "MXN"
    validate_document = staticmethod(document.validate_document)
    fetch_bank_profile = staticmethod(bank.fetch_bank_profile)

    def evaluate(self, amount, monthly_income, bank_profile):
        raise NotImplementedError("The Mexican rules arrive in step 38.")


plugin = MexicoPlugin()
