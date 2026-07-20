from pathlib import Path

REQUIRED_PATHS = [
    "snowflake/ddl",
    "dbt/models/staging",
    "dbt/models/silver",
    "dbt/models/gold",
    "dbt/models/features",
    "spark/jobs",
    "airflow/dags",
    "terraform/environments",
    "services/feature_api",
    "ml",
    "contracts",
    "observability/sql",
]


def test_required_production_domains_exist() -> None:
    missing = [path for path in REQUIRED_PATHS if not Path(path).exists()]
    assert not missing, f"Missing production domains: {missing}"
