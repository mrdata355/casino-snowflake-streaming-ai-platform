from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from typing import Any

DECIMAL_GB = 1_000_000_000
DECIMAL_TB = 1_000_000_000_000
DEFAULT_PAYLOAD_BYTES = 1_024
DEFAULT_TARGET_GB = 10
VALID_TARGETS_GB = (10, 100, 1_000)
_IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")


@dataclass(frozen=True)
class BenchmarkPlan:
    run_id: str
    target_gb: int
    target_bytes: int
    payload_bytes_per_row: int
    row_count: int
    duplicate_every: int
    malformed_every: int
    negative_amount_every: int

    @property
    def logical_payload_tb(self) -> float:
        return self.target_bytes / DECIMAL_TB

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"logical_payload_tb": self.logical_payload_tb}


@dataclass(frozen=True)
class Projection:
    measured_tb: float
    target_tb: float
    elapsed_seconds: float
    projected_seconds: float
    credits: float | None
    projected_credits: float | None
    throughput_gb_per_minute: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_identifier(value: str, field_name: str = "identifier") -> str:
    normalized = value.strip().upper().replace("-", "_")
    if not _IDENTIFIER.fullmatch(normalized):
        raise ValueError(f"{field_name} must contain only letters, digits, and underscores")
    return normalized


def build_plan(
    *,
    run_id: str,
    target_gb: int = DEFAULT_TARGET_GB,
    payload_bytes_per_row: int = DEFAULT_PAYLOAD_BYTES,
    duplicate_every: int = 1_000,
    malformed_every: int = 2_000,
    negative_amount_every: int = 5_000,
) -> BenchmarkPlan:
    if target_gb <= 0:
        raise ValueError("target_gb must be positive")
    if payload_bytes_per_row < 128:
        raise ValueError("payload_bytes_per_row must be at least 128")
    for name, value in {
        "duplicate_every": duplicate_every,
        "malformed_every": malformed_every,
        "negative_amount_every": negative_amount_every,
    }.items():
        if value < 2:
            raise ValueError(f"{name} must be at least 2")

    normalized_run_id = normalize_identifier(run_id, "run_id")
    target_bytes = target_gb * DECIMAL_GB
    row_count = math.ceil(target_bytes / payload_bytes_per_row)
    return BenchmarkPlan(
        run_id=normalized_run_id,
        target_gb=target_gb,
        target_bytes=target_bytes,
        payload_bytes_per_row=payload_bytes_per_row,
        row_count=row_count,
        duplicate_every=duplicate_every,
        malformed_every=malformed_every,
        negative_amount_every=negative_amount_every,
    )


def project_scale(
    *,
    measured_tb: float,
    elapsed_seconds: float,
    target_tb: float = 10.0,
    credits: float | None = None,
) -> Projection:
    if measured_tb <= 0:
        raise ValueError("measured_tb must be positive")
    if elapsed_seconds <= 0:
        raise ValueError("elapsed_seconds must be positive")
    if target_tb <= 0:
        raise ValueError("target_tb must be positive")
    if credits is not None and credits < 0:
        raise ValueError("credits cannot be negative")

    scale_factor = target_tb / measured_tb
    projected_seconds = elapsed_seconds * scale_factor
    projected_credits = None if credits is None else credits * scale_factor
    throughput_gb_per_minute = measured_tb * 1_000 * 60 / elapsed_seconds
    return Projection(
        measured_tb=measured_tb,
        target_tb=target_tb,
        elapsed_seconds=elapsed_seconds,
        projected_seconds=projected_seconds,
        credits=credits,
        projected_credits=projected_credits,
        throughput_gb_per_minute=throughput_gb_per_minute,
    )


