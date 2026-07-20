# S.T.A.R.T. Walkthrough

This is the exact operating sequence for the repository. Follow it in order. Do not add cloud credentials until the credential-free path passes on your computer.

## What was delivered

The repository contains eight integrated production-style projects:

1. Snowflake lakehouse foundation, schemas, warehouses, RBAC, masking, row-access policies, resource monitors, Time Travel, and validation views.
2. Kafka and Pub/Sub event ingestion with Spark Structured Streaming, event-time processing, watermarks, deduplication, checkpoints, dead-letter routing, and replay-safe Snowflake merges.
3. Snowpipe, Streams, Tasks, and Dynamic Tables for native Snowflake ingestion and transformation.
4. Certified casino revenue, slot-performance, and location-profitability data products.
5. Point-in-time ML features, time-based training, MLflow registration, governed model outputs, and drift monitoring.
6. Cortex semantic models with verified questions and restrictions against exposing player-level PII.
7. Airflow, dbt, Terraform, and GitHub Actions for orchestration, testing, infrastructure, promotion, and security scanning.
8. Contracts, reconciliation, observability, cost attribution, source-to-target mappings, incident response, replay, and rollback procedures.

The data and identifiers are synthetic. This is a reference implementation, not a system deployed for a casino operator.

---

# S — Set up the credential-free environment

## 1. Install prerequisites

Install:

- Git
- Python 3.11, 3.12, or 3.13
- Docker Desktop with Docker Compose
- Terraform for the infrastructure validation stage

Confirm the tools:

```bash
git --version
python3 --version
docker --version
docker compose version
terraform version
```

## 2. Clone the repository

```bash
git clone https://github.com/mrdata355/casino-snowflake-streaming-ai-platform.git
cd casino-snowflake-streaming-ai-platform
git checkout main
git pull
```

## 3. Create the local Python environment

```bash
make bootstrap
```

That command creates `.venv`, installs the credential-free developer dependencies, and copies `.env.example` to `.env` without overwriting an existing file.

Activate the environment when working manually:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Run the credential-free end-to-end demonstration

```bash
make local-demo
```

The demonstration generates synthetic slot events, validates them, handles duplicates and malformed records, creates business aggregates, and produces a baseline anomaly score. Review the generated files under:

```text
build/demo/
```

---

# T — Test the complete credential-free core

Run the full validation gate:

```bash
make validate
```

This runs:

- Ruff formatting and lint checks
- Python compilation
- Contract and repository-architecture tests
- Deterministic unit, integration, and reconciliation tests
- Core coverage reporting

The merged GitHub pull request passed CI, security scanning, Snowflake template validation, Terraform validation, and the deterministic test suite. The measured credential-free core coverage at publication was 93.91%.

Also run Terraform independently:

```bash
make terraform-check
```

Do not proceed to credentials until both commands pass.

---

# A — Add credentials safely later

## Local Snowflake configuration

Keep `.env` only on your computer. It is ignored by Git and must never be committed.

Update these values in `.env`:

```text
SNOWFLAKE_ACCOUNT_IDENTIFIER
SNOWFLAKE_USER
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
SNOWFLAKE_PRIVATE_KEY_PATH
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
```

Preferred authentication is an encrypted PKCS#8 private key. Point `SNOWFLAKE_PRIVATE_KEY_PATH` to the local key file. Do not place the key inside the repository.

Password authentication is intentionally disabled by default. Do not change `ALLOW_SNOWFLAKE_PASSWORD_AUTH=false` unless you are performing a temporary, controlled local test.

Load the local environment in Bash before cloud commands:

```bash
set -a
source .env
set +a
```

Install the optional cloud packages:

```bash
make install-cloud
```

Validate that the required local values are present without printing secrets:

```bash
python -m scripts.validate_env
```

## GitHub Environment configuration

In the repository, open **Settings → Environments** and create:

- `dev`
- `qa`
- `prod`

Add these GitHub Environment secrets:

```text
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PRIVATE_KEY
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
```

Add these GitHub Environment variables:

