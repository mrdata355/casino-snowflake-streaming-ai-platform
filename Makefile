SHELL := /bin/bash
PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

.PHONY: help bootstrap install-dev install-cloud validate lint test local-demo local-up local-down \
        create-topics contracts dbt-compile dbt-build terraform-check cloud-smoke package clean

help:
	@echo "bootstrap        Create a virtual environment and install developer dependencies"
	@echo "validate         Run lint, compilation, contracts, tests, and coverage"
	@echo "local-demo       Run the credential-free end-to-end casino pipeline"
	@echo "install-cloud    Install Snowflake, Spark, Airflow, dbt, MLflow, and cloud packages"
	@echo "local-up         Start Kafka, Postgres, MLflow, and the optional feature API"
	@echo "create-topics    Create the local Kafka topics after local-up"
	@echo "dbt-compile      Compile dbt models after Snowflake credentials are configured"
	@echo "terraform-check  Format and validate Terraform when Terraform is installed"
	@echo "cloud-smoke      Validate local Snowflake credentials and run a smoke query"

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements-dev.txt
	cp -n .env.example .env || true

install-dev:
	$(VENV_PIP) install -r requirements-dev.txt

install-cloud:
	$(VENV_PIP) install -r requirements-cloud.txt

validate: lint contracts test

lint:
	$(VENV_PYTHON) -m ruff format --check .
	$(VENV_PYTHON) -m ruff check .
	$(VENV_PYTHON) -m compileall -q local_demo ingestion spark services ml scripts airflow lakehouse tests

contracts:
	APP_ENV=test $(VENV_PYTHON) -m pytest -q tests/contract tests/architecture

test:
	APP_ENV=test $(VENV_PYTHON) -m pytest -q --cov=local_demo --cov-report=term-missing --cov-report=xml

local-demo:
	$(VENV_PYTHON) -m scripts.run_local_demo --count 250 --output-dir build/demo

local-up:
	docker compose --profile platform up -d

local-down:
	docker compose --profile platform down -v

create-topics:
	bash scripts/create_kafka_topics.sh

dbt-compile:
	cd dbt && ../$(VENV_PYTHON) -m dbt deps --profiles-dir . && \
	../$(VENV_PYTHON) -m dbt compile --profiles-dir . --target $${DBT_TARGET:-dev}

dbt-build:
	cd dbt && ../$(VENV_PYTHON) -m dbt build --profiles-dir . --target $${DBT_TARGET:-dev}

terraform-check:
	terraform -chdir=terraform fmt -check -recursive
	terraform -chdir=terraform init -backend=false
	terraform -chdir=terraform validate

cloud-smoke:
	$(VENV_PYTHON) -m scripts.validate_env
	bash scripts/smoke_test.sh

package:
	zip -r casino-snowflake-streaming-ai-platform.zip . \
		-x '.git/*' '.venv/*' '.env' 'build/*' '*.pyc' '__pycache__/*'

clean:
	rm -rf build .pytest_cache .ruff_cache coverage.xml htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
