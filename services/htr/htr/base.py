from __future__ import annotations

from typing import Protocol

from .contracts import HtrRequest, HtrResult


class HtrEngine(Protocol):
    @property
    def name(self) -> str: ...

    def recognize(self, request: HtrRequest) -> HtrResult: ...
