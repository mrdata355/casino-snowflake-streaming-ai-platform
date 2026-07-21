# Getting Started

This guide covers local validation, optional cloud dependencies, Snowflake configuration, and deployment.

## 1. Prerequisites

Install:

- Git
- Python 3.11, 3.12, or 3.13
- Docker Desktop with Docker Compose
- Terraform

Verify the toolchain:

```bash
git --version
python3 --version
docker --version
docker compose version
terraform version
```

## 2. Clone and bootstrap

```bash
git clone https://github.com/mrdata355/casino-snowflake-streaming-ai-platform.git
cd casino-snowflake-streaming-ai-platform
git checkout main
git pull
make bootstrap
```

`make bootstrap` creates `.venv`, installs credential-free development dependencies, and copies `.env.example` to `.env` without overwriting an existing file.

Activate the environment when running commands manually:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Run the local pipeline

```bash
make local-demo
```

The local pipeline generates synthetic slot events, validates contracts, processes duplicates and malformed records, builds business aggregates, and produces a baseline anomaly score. Output is written to:

```text
build/demo/
```

Run the full validation gate:

```bash
make validate
make terraform-check
```

The validation gate includes linting, Python compilation, contract tests, architecture tests, deterministic unit and integration tests, reconciliation tests, coverage reporting, and Terraform validation.

## 4. Start local services

```bash
make local-up
make create-topics
```

Generate sample events:

```bash
python -m scripts.generate_sample_events --count 100 --out /tmp/slot_events.jsonl
```

Stop and remove the containers:

```bash
make local-down
```

The local stack includes Kafka, PostgreSQL, MLflow, and the optional feature API.

## 5. Configure Snowflake

Keep `.env` local. It is ignored by Git and must not be committed.

Set the following variables:

```text
SNOWFLAKE_ACCOUNT_IDENTIFIER
SNOWFLAKE_USER
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
SNOWFLAKE_PRIVATE_KEY_PATH
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
```

Encrypted PKCS#8 key-pair authentication is the preferred local authentication method. The private key must remain outside the repository.

Password authentication is disabled by default through:

```text
ALLOW_SNOWFLAKE_PASSWORD_AUTH=false
```

Load the environment in Bash:

```bash
set -a
source .env
set +a
```

Install optional cloud dependencies and validate the configuration:

```bash
make install-cloud
python -m scripts.validate_env
make cloud-smoke
```

The environment validator checks required values without printing secrets.

## 6. Configure GitHub Environments

Create these repository environments under **Settings → Environments**:

- `dev`
- `qa`
- `prod`

Add these environment secrets:

```text
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PRIVATE_KEY
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
```

Add these environment variables:

```text
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
```

Store the complete private-key text as a multiline secret. Configure required reviewers for the `prod` environment.

## 7. Deploy Snowflake objects

Open **Actions → Deploy Snowflake → Run workflow**.

Render the SQL first:

```text
environment: dev
dry_run: true
```

After reviewing the generated SQL, execute the deployment:

```text
environment: dev
dry_run: false
```

Promote to `qa` and `prod` only after the lower environment passes validation.

## 8. Build dbt models

```bash
make dbt-compile
make dbt-build
```

The dbt project includes source freshness, staging models, replay-safe Silver models, incremental Gold products, point-in-time feature products, contracts, and revenue reconciliation.

## 9. Run Spark streaming

The primary streaming job is:

```text
spark/jobs/slot_stream.py
```

Configure Kafka, Snowflake, checkpoint, and Spark connector variables in `.env` before execution. The job uses deterministic event IDs, event-time watermarks, deduplication, dead-letter handling, isolated checkpoints, and an idempotent Snowflake merge sink.

## 10. Run orchestration and ML services

The Airflow DAG is located at:

```text
airflow/dags/casino_data_products.py
```

It checks source freshness, executes changed dbt models, enforces a publication gate, and records the deployment Git SHA.

Model training and drift monitoring are located at:

```text
ml/training/train_player_value.py
ml/monitoring/drift.py
```

The model pipeline uses time-based validation to reduce temporal leakage. Model promotion requires recorded metrics, feature timestamps, model version, drift status, and rollback metadata.

## 11. Cortex semantic analytics

The governed semantic definition is located at:

```text
snowflake/semantic/casino_semantic_model.yaml
```

It defines certified revenue and profitability metrics, verified queries, business-language instructions, and restrictions against player-level PII exposure.

## Validation checklist

Credential-free validation:

```bash
make bootstrap
make validate
make local-demo
make terraform-check
```

Cloud validation:

```bash
make install-cloud
make cloud-smoke
make dbt-compile
make dbt-build
```

Deployment validation begins with the Snowflake workflow in `dev` using `dry_run: true`, followed by a reviewed `dry_run: false` execution.
