from countries.mx import bank, document, rules


class MexicoPlugin:
    code = "MX"
    currency = "MXN"
    validate_document = staticmethod(document.validate_document)
    fetch_bank_profile = staticmethod(bank.fetch_bank_profile)
    evaluate = staticmethod(rules.evaluate)


plugin = MexicoPlugin()