def render_statements(
    plan: BenchmarkPlan,
    *,
    database: str,
    schema: str = "BENCHMARK",
    warehouse: str | None = None,
    retain_data: bool = False,
) -> list[tuple[str, str]]:
    database_name = normalize_identifier(database, "database")
    schema_name = normalize_identifier(schema, "schema")
    warehouse_name = normalize_identifier(warehouse, "warehouse") if warehouse else None
    run_suffix = plan.run_id[:64]
    raw_table = f"SLOT_EVENTS_{run_suffix}"
    aggregate_table = f"SLOT_HOURLY_{run_suffix}"
    fully_qualified_raw = f"{database_name}.{schema_name}.{raw_table}"
    fully_qualified_aggregate = f"{database_name}.{schema_name}.{aggregate_table}"
    query_tag = f"CASINO_SCALE_BENCHMARK:{plan.run_id}"

    statements: list[tuple[str, str]] = []
    if warehouse_name:
        statements.append(("use_warehouse", f"USE WAREHOUSE {warehouse_name}"))
    statements.extend(
        [
            ("set_query_tag", f"ALTER SESSION SET QUERY_TAG = '{query_tag}'"),
            ("create_schema", f"CREATE SCHEMA IF NOT EXISTS {database_name}.{schema_name}"),
            (
                "create_raw_table",
                f"""CREATE OR REPLACE TRANSIENT TABLE {fully_qualified_raw} (
    synthetic_sequence NUMBER NOT NULL,
    event_id VARCHAR NOT NULL,
    event_time TIMESTAMP_NTZ NOT NULL,
    property_id VARCHAR NOT NULL,
    location_id VARCHAR NOT NULL,
    machine_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    amount NUMBER(18, 2) NOT NULL,
    payload_padding VARCHAR NOT NULL,
    ingested_at TIMESTAMP_NTZ NOT NULL
) DATA_RETENTION_TIME_IN_DAYS = 0""",
            ),
            (
                "generate_data",
                f"""INSERT INTO {fully_qualified_raw}
WITH generated AS (
    SELECT SEQ8() AS seq
    FROM TABLE(GENERATOR(ROWCOUNT => {plan.row_count}))
)
SELECT
    seq AS synthetic_sequence,
    SHA2_HEX(
        TO_VARCHAR(IFF(seq > 0 AND MOD(seq, {plan.duplicate_every}) = 0, seq - 1, seq)),
        256
    ) AS event_id,
    DATEADD('millisecond', MOD(seq, 86_400_000), '2026-01-01'::TIMESTAMP_NTZ) AS event_time,
    'PROPERTY_' || LPAD(MOD(seq, 8)::VARCHAR, 2, '0') AS property_id,
    'FLOOR_' || LPAD(MOD(seq, 32)::VARCHAR, 2, '0') AS location_id,
    'SLOT_' || LPAD(MOD(seq, 50_000)::VARCHAR, 6, '0') AS machine_id,
    IFF(MOD(seq, {plan.malformed_every}) = 0, 'UNKNOWN',
        CASE MOD(seq, 6)
            WHEN 0 THEN 'SPIN'
            WHEN 1 THEN 'COIN_IN'
            WHEN 2 THEN 'COIN_OUT'
            WHEN 3 THEN 'JACKPOT'
            WHEN 4 THEN 'FAULT'
            ELSE 'HEARTBEAT'
        END
    ) AS event_type,
    IFF(MOD(seq, {plan.negative_amount_every}) = 0, -1,
        ROUND(UNIFORM(0, 15000, RANDOM()) / 100, 2)
    ) AS amount,
    RANDSTR({plan.payload_bytes_per_row}, RANDOM()) AS payload_padding,
    CURRENT_TIMESTAMP() AS ingested_at
FROM generated""",
            ),
            (
                "build_deduplicated_aggregate",
                f"""CREATE OR REPLACE TRANSIENT TABLE {fully_qualified_aggregate} AS
WITH valid AS (
    SELECT *
    FROM {fully_qualified_raw}
    WHERE event_type IN ('SPIN', 'COIN_IN', 'COIN_OUT', 'JACKPOT', 'FAULT', 'HEARTBEAT')
      AND amount >= 0
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY event_id
        ORDER BY ingested_at DESC, synthetic_sequence DESC
    ) = 1
),
aggregated AS (
    SELECT
        property_id,
        location_id,
        DATE_TRUNC('hour', event_time) AS event_hour,
        COUNT(*) AS event_count,
        SUM(IFF(event_type = 'COIN_IN', amount, 0)) AS coin_in,
        SUM(IFF(event_type = 'COIN_OUT', amount, 0)) AS coin_out,
        SUM(IFF(event_type = 'JACKPOT', amount, 0)) AS jackpot_amount,
        SUM(IFF(event_type = 'FAULT', 1, 0)) AS fault_count
    FROM valid
    GROUP BY 1, 2, 3
)
SELECT
    *,
    coin_in - coin_out - jackpot_amount AS net_gaming_revenue
FROM aggregated""",
            ),
            (
                "validate_results",
                f"""SELECT
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT event_id) AS distinct_event_ids,
    COUNT_IF(event_type = 'UNKNOWN') AS malformed_rows,
    COUNT_IF(amount < 0) AS negative_amount_rows,
    (SELECT COUNT(*) FROM {fully_qualified_aggregate}) AS aggregate_rows
FROM {fully_qualified_raw}""",
            ),
            (
                "show_raw_table",
                f"SHOW TABLES LIKE '{raw_table}' IN SCHEMA {database_name}.{schema_name}",
            ),
        ]
    )
    if not retain_data:
        statements.extend(
            [
                ("drop_aggregate", f"DROP TABLE IF EXISTS {fully_qualified_aggregate}"),
                ("drop_raw", f"DROP TABLE IF EXISTS {fully_qualified_raw}"),
            ]
        )
    return statements
