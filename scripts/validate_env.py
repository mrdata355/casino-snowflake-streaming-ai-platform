from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

from scripts.apply_snowflake import render_environment_tokens
from services.common.snowflake import SnowflakeConfigurationError, build_connection_parameters

TEMPLATE_DEFAULTS = {
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


def validate_templates() -> int:
    for name, value in TEMPLATE_DEFAULTS.items():
        os.environ.setdefault(name, value)

    sql_files = sorted(Path("snowflake/ddl").glob("*.sql"))
    if not sql_files:
        print("INVALID: no Snowflake DDL templates found")
        return 1
    for path in sql_files:
        rendered = render_environment_tokens(path.read_text(encoding="utf-8"))
        if "${" in rendered or not rendered.strip():
            print(f"INVALID: unresolved or empty Snowflake template: {path}")
            return 1

    contract_files = sorted(Path("contracts").glob("*.schema.json"))
    for path in contract_files:
        json.loads(path.read_text(encoding="utf-8"))

    semantic_files = sorted(Path("snowflake/semantic").glob("*.yml")) + sorted(
        Path("snowflake/semantic").glob("*.yaml")
    )
    for path in semantic_files:
        rendered = render_environment_tokens(path.read_text(encoding="utf-8"))
        document = yaml.safe_load(rendered)
        if not isinstance(document, dict):
            print(f"INVALID: semantic definition is not a mapping: {path}")
            return 1

    print(
        "VALID: "
        f"{len(sql_files)} Snowflake templates, "
        f"{len(contract_files)} contracts, and "
        f"{len(semantic_files)} semantic definitions"
    )
    return 0


def validate_connection_settings() -> int:
    try:
        parameters = build_connection_parameters("validation.environment")
    except SnowflakeConfigurationError as exc:
        print(f"INVALID: {exc}")
        return 1

    safe_fields = {
        key: ("<configured>" if "key" in key or "password" in key else value)
        for key, value in parameters.items()
        if key != "session_parameters"
    }
    print(f"VALID: Snowflake connection settings are present: {safe_fields}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate credential-free templates or local credentials")
    parser.add_argument("--template-mode", action="store_true")
    args = parser.parse_args()
    return validate_templates() if args.template_mode else validate_connection_settings()


if __name__ == "__main__":
    sys.exit(main())
