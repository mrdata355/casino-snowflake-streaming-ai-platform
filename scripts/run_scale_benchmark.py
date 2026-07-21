from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmarks.scale import VALID_TARGETS_GB, build_plan, project_scale, render_statements


def default_run_id(target_gb: int) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"SCALE_{target_gb}GB_{timestamp}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def render_sql(statements: list[tuple[str, str]]) -> str:
    blocks = [f"-- {name}\n{sql.rstrip(';')};" for name, sql in statements]
    return "\n\n".join(blocks) + "\n"


def execute_statement(conn: Any, name: str, sql: str) -> dict[str, Any]:
    cursor = conn.cursor()
    step_start = time.perf_counter()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall() if cursor.description else []
        columns = [item[0].lower() for item in cursor.description or []]
        return {
            "name": name,
            "status": "succeeded",
            "query_id": getattr(cursor, "sfqid", None),
            "elapsed_seconds": time.perf_counter() - step_start,
            "rowcount": cursor.rowcount,
            "columns": columns,
            "rows": [dict(zip(columns, row, strict=True)) for row in rows[:20]],
        }
    finally:
        cursor.close()


def execute_benchmark(
    statements: list[tuple[str, str]],
    *,
    query_tag: str,
    credits_per_hour: float | None,
) -> dict[str, Any]:
    from services.common.snowflake import connection

    primary = [(name, sql) for name, sql in statements if not name.startswith("drop_")]
    cleanup = [(name, sql) for name, sql in statements if name.startswith("drop_")]
    statement_results: list[dict[str, Any]] = []
    execution_error: str | None = None
    cleanup_errors: list[str] = []
    started_at = datetime.now(UTC)
    wall_start = time.perf_counter()

    with connection(query_tag) as conn:
        try:
            for name, sql in primary:
                try:
                    statement_results.append(execute_statement(conn, name, sql))
                except Exception as exc:  # Snowflake exceptions vary by connector version.
                    execution_error = f"{type(exc).__name__}: {exc}"
                    statement_results.append(
                        {
                            "name": name,
                            "status": "failed",
                            "elapsed_seconds": None,
                            "error": execution_error,
                        }
                    )
                    break
        finally:
            for name, sql in cleanup:
                try:
                    statement_results.append(execute_statement(conn, name, sql))
                except Exception as exc:  # Cleanup must continue after an individual failure.
                    message = f"{name}: {type(exc).__name__}: {exc}"
                    cleanup_errors.append(message)
                    statement_results.append(
                        {
                            "name": name,
                            "status": "failed",
                            "elapsed_seconds": None,
                            "error": message,
                        }
                    )
            conn.commit()

    elapsed_seconds = time.perf_counter() - wall_start
    finished_at = datetime.now(UTC)
    estimated_credits = None
    if credits_per_hour is not None:
        estimated_credits = credits_per_hour * elapsed_seconds / 3_600
    return {
        "success": execution_error is None and not cleanup_errors,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "credits_per_hour": credits_per_hour,
        "estimated_credits": estimated_credits,
        "execution_error": execution_error,
        "cleanup_errors": cleanup_errors,
        "statements": statement_results,
    }


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-gb", type=int, default=10)
    parser.add_argument("--payload-bytes", type=int, default=1_024)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--database", default=os.getenv("SNOWFLAKE_DATABASE", "CASINO_DEV"))
    parser.add_argument("--schema", default="BENCHMARK")
    parser.add_argument("--warehouse", default=os.getenv("SNOWFLAKE_WAREHOUSE"))
    parser.add_argument("--retain-data", action="store_true")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan, render, or execute Snowflake scale benchmarks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Print a credential-free benchmark plan")
    add_common_arguments(plan_parser)

    render_parser = subparsers.add_parser("render", help="Render executable Snowflake SQL")
    add_common_arguments(render_parser)
    render_parser.add_argument("--out", type=Path, required=True)

    execute_parser = subparsers.add_parser("execute", help="Execute the controlled Snowflake benchmark")
    add_common_arguments(execute_parser)
    execute_parser.add_argument("--out", type=Path, required=True)
    execute_parser.add_argument("--confirm-scale-run", action="store_true")
    execute_parser.add_argument("--credits-per-hour", type=float, default=None)
    execute_parser.add_argument("--project-to-tb", type=float, default=10.0)

    args = parser.parse_args()
    run_id = args.run_id or default_run_id(args.target_gb)
    plan = build_plan(
        run_id=run_id,
        target_gb=args.target_gb,
        payload_bytes_per_row=args.payload_bytes,
    )
    statements = render_statements(
        plan,
        database=args.database,
        schema=args.schema,
        warehouse=args.warehouse,
        retain_data=args.retain_data,
    )

    if args.command == "plan":
        payload = plan.to_dict() | {
            "supported_staged_targets_gb": list(VALID_TARGETS_GB),
            "note": "Target size is logical random payload before Snowflake compression.",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    if args.command == "render":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(render_sql(statements), encoding="utf-8")
        print(f"rendered {len(statements)} statements to {args.out}")
        return

    if not args.confirm_scale_run:
        parser.error("execute requires --confirm-scale-run")
    if args.credits_per_hour is not None and args.credits_per_hour < 0:
        parser.error("credits-per-hour cannot be negative")
    if args.target_gb not in VALID_TARGETS_GB:
        supported = ", ".join(map(str, VALID_TARGETS_GB))
        parser.error(f"execute target must be one of: {supported} GB")

    query_tag = f"CASINO_SCALE_BENCHMARK:{plan.run_id}"
    result = execute_benchmark(
        statements,
        query_tag=query_tag,
        credits_per_hour=args.credits_per_hour,
    )
    projection = None
    if result["success"]:
        projection = project_scale(
            measured_tb=plan.logical_payload_tb,
            elapsed_seconds=result["elapsed_seconds"],
            target_tb=args.project_to_tb,
            credits=result["estimated_credits"],
        )
    report = {
        "plan": plan.to_dict(),
        "execution": result,
        "projection": None if projection is None else projection.to_dict(),
        "warnings": [
            "Logical payload size is not the same as compressed Snowflake storage.",
            "Credit estimates are valid only when the benchmark warehouse is isolated.",
            "The 10 TB projection is linear and must be labeled as a projection, not a measured run.",
        ],
    }
    write_json(args.out, report)
    print(f"wrote benchmark report to {args.out}")
    if not result["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
