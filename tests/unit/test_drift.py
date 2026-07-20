from ml.monitoring.drift import classify_drift, population_stability_index


def test_population_stability_index_detects_distribution_shift() -> None:
    expected = [1, 2, 3, 4, 5] * 20
    stable = [1, 2, 3, 4, 5] * 20
    shifted = [20, 21, 22, 23, 24] * 20
    assert population_stability_index(expected, stable) < 0.01
    assert population_stability_index(expected, shifted) > 0.20


def test_drift_classification() -> None:
    assert classify_drift(0.05) == "STABLE"
    assert classify_drift(0.15) == "WATCH"
    assert classify_drift(0.25) == "ALERT"
