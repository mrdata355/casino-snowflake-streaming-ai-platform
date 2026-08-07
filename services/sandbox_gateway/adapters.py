from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .safety import SandboxPolicyError, validate_python, validate_sql


@dataclass
class AdapterResponse:
    state: str
    columns: list[str]
    rows: list[list[Any]]
    message: str
    statement_id: str | None = None
    elapsed_ms: int | None = None


class SnowflakeAdapter:
    platform = "snowflake"

    def __init__(self) -> None:
        self.account = os.getenv("SNOWFLAKE_ACCOUNT", "") or os.getenv("SNOWFLAKE_ACCOUNT_IDENTIFIER", "")
        self.user = os.getenv("SNOWFLAKE_USER", "")
        self.password = os.getenv("SNOWFLAKE_PASSWORD", "")
        self.private_key_file = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "")
        self.private_key_passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "")
        self.role = os.getenv("SNOWFLAKE_ROLE", "OPSREADY_TRAINER")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "OPSREADY_WH")
        self.database = os.getenv("SNOWFLAKE_TRAINING_DATABASE", "OPSREADY_TRAINING")
        self.allow_admin = os.getenv("OPSREADY_ALLOW_ADMIN_LABS", "false").lower() == "true"

    @property
    def available(self) -> bool:
        auth_ready = bool(self.password or self.private_key_file)
        return bool(self.account and self.user and auth_ready and self.warehouse and self.database)

    def _connect(self):
        import snowflake.connector

        kwargs: dict[str, Any] = {
            "account": self.account,
            "user": self.user,
            "role": self.role,
            "warehouse": self.warehouse,
            "database": self.database,
            "session_parameters": {"QUERY_TAG": "OPSREADY_SANDBOX"},
        }
        if self.private_key_file:
            kwargs.update(
                {
                    "authenticator": "SNOWFLAKE_JWT",
                    "private_key_file": self.private_key_file,
                }
            )
            if self.private_key_passphrase:
                kwargs["private_key_file_pwd"] = self.private_key_passphrase
        elif self.password:
            kwargs["password"] = self.password
        else:
            raise RuntimeError("Snowflake authentication is not configured.")
        return snowflake.connector.connect(**kwargs)

    def create_session(self, schema: str, admin_lab: bool) -> str:
        if admin_lab and not self.allow_admin:
            raise SandboxPolicyError("Snowflake admin labs are disabled on this gateway.")
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}" DATA_RETENTION_TIME_IN_DAYS = 0')
        return f"{self.database}.{schema}"

    def execute(self, schema: str, code: str, *, admin_lab: bool) -> AdapterResponse:
        statements = validate_sql(code, admin_lab=admin_lab)
        started = time.perf_counter()
        rows: list[list[Any]] = []
        columns: list[str] = []
        query_id: str | None = None
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(f'USE SCHEMA "{schema}"')
            for statement in statements:
                cur.execute(statement, timeout=60)
                query_id = getattr(cur, "sfqid", None)
                if cur.description:
                    columns = [d[0] for d in cur.description]
                    rows = [list(r) for r in cur.fetchmany(200)]
        elapsed = int((time.perf_counter() - started) * 1000)
        return AdapterResponse(
            state="SUCCEEDED",
            columns=columns,
            rows=rows,
            message=f"Executed {len(statements)} Snowflake statement(s) in isolated schema {schema}.",
            statement_id=query_id,
            elapsed_ms=elapsed,
        )

    def cleanup(self, schema: str) -> None:
        with self._connect() as conn:
            conn.cursor().execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


