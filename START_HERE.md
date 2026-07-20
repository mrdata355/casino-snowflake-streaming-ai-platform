# S.T.A.R.T. Here

This is the simplest path through the project. You do not need Snowflake credentials for the first three steps.

The project uses **synthetic casino data**. It is a portfolio reference implementation, not a system deployed by Hard Rock or another casino operator.

## The project in very simple words

- **GitHub repository** = the filing cabinet holding all project files.
- **Python virtual environment** = a private toolbox for this project.
- **Synthetic data** = pretend casino records that are safe to use publicly.
- **Snowflake database** = the organized storage building.
- **Schema** = a room inside the storage building.
- **Warehouse** = the worker that performs Snowflake calculations.
- **Role** = the key deciding which rooms a person or service may enter.
- **GitHub secret** = a locked envelope containing a private credential.

## S — Set up the project

Use a Windows or Mac computer. Install these first:

1. GitHub Desktop
2. Python 3.11
3. Visual Studio Code
4. Docker Desktop
5. Terraform

In GitHub Desktop:

1. Click **File**.
2. Click **Clone repository**.
3. Choose `mrdata355/casino-snowflake-streaming-ai-platform`.
4. Choose a folder on your computer.
5. Click **Clone**.
6. Click **Open in Visual Studio Code**.

Open the Visual Studio Code terminal and run:

```bash
make bootstrap
```

On Windows PowerShell without `make`, run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

What this does:

- Creates the project toolbox named `.venv`.
- Installs testing and API packages.
- Creates a private local `.env` file from the safe example.
- Does not connect to Snowflake yet.

## T — Test the credential-free project

Mac or Linux:

```bash
make validate
```

Windows PowerShell:

```powershell
$env:APP_ENV="test"
.\.venv\Scripts\python.exe -m ruff check local_demo services scripts tests
.\.venv\Scripts\python.exe -m scripts.validate_env --template-mode
.\.venv\Scripts\python.exe -m pytest -q --cov=local_demo --cov-fail-under=90
```

A successful run proves:

- The code follows quality rules.
- The Snowflake templates have all required variables.
- The JSON data contracts are valid.
- The semantic model is valid YAML.
- The tests pass.
- Core local-demo coverage is at least 90 percent.

## A — Activate the synthetic casino demonstration

Mac or Linux:

```bash
make local-demo
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_local_demo --count 250 --output-dir build/demo
```

Then open:

```text
build/demo/summary.json
```

The demonstration performs this pipeline:

```text
Generate pretend slot events
        ↓
Validate business and contract rules
        ↓
Detect and remove duplicate event IDs
        ↓
Write Bronze raw events
        ↓
Write Silver cleaned events
        ↓
Create Gold five-minute slot-performance records
        ↓
Train and evaluate a simple baseline model
        ↓
Write data-quality and model-metric results
```

Expected proof includes:

- Raw event count
- Deduplicated event count
- Duplicate count removed
- Five-minute window count
- Data-quality results
- Model validation error

## R — Register private Snowflake credentials later

Never put a password or private key into a code file, README, issue, pull request, or chat message.

In GitHub:

1. Open the repository.
2. Click **Settings**.
3. Click **Environments**.
4. Create environments named `dev`, `qa`, and `prod`.
5. Open the `dev` environment first.
6. Add the following environment secrets:

```text
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PRIVATE_KEY
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
```

Add the following environment variables:

```text
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
```

Use key-pair authentication rather than committing a Snowflake password.

The repository contains placeholders only. You enter the real values privately in GitHub.

## T — Turn on Snowflake carefully

Do not begin with production.

1. Open the repository's **Actions** tab.
2. Select **Deploy Snowflake**.
3. Click **Run workflow**.
4. Select the `dev` environment.
5. Keep `dry_run` set to `true`.
6. Run it.
7. Read the generated validation output.
8. Correct names or permissions before creating anything.
9. Run again with `dry_run` set to `false` only after the DEV configuration is correct.
10. Validate DEV before moving the same reviewed commit to QA.
11. Validate QA before requesting approval for PROD.

The Snowflake deployment creates and validates:

- DEV database and schemas
- Workload-specific warehouses
- Resource monitors and credit limits
- Human and service roles
- Least-privilege grants
- Bronze, Silver, Gold, Semantic, Features, ML, Operations, Quarantine, and Temp layers
- Snowpipe and Snowpipe Streaming objects
- Streams and Tasks
- Dynamic Tables
- Masking and row-access policies
- Observability views
- Semantic-model objects

## What to learn first

Start with Topic 1 in this order:

1. Database
2. Schema
3. Warehouse
4. Role
5. Grant
6. Resource monitor
7. DEV, QA, and PROD separation
8. Deployment validation
9. Rollback
10. Interview explanation

Do not try to memorize every file at once. First understand what each room, worker, and key is responsible for. Then write the code from memory in small sections.

## The safety rule

```text
Code goes in GitHub.
Mock values may go in GitHub.
Real secrets go only in GitHub Secrets or an approved secret manager.
```
