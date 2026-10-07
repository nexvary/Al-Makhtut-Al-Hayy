from app.arabic import normalize_arabic, tokenize_arabic


def test_arabic_normalization() -> None:
    assert normalize_arabic("إِنَّ الـعِلْمَ") == "ان العلم"


def test_arabic_tokenization() -> None:
    assert tokenize_arabic("قال: الزهراوي، رحمه الله") == ["قال", "الزهراوي", "رحمه", "الله"]
