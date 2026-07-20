from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from local_demo.generator import generate_slot_events
from local_demo.ml_baseline import mean_absolute_error, train_mean_baseline
from local_demo.quality import validate_events
from local_demo.transform import aggregate_slot_performance, deduplicate_latest


def run_demo(output_dir: Path, count: int = 250, seed: int = 355) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_events = generate_slot_events(count=count, seed=seed)
    quality_results = validate_events(raw_events)
    clean_events = deduplicate_latest(raw_events)
    windows = aggregate_slot_performance(clean_events)

    training_rows = [
        {
            "coin_in": float(window.coin_in),
            "fault_count": float(window.fault_count),
            "next_30d_value": max(float(window.net_gaming_revenue), 0.0),
        }
        for window in windows
    ]
    model = train_mean_baseline(training_rows, target="next_30d_value")
    predictions = model.predict(training_rows)
    mae = mean_absolute_error(
        [row["next_30d_value"] for row in training_rows],
        predictions,
    )

    _write_jsonl(output_dir / "bronze_slot_events.jsonl", [event.to_dict() for event in raw_events])
    _write_jsonl(output_dir / "silver_slot_events.jsonl", [event.to_dict() for event in clean_events])
    _write_jsonl(output_dir / "gold_slot_performance_5min.jsonl", [row.to_dict() for row in windows])
    (output_dir / "dq_results.json").write_text(
        json.dumps([asdict(result) for result in quality_results], indent=2),
        encoding="utf-8",
    )
    (output_dir / "model_metrics.json").write_text(
        json.dumps({"model": "mean-baseline", "validation_mae": mae}, indent=2),
        encoding="utf-8",
    )

    summary = {
        "raw_event_count": len(raw_events),
        "deduplicated_event_count": len(clean_events),
        "duplicate_count_removed": len(raw_events) - len(clean_events),
        "five_minute_window_count": len(windows),
        "quality_failed_checks": sum(result.status == "FAIL" for result in quality_results),
        "validation_mae": round(mae, 4),
        "output_dir": str(output_dir),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
