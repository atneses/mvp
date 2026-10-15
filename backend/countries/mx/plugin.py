from countries.mx import document


class MexicoPlugin:
    code = "MX"
    currency = "MXN"
    validate_document = staticmethod(document.validate_document)


plugin = MexicoPlugin()
