"""Literal witness comparison. No inferred alignment or automatic critical reading."""
from difflib import SequenceMatcher

from pydantic import BaseModel


class WordDifference(BaseModel):
    operation: str
    left: list[str]
    right: list[str]
    left_range: tuple[int, int]
    right_range: tuple[int, int]


def word_differences(left: str, right: str) -> list[WordDifference]:
    a, b = left.split(), right.split()
    return [WordDifference(operation=tag, left=a[i:j], right=b[k:l],
                           left_range=(i, j), right_range=(k, l))
            for tag, i, j, k, l in SequenceMatcher(None, a, b, autojunk=False).get_opcodes()]
