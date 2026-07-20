from __future__ import annotations

import sys

from services.common.snowflake import SnowflakeConfigurationError, build_connection_parameters


def main() -> int:
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


if __name__ == "__main__":
    sys.exit(main())
