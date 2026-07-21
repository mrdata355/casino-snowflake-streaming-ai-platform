from __future__ import annotations

import math

import pytest

from benchmarks.scale import DECIMAL_GB, build_plan, normalize_identifier, project_scale, render_statements


def test_build_plan_calculates_rows_from_logical_payload() -> None:
    plan = build_plan(run_id="scale-10gb", target_gb=10, payload_bytes_per_row=1_024)

    assert plan.run_id == "SCALE_10GB"
    assert plan.target_bytes == 10 * DECIMAL_GB
    assert plan.row_count == math.ceil(10 * DECIMAL_GB / 1_024)


def test_project_scale_uses_measured_results() -> None:
    projection = project_scale(measured_tb=1.0, elapsed_seconds=600, target_tb=10.0, credits=4.0)

    assert projection.projected_seconds == 6_000
    assert projection.projected_credits == 40
    assert projection.throughput_gb_per_minute == 100


def test_render_statements_uses_transient_tables_and_cleanup() -> None:
    plan = build_plan(run_id="scale_10gb", target_gb=10)
    statements = render_statements(plan, database="casino_dev", warehouse="casino_dev_transform_wh")
    rendered = "\n".join(sql for _, sql in statements)

    assert "CREATE OR REPLACE TRANSIENT TABLE CASINO_DEV.BENCHMARK.SLOT_EVENTS_SCALE_10GB" in rendered
    assert f"GENERATOR(ROWCOUNT => {plan.row_count})" in rendered
    assert "DROP TABLE IF EXISTS CASINO_DEV.BENCHMARK.SLOT_EVENTS_SCALE_10GB" in rendered
    assert "CASINO_SCALE_BENCHMARK:SCALE_10GB" in rendered
    assert "),\naggregated AS (" in rendered


def test_retain_data_skips_cleanup() -> None:
    plan = build_plan(run_id="scale_100gb", target_gb=100)
    names = [name for name, _ in render_statements(plan, database="casino_dev", retain_data=True)]

    assert "drop_raw" not in names
    assert "drop_aggregate" not in names


@pytest.mark.parametrize("value", ["bad.name", "1BAD", "BAD NAME", ""])
def test_identifier_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_identifier(value)
