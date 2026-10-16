from countries.es import bank, document, rules


class SpainPlugin:
    code = "ES"
    currency = "EUR"
    validate_document = staticmethod(document.validate_document)
    fetch_bank_profile = staticmethod(bank.fetch_bank_profile)
    evaluate = staticmethod(rules.evaluate)


plugin = SpainPlugin()
