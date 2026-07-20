from local_demo.ml_baseline import mean_absolute_error, train_mean_baseline


def test_mean_baseline() -> None:
    rows = [{"target": 10.0}, {"target": 20.0}, {"target": 30.0}]
    model = train_mean_baseline(rows, "target")
    predictions = model.predict(rows)

    assert predictions == [20.0, 20.0, 20.0]
    assert mean_absolute_error([10.0, 20.0, 30.0], predictions) == 20 / 3
