from __future__ import annotations

import re
import unicodedata

_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL = "\u0640"


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
    cleaned = "".join(
        char if unicodedata.category(char)[0] in {"L", "N"} or char == "_" else " "
        for char in normalized
    )
    return [token for token in cleaned.split() if token]
