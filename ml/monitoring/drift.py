from __future__ import annotations

import math
from collections.abc import Sequence


def population_stability_index(
    expected: Sequence[float], actual: Sequence[float], bins: int = 10
) -> float:
    if not expected or not actual:
        raise ValueError("Expected and actual samples must not be empty")
    if bins < 2:
        raise ValueError("bins must be at least 2")

    sorted_expected = sorted(float(value) for value in expected)
    boundaries = [
        sorted_expected[min(len(sorted_expected) - 1, int(len(sorted_expected) * index / bins))]
        for index in range(1, bins)
    ]

    def proportions(values: Sequence[float]) -> list[float]:
        counts = [0] * bins
        for raw in values:
            value = float(raw)
            index = 0
            while index < len(boundaries) and value > boundaries[index]:
                index += 1
            counts[index] += 1
        total = len(values)
        return [max(count / total, 1e-6) for count in counts]

    expected_pct = proportions(expected)
    actual_pct = proportions(actual)
    return sum(
        (actual_value - expected_value) * math.log(actual_value / expected_value)
        for expected_value, actual_value in zip(expected_pct, actual_pct, strict=True)
    )


def classify_drift(psi: float, threshold: float = 0.20) -> str:
    if psi >= threshold:
        return "ALERT"
    if psi >= threshold / 2:
        return "WATCH"
    return "STABLE"
