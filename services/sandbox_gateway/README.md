# OpsReady isolated execution gateway

This service converts eligible OpsReady V6 exercises from pattern simulation into bounded real execution against dedicated training resources.

## Security model

The browser never receives Snowflake, Databricks, or SQL Server credentials. It stores only the gateway URL and short-lived sandbox session IDs. The gateway creates one isolated namespace per learner session, applies a statement policy before execution, limits response size, and exposes explicit cleanup.

The default profile is **schema-safe**. Account-level actions such as creating warehouses, roles, resource monitors, databases, or catalogs are denied. Those exercises remain simulated unless the gateway runs against a disposable training account/workspace and `OPSREADY_ALLOW_ADMIN_LABS=true` is deliberately enabled.

Never point this gateway at production credentials or production namespaces.

## Local SQL Server sandbox

Set a strong local-only password in your shell, then start the sandbox profile:

```bash
export MSSQL_SA_PASSWORD='set-a-strong-local-password'
docker compose --profile sandbox up --build
```

The gateway listens on `http://localhost:8090`. SQL Server sessions create a disposable database named `OpsReady_<token>` and drop it when the session is cleaned up.

When OpsReady itself is opened from an HTTPS site, the browser cannot call an HTTP localhost gateway because of mixed-content rules. For public-site live execution, deploy this gateway behind HTTPS on a container service and place only the HTTPS gateway URL in the V6 Real Sandbox panel.

## Snowflake training connection

Configure a dedicated training database, small warehouse, and least-privilege training role. The gateway supports password authentication for local testing and key-pair authentication when the private-key variables are configured.

Expected variables include:

```text
SNOWFLAKE_ACCOUNT or SNOWFLAKE_ACCOUNT_IDENTIFIER
SNOWFLAKE_USER
SNOWFLAKE_ROLE=OPSREADY_TRAINER
SNOWFLAKE_WAREHOUSE=OPSREADY_WH
SNOWFLAKE_TRAINING_DATABASE=OPSREADY_TRAINING
SNOWFLAKE_PASSWORD                         # optional local path
SNOWFLAKE_PRIVATE_KEY_PATH                 # preferred where available
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE           # if the key is encrypted
```

The configured role needs only the privileges required to create/drop schemas inside the training database and operate the allowed objects for schema-safe labs. Leave admin labs disabled for ordinary training.

## Databricks training connection

Configure a dedicated training catalog and SQL warehouse. SQL exercises use the Databricks SQL Statement Execution API. Optional Python execution requires a configured classic all-purpose training cluster for the bounded Command Execution adapter.

```text
DATABRICKS_HOST
DATABRICKS_TOKEN
DATABRICKS_SQL_WAREHOUSE_ID
DATABRICKS_TRAINING_CATALOG=opsready_training
DATABRICKS_CLUSTER_ID                      # optional Python mode
```

Use a service principal or training identity with access limited to the training catalog/workspace resources. Shell commands, direct secret access, and outbound-network helpers are blocked by the Python policy layer.

## Gateway endpoints

```text
GET    /health
GET    /capabilities
POST   /sessions
POST   /execute
DELETE /sessions/{session_id}
```

A normal flow is: create session → execute one or more eligible tasks → capture evidence → delete session. Sessions also have a TTL and cleanup is requested when an expired session is encountered.

## What remains simulated

Some V6 exercises intentionally remain simulations unless a dedicated admin training environment exists. Examples include account-level Snowflake warehouse/role provisioning, Databricks bundle/CLI deployment, and other operations that would require broad control-plane authority. The UI labels these instead of silently pretending they were executed.