class DatabricksAdapter:
    platform = "databricks"

    def __init__(self) -> None:
        self.host = os.getenv("DATABRICKS_HOST", "").rstrip("/")
        self.token = os.getenv("DATABRICKS_TOKEN", "")
        self.warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID", "")
        self.catalog = os.getenv("DATABRICKS_TRAINING_CATALOG", "opsready_training")
        self.cluster_id = os.getenv("DATABRICKS_CLUSTER_ID", "")
        self.allow_admin = os.getenv("OPSREADY_ALLOW_ADMIN_LABS", "false").lower() == "true"

    @property
    def available(self) -> bool:
        return bool(self.host and self.token and self.warehouse_id and self.catalog)

    @property
    def python_available(self) -> bool:
        return bool(self.host and self.token and self.cluster_id and self.catalog)

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def _sql(self, statement: str, schema: str | None = None, wait_seconds: int = 10) -> AdapterResponse:
        payload: dict[str, Any] = {
            "warehouse_id": self.warehouse_id,
            "catalog": self.catalog,
            "statement": statement,
            "format": "JSON_ARRAY",
            "disposition": "INLINE",
            "wait_timeout": f"{wait_seconds}s",
            "on_wait_timeout": "CONTINUE",
        }
        if schema:
            payload["schema"] = schema
        started = time.perf_counter()
        with httpx.Client(timeout=35) as client:
            response = client.post(f"{self.host}/api/2.0/sql/statements", headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            statement_id = data.get("statement_id")
            state = data.get("status", {}).get("state", "UNKNOWN")
            deadline = time.time() + 60
            while statement_id and state in {"PENDING", "RUNNING"} and time.time() < deadline:
                time.sleep(1)
                response = client.get(f"{self.host}/api/2.0/sql/statements/{statement_id}", headers=self.headers)
                response.raise_for_status()
                data = response.json()
                state = data.get("status", {}).get("state", "UNKNOWN")
        if state != "SUCCEEDED":
            error = data.get("status", {}).get("error", {})
            raise RuntimeError(error.get("message") or f"Databricks statement ended in state {state}.")
        manifest = data.get("manifest", {})
        cols = [c.get("name", "") for c in manifest.get("schema", {}).get("columns", [])]
        rows = data.get("result", {}).get("data_array", []) or []
        elapsed = int((time.perf_counter() - started) * 1000)
        location = f"{self.catalog}.{schema}" if schema else self.catalog
        return AdapterResponse(
            state=state,
            columns=cols,
            rows=rows[:200],
            message=f"Databricks SQL statement succeeded in {location}.",
            statement_id=statement_id,
            elapsed_ms=elapsed,
        )

    def create_session(self, schema: str, admin_lab: bool) -> str:
        if admin_lab and not self.allow_admin:
            raise SandboxPolicyError("Databricks admin labs are disabled on this gateway.")
        self._sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{schema}")
        return f"{self.catalog}.{schema}"

    def execute_sql(self, schema: str, code: str, *, admin_lab: bool) -> AdapterResponse:
        statements = validate_sql(code, admin_lab=admin_lab)
        result = AdapterResponse("SUCCEEDED", [], [], "")
        for statement in statements:
            result = self._sql(statement, schema)
        result.message = f"Executed {len(statements)} Databricks SQL statement(s) in {self.catalog}.{schema}."
        return result

    def execute_python(self, schema: str, code: str) -> AdapterResponse:
        if not self.python_available:
            raise RuntimeError("DATABRICKS_CLUSTER_ID is not configured for bounded Python execution.")
        validate_python(code)
        started = time.perf_counter()
        with httpx.Client(timeout=35) as client:
            create = client.post(
                f"{self.host}/api/1.2/contexts/create",
                headers=self.headers,
                json={"clusterId": self.cluster_id, "language": "python"},
            )
            create.raise_for_status()
            context_id = create.json()["id"]
            try:
                command = client.post(
                    f"{self.host}/api/1.2/commands/execute",
                    headers=self.headers,
                    json={
                        "clusterId": self.cluster_id,
                        "contextId": context_id,
                        "language": "python",
                        "command": f"spark.sql('USE CATALOG {self.catalog}')\nspark.sql('USE SCHEMA {schema}')\n" + code,
                    },
                )
                command.raise_for_status()
                command_id = command.json()["id"]
                deadline = time.time() + 90
                status: dict[str, Any] = {}
                while time.time() < deadline:
                    status_r = client.get(
                        f"{self.host}/api/1.2/commands/status",
                        headers=self.headers,
                        params={
                            "clusterId": self.cluster_id,
                            "contextId": context_id,
                            "commandId": command_id,
                        },
                    )
                    status_r.raise_for_status()
                    status = status_r.json()
                    if status.get("status") in {"Finished", "Error", "Cancelled"}:
                        break
                    time.sleep(1)
                if status.get("status") != "Finished":
                    raise RuntimeError(status.get("results", {}).get("cause") or "Databricks Python command did not finish successfully.")
                results = status.get("results", {})
                text = results.get("data") or results.get("summary") or "Python command completed."
            finally:
                try:
                    client.post(
                        f"{self.host}/api/1.2/contexts/destroy",
                        headers=self.headers,
                        json={"clusterId": self.cluster_id, "contextId": context_id},
                    )
                except Exception:
                    pass
        return AdapterResponse(
            state="SUCCEEDED",
            columns=["output"],
            rows=[[str(text)[:20_000]]],
            message=f"Databricks Python executed on bounded classic cluster context in {self.catalog}.{schema}.",
            statement_id=command_id,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
        )

    def cleanup(self, schema: str) -> None:
        self._sql(f"DROP SCHEMA IF EXISTS {self.catalog}.{schema} CASCADE")


class SqlServerAdapter:
    platform = "sqlserver"

    def __init__(self) -> None:
        self.host = os.getenv("SQLSERVER_HOST", "")
        self.port = int(os.getenv("SQLSERVER_PORT", "1433"))
        self.user = os.getenv("SQLSERVER_USER", "sa")
        self.password = os.getenv("SQLSERVER_PASSWORD", "")
        self.driver = os.getenv("SQLSERVER_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
        self.allow_admin = os.getenv("OPSREADY_ALLOW_ADMIN_LABS", "false").lower() == "true"

    @property
    def available(self) -> bool:
        return bool(self.host and self.password)

    def _connect(self, database: str = "master"):
        import pyodbc

        cs = (
            f"DRIVER={{{self.driver}}};SERVER={self.host},{self.port};DATABASE={database};"
            f"UID={self.user};PWD={self.password};Encrypt=yes;TrustServerCertificate=yes;"
        )
        return pyodbc.connect(cs, timeout=10, autocommit=True)

    def create_session(self, database: str, admin_lab: bool) -> str:
        if admin_lab and not self.allow_admin:
            raise SandboxPolicyError("SQL Server admin labs are disabled on this gateway.")
        with self._connect("master") as conn:
            cur = conn.cursor()
            cur.execute(f"IF DB_ID(?) IS NULL EXEC('CREATE DATABASE [{database}]')", database)
        return database

    def execute(self, database: str, code: str, *, admin_lab: bool) -> AdapterResponse:
        statements = validate_sql(code, admin_lab=admin_lab)
        started = time.perf_counter()
        columns: list[str] = []
        rows: list[list[Any]] = []
        with self._connect(database) as conn:
            cur = conn.cursor()
            for statement in statements:
                cur.execute(statement)
                if cur.description:
                    columns = [d[0] for d in cur.description]
                    rows = [list(r) for r in cur.fetchmany(200)]
        return AdapterResponse(
            state="SUCCEEDED",
            columns=columns,
            rows=rows,
            message=f"Executed {len(statements)} SQL Server statement(s) in isolated database {database}.",
            elapsed_ms=int((time.perf_counter() - started) * 1000),
        )

    def cleanup(self, database: str) -> None:
        with self._connect("master") as conn:
            cur = conn.cursor()
            cur.execute(
                f"IF DB_ID(?) IS NOT NULL BEGIN ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{database}]; END",
                database,
            )
