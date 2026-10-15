from countries.es import document


class SpainPlugin:
    code = "ES"
    currency = "EUR"
    validate_document = staticmethod(document.validate_document)


plugin = SpainPlugin()
