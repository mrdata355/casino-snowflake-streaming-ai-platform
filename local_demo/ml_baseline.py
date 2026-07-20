from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean


@dataclass(frozen=True, slots=True)
class BaselineModel:
    mean_target: float

    def predict(self, rows: list[dict[str, float]]) -> list[float]:
        return [self.mean_target for _ in rows]


def train_mean_baseline(rows: list[dict[str, float]], target: str) -> BaselineModel:
    if not rows:
        raise ValueError("training rows cannot be empty")
    targets = [float(row[target]) for row in rows]
    return BaselineModel(mean_target=fmean(targets))


def mean_absolute_error(actual: list[float], predicted: list[float]) -> float:
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted lengths must match")
    if not actual:
        raise ValueError("at least one value is required")
    return fmean(abs(left - right) for left, right in zip(actual, predicted, strict=True))
