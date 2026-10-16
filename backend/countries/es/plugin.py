from countries.es import document


class SpainPlugin:
    code = "ES"
    currency = "EUR"
    # Synchronous bank provider: the base flow is enough.
    state_extension = {}
    validate_document = staticmethod(document.validate_document)


plugin = SpainPlugin()
