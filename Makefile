SHELL := /bin/bash
PYTHON ?= python3

.PHONY: bootstrap validate local-up local-down lint test dbt-compile dbt-build terraform-fmt smoke package

bootstrap:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && bash scripts/install.sh
	cp -n .env.example .env || true

validate: lint test dbt-compile terraform-fmt

local-up:
	docker compose up -d kafka postgres mlflow feature-api

local-down:
	docker compose down -v

lint:
	. .venv/bin/activate && ruff check ingestion spark services ml tests airflow scripts
	. .venv/bin/activate && python -m compileall ingestion spark services ml tests airflow scripts

test:
	. .venv/bin/activate && pytest -q

dbt-compile:
	cd dbt && dbt deps --profiles-dir . && dbt compile --profiles-dir . --target $${DBT_TARGET:-dev}

dbt-build:
	cd dbt && dbt build --profiles-dir . --target $${DBT_TARGET:-dev}

terraform-fmt:
	terraform -chdir=terraform fmt -check -recursive

smoke:
	bash scripts/smoke_test.sh

package:
	zip -r casino-lakehouse-platform.zip . -x '.git/*' '.venv/*' '.env'
