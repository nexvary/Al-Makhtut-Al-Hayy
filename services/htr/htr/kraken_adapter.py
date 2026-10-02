from __future__ import annotations

from .contracts import HtrRequest, HtrResult


class KrakenEngine:
    """Integration boundary for Kraken.

    The heavy Kraken/Torch runtime is deliberately not imported by the core
    package yet. Production workers can install a pinned Kraken image and
    implement this adapter without leaking Kraken-specific structures into
    the product API.
    """

    @property
    def name(self) -> str:
        return "kraken"

    def recognize(self, request: HtrRequest) -> HtrResult:
        raise NotImplementedError(
            "Kraken worker runtime is not wired yet. "
            "Return HtrResult with source polygons and raw artifacts when implemented."
        )
