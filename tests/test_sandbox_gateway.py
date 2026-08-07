import pytest

from services.sandbox_gateway.safety import SandboxPolicyError, split_sql, validate_python, validate_sql


def test_split_sql_preserves_semicolon_inside_string():
    statements = split_sql("SELECT 'a;b'; SELECT 2;")
    assert statements == ["SELECT 'a;b'", "SELECT 2"]


def test_schema_safe_profile_rejects_account_level_ddl():
    with pytest.raises(SandboxPolicyError):
        validate_sql("CREATE WAREHOUSE OPSREADY_WH WAREHOUSE_SIZE='XSMALL'", admin_lab=False)


def test_admin_profile_still_rejects_account_mutation():
    with pytest.raises(SandboxPolicyError):
        validate_sql("ALTER ACCOUNT SET SOME_PARAMETER=TRUE", admin_lab=True)


def test_normal_training_sql_is_allowed():
    assert validate_sql("CREATE TABLE t(id INT); INSERT INTO t VALUES (1); SELECT * FROM t", admin_lab=False)


def test_bounded_python_rejects_shell_and_secret_access():
    with pytest.raises(SandboxPolicyError):
        validate_python("import subprocess; subprocess.run(['bash'])")
    with pytest.raises(SandboxPolicyError):
        validate_python("dbutils.secrets.get('scope','key')")


def test_normal_spark_python_is_allowed():
    validate_python("df = spark.table('events').groupBy('property_id').count(); display(df)")
