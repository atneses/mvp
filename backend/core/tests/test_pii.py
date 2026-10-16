from core.pii import mask_document, mask_name


def test_mask_document_keeps_only_the_last_characters():
    assert mask_document("12345678Z") == "****5678Z"


def test_mask_name_keeps_only_the_initials():
    assert mask_name("Ana  Perez Lopez") == "A. P. L."
