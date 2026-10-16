from countries.mx import document


class MexicoPlugin:
    code = "MX"
    currency = "MXN"
    # Asynchronous bank provider: wait for its callback; on timeout, retry or give up.
    state_extension = {
        "FETCHING_BANK_DATA": {"WAITING_BANK_CALLBACK"},
        "WAITING_BANK_CALLBACK": {"EVALUATING", "FETCHING_BANK_DATA", "FAILED"},
    }
    validate_document = staticmethod(document.validate_document)

    def fetch_bank_profile(self, document):
        raise NotImplementedError("The Mexican bank provider arrives in step 35.")


plugin = MexicoPlugin()