```text
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
```

Store the complete private-key text as a multiline secret. Never paste it into source code, issues, pull requests, screenshots, chat messages, or workflow YAML.

For `prod`, configure required reviewers so a deployment cannot run without manual approval.

---

# R — Run each platform layer

## 1. Local Kafka, PostgreSQL, MLflow, and optional API services

```bash
make local-up
make create-topics
```

Generate sample events:

```bash
python -m scripts.generate_sample_events --count 100 --out /tmp/slot_events.jsonl
```

Stop and remove the local containers when finished:

```bash
make local-down
```

## 2. Snowflake smoke test

After loading `.env` and installing cloud packages:

```bash
make cloud-smoke
```

This validates the connection configuration and runs the repository smoke checks.

## 3. Snowflake deployment workflow

Open **Actions → Deploy Snowflake → Run workflow**.

First run:

```text
environment: dev
dry_run: true
```

Review the rendered SQL. Then run:

```text
environment: dev
dry_run: false
```

Only promote to `qa` and `prod` after the development deployment and validation queries pass.

## 4. dbt models

After Snowflake is configured:

```bash
make dbt-compile
make dbt-build
```

The dbt project includes source freshness, staging, replay-safe Silver models, incremental Gold products, point-in-time feature products, contracts, and revenue reconciliation.

## 5. Spark streaming

The main streaming job is:

```text
spark/jobs/slot_stream.py
```

Before running it, configure Kafka, Snowflake, checkpoint, and Spark connector variables in `.env`. The job uses deterministic event IDs, event-time watermarks, deduplication, dead-letter handling, isolated checkpoints, and an idempotent Snowflake merge sink.

## 6. Airflow

The production-style orchestration DAG is:

```text
airflow/dags/casino_data_products.py
```

It checks source freshness, runs changed dbt models, enforces a publication gate, and records the deployment Git SHA.

## 7. MLflow and model monitoring

The primary model-training code is:

```text
ml/training/train_player_value.py
```

The drift monitor is:

```text
ml/monitoring/drift.py
```

The model uses a time-based split rather than a random split to reduce temporal leakage. Do not promote a model unless its metrics, feature timestamps, model version, drift status, and rollback target are recorded.

## 8. Cortex semantic analytics

The governed semantic definition is:

```text
snowflake/semantic/casino_semantic_model.yaml
```

It contains certified revenue and profitability metrics, a verified query, business-language instructions, and restrictions against player-level PII exposure.

---

# T — Tell the project story and prove ownership

Use these documents in this order:

1. `docs/PROJECTS.md` — map of the eight integrated projects.
2. `docs/architecture.md` — production architecture and reliability decisions.
3. `docs/source_to_target.md` — source, Bronze, Silver, Gold, feature, and grain mapping.
4. `docs/runbook.md` — incident triage, replay, recovery, and rollback.
5. `docs/interview_walkthrough.md` — five-minute senior-engineer explanation.

For every module, be able to answer:

- What business problem does it solve?
- What is the exact row or event grain?
- What are the primary and natural keys?
- How are duplicates, retries, and late data handled?
- What blocks unsafe publication?
- How is PII restricted?
- How is cost attributed and controlled?
- How is the system replayed or rolled back?
- What evidence proves the module works?

Use this truthful portfolio statement:

> I built a production-style Snowflake streaming and AI reference platform using synthetic casino and resort data. I can explain and operate each module, but it was not deployed for a casino employer or customer.

---

# Final definition of done

You are ready to present the project only after you can complete all of the following without assistance:

```bash
make bootstrap
make validate
make local-demo
make terraform-check
```

After credentials are added, also complete:

```bash
make install-cloud
make cloud-smoke
make dbt-compile
make dbt-build
```

Then execute the GitHub Snowflake deployment workflow in `dev` with `dry_run: true`, review the output, and deploy with `dry_run: false`.

Never claim ownership merely because the code exists in your account. Ownership means you can explain the architecture, modify the code, diagnose a failed test, replay data safely, and defend each design tradeoff.
