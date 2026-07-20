from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


class SnowflakeConfigurationError(RuntimeError):
    """Raised when required Snowflake connection settings are missing or unsafe."""


def build_connection_parameters(query_tag: str) -> dict[str, Any]:
    required = ("SNOWFLAKE_ACCOUNT_IDENTIFIER", "SNOWFLAKE_USER")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SnowflakeConfigurationError(f"Missing Snowflake settings: {', '.join(missing)}")

    parameters: dict[str, Any] = {
        "account": os.environ["SNOWFLAKE_ACCOUNT_IDENTIFIER"],
        "user": os.environ["SNOWFLAKE_USER"],
        "role": os.getenv("SNOWFLAKE_ROLE", "CASINO_ANALYST_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "CASINO_DEV_CORTEX_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "CASINO_DEV"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "OPS"),
        "session_parameters": {"QUERY_TAG": query_tag},
    }

    private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    if private_key_path:
        parameters.update(
            {
                "authenticator": "SNOWFLAKE_JWT",
                "private_key_file": private_key_path,
            }
        )
        passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
        if passphrase:
            parameters["private_key_file_pwd"] = passphrase
        return parameters

    password_allowed = os.getenv("ALLOW_SNOWFLAKE_PASSWORD_AUTH", "false").lower() == "true"
    password = os.getenv("SNOWFLAKE_PASSWORD")
    if password_allowed and password and password != "DO_NOT_COMMIT_REAL_PASSWORD":
        parameters["password"] = password
        return parameters

    raise SnowflakeConfigurationError(
        "Configure SNOWFLAKE_PRIVATE_KEY_PATH or explicitly enable temporary password auth"
    )


@contextmanager
def connection(query_tag: str) -> Iterator[Any]:
    # Imported lazily so credential-free local tests do not require the cloud package.
    import snowflake.connector  # type: ignore[import-not-found]

    conn = snowflake.connector.connect(**build_connection_parameters(query_tag))
    try:
        yield conn
    finally:
        conn.close()
