from pathlib import Path

REQUIRED_PLATFORM_FILES = [
    "docker-compose.yml",
    "spark/jobs/slot_stream.py",
    "airflow/dags/casino_data_products.py",
    "dbt/dbt_project.yml",
    "dbt/models/gold/fact_slot_performance_5min.sql",
    "ml/training/train_player_value.py",
    "terraform/main.tf",
    "observability/sql/platform_health.sql",
    ".github/workflows/ci.yml",
    ".github/workflows/deploy-snowflake.yml",
    "docs/runbook.md",
]


def test_production_modules_are_present() -> None:
    missing = [path for path in REQUIRED_PLATFORM_FILES if not Path(path).is_file()]
    assert missing == []


def test_bootstrap_transport_files_are_removed() -> None:
    assert not Path("bootstrap").exists()
    assert not Path(".github/workflows/bootstrap-platform.yml").exists()
