from pathlib import Path

import pytest

from services.common.snowflake import SnowflakeConfigurationError, build_connection_parameters


def test_key_pair_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    key_path = tmp_path / "rsa_key.p8"
    key_path.write_text("mock-key", encoding="utf-8")
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT_IDENTIFIER", "ORG-ACCOUNT")
    monkeypatch.setenv("SNOWFLAKE_USER", "KELLON_DEV")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PATH", str(key_path))
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "example-passphrase")

    parameters = build_connection_parameters("test.query")

    assert parameters["authenticator"] == "SNOWFLAKE_JWT"
    assert parameters["private_key_file"] == str(key_path)
    assert parameters["session_parameters"]["QUERY_TAG"] == "test.query"


def test_missing_authentication_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT_IDENTIFIER", "ORG-ACCOUNT")
    monkeypatch.setenv("SNOWFLAKE_USER", "KELLON_DEV")
    monkeypatch.delenv("SNOWFLAKE_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("SNOWFLAKE_PASSWORD", raising=False)
    monkeypatch.setenv("ALLOW_SNOWFLAKE_PASSWORD_AUTH", "false")

    with pytest.raises(SnowflakeConfigurationError):
        build_connection_parameters("test.query")
