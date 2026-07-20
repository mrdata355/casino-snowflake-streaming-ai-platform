from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException
from airflow.providers.common.sql.operators.sql import SQLCheckOperator
from airflow.providers.standard.operators.bash import BashOperator

DEFAULT_ARGS = {
    "owner": "casino-data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=45),
}


@dag(
    dag_id="casino_data_products",
    start_date=datetime(2026, 1, 1),
    schedule="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["casino", "snowflake", "dbt", "production"],
)
def casino_data_products():
    validate_source_freshness = SQLCheckOperator(
        task_id="validate_source_freshness",
        conn_id="snowflake_casino",
        sql="""
        SELECT DATEDIFF('minute', MAX(ingested_at), CURRENT_TIMESTAMP()) < 20
        FROM {{ var.value.snowflake_database }}.BRONZE.SLOT_EVENTS_RAW
        """,
    )

    dbt_build = BashOperator(
        task_id="dbt_build_changed_models",
        bash_command=(
            "cd /opt/airflow/repo/dbt && "
            "dbt build --target {{ var.value.dbt_target }} "
            "--select state:modified+ --defer --state /opt/airflow/dbt-state"
        ),
    )

    publication_gate = SQLCheckOperator(
        task_id="publication_gate",
        conn_id="snowflake_casino",
        sql="""
        SELECT COUNT_IF(status = 'FAIL') = 0
        FROM {{ var.value.snowflake_database }}.OPS.DQ_CHECK_RESULTS
        WHERE check_ts >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
          AND severity = 'CRITICAL'
        """,
    )

    @task
    def record_release(execution_date: str, git_sha: str) -> None:
        if not git_sha or len(git_sha) < 7:
            raise AirflowFailException("A valid deployment git SHA is required")
        print({"execution_date": execution_date, "git_sha": git_sha, "status": "PUBLISHED"})

    record = record_release(
        "{{ data_interval_end.isoformat() }}",
        "{{ var.value.deployment_git_sha }}",
    )
    validate_source_freshness >> dbt_build >> publication_gate >> record


casino_data_products()
