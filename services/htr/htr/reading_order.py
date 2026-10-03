from __future__ import annotations

from .contracts import RecognizedLine


def _bounds(line: RecognizedLine) -> tuple[float, float, float, float]:
    if not line.polygon:
        return (0, 0, 0, 0)
    xs = [point.x for point in line.polygon]
    ys = [point.y for point in line.polygon]
    return (min(xs), min(ys), max(xs), max(ys))


def heuristic_reading_order(lines: list[RecognizedLine], *, rtl: bool = True) -> list[RecognizedLine]:
    """Fallback reading order.

    Real manuscript reading order should prefer model/PAGE metadata. This
    heuristic groups by vertical position and uses right-to-left position as
    a tiebreaker.
    """
    return sorted(
        lines,
        key=lambda line: (
            round(_bounds(line)[1] / 20),
            -_bounds(line)[2] if rtl else _bounds(line)[0],
        ),
    )
