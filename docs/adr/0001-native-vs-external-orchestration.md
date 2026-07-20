# ADR 0001: Snowflake-native and external orchestration

## Status
Accepted

## Decision
Use Snowflake Streams, Tasks, and Dynamic Tables for transformations whose source, state, and target remain entirely in Snowflake. Use Airflow for cross-system dependencies, bounded backfills, ML workflows, publication gates, and activities requiring external APIs or infrastructure.

## Consequences
This avoids unnecessary external orchestration latency for native workloads while preserving centralized operational control for multi-platform workflows. Every workflow must have one authoritative scheduler; the same dependency may not be independently scheduled in both Snowflake and Airflow.
