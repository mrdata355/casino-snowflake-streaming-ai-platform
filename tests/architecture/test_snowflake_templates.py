from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.apply_snowflake import ordered_paths, render_environment_tokens

MOCK_ENV = {
    "PLATFORM_PREFIX": "CASINO",
    "ENVIRONMENT": "DEV",
    "RESOURCE_MONITOR": "CASINO_DEV_MONTHLY_RM",
    "MONTHLY_CREDIT_QUOTA": "25",
    "DATA_RETENTION_DAYS": "1",
    "DATABASE_NAME": "CASINO_DEV",
    "ADMIN_WAREHOUSE": "CASINO_DEV_ADMIN_WH",
    "INGEST_WAREHOUSE": "CASINO_DEV_INGEST_WH",
    "TRANSFORM_WAREHOUSE": "CASINO_DEV_TRANSFORM_WH",
    "FEATURE_WAREHOUSE": "CASINO_DEV_FEATURE_WH",
    "CORTEX_WAREHOUSE": "CASINO_DEV_CORTEX_WH",
    "ADMIN_WAREHOUSE_SIZE": "XSMALL",
    "INGEST_WAREHOUSE_SIZE": "XSMALL",
    "TRANSFORM_WAREHOUSE_SIZE": "XSMALL",
    "FEATURE_WAREHOUSE_SIZE": "XSMALL",
    "CORTEX_WAREHOUSE_SIZE": "XSMALL",
}


def set_mock_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in MOCK_ENV.items():
        monkeypatch.setenv(name, value)


def test_every_deployment_sql_template_renders(monkeypatch: pytest.MonkeyPatch) -> None:
    set_mock_environment(monkeypatch)
    for path in sorted(Path("snowflake/ddl").glob("*.sql")):
        rendered = render_environment_tokens(path.read_text(encoding="utf-8"))
        assert "${" not in rendered, path
        assert rendered.strip(), path


def test_semantic_model_renders_and_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    set_mock_environment(monkeypatch)
    rendered = render_environment_tokens(
        Path("snowflake/semantic/casino_semantic_model.yaml").read_text(encoding="utf-8")
    )
    document = yaml.safe_load(rendered)
    assert document["name"] == "CASINO_OPERATIONS"
    assert document["tables"][0]["base_table"]["database"] == "CASINO_DEV"


def test_ordered_paths_are_deterministic() -> None:
    paths = ordered_paths("snowflake/ddl", None)
    assert paths == sorted(paths)
    assert paths[0].name == "00_bootstrap.sql"
    assert paths[-1].name == "10_validation_views.sql"


def test_missing_template_value_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_NAME", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_NAME"):
        render_environment_tokens("USE DATABASE ${DATABASE_NAME};")
