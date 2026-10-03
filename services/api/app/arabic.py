from __future__ import annotations

import re
import unicodedata

_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL = "\u0640"
_NON_WORD = re.compile(r"[^\w\u0600-\u06FF]+", re.UNICODE)


def normalize_arabic(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _DIACRITICS.sub("", text).replace(_TATWEEL, "")
    table = str.maketrans(
        {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ٱ": "ا",
            "ى": "ي",
            "ؤ": "و",
            "ئ": "ي",
        }
    )
    return " ".join(text.translate(table).split())


def tokenize_arabic(text: str) -> list[str]:
    normalized = normalize_arabic(text).lower()
    return [token for token in _NON_WORD.sub(" ", normalized).split() if token]
