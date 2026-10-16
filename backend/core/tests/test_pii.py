from core.pii import mask_document


def test_mask_document_keeps_only_the_last_characters():
    assert mask_document("12345678Z") == "****5678Z"
