import json
from pathlib import Path

from local_demo.pipeline import run_demo


def test_local_demo_is_deterministic_and_writes_layers(tmp_path: Path) -> None:
    summary = run_demo(tmp_path, count=50, seed=355)

    assert summary["raw_event_count"] == 51
    assert summary["deduplicated_event_count"] == 50
    assert summary["duplicate_count_removed"] == 1
    assert summary["five_minute_window_count"] > 0

    expected = {
        "bronze_slot_events.jsonl",
        "silver_slot_events.jsonl",
        "gold_slot_performance_5min.jsonl",
        "dq_results.json",
        "model_metrics.json",
        "summary.json",
    }
    assert expected.issubset(path.name for path in tmp_path.iterdir())
    persisted = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert persisted["duplicate_count_removed"] == 1
