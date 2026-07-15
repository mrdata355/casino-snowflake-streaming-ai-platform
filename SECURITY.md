# Security Policy

## Public repository boundaries

This project must contain synthetic data only. Do not commit:

- Snowflake private keys, passwords, OAuth tokens, session tokens, or account URLs tied to a real environment
- AWS, Azure, or GCP credentials
- customer, player, employee, payment, loyalty, gaming, or operational records
- `.env`, Terraform state, dbt target artifacts, Spark checkpoints, ML model binaries, or Airflow metadata

## Authentication pattern

Production deployments should use Snowflake key-pair authentication or workload identity, GitHub Environments for approval, and an enterprise secret manager. Secrets must be injected at runtime and rotated according to organizational policy.

## Data protection pattern

Sensitive player attributes must be protected with classification tags, masking policies, row-access policies, least-privilege roles, audited access, and restricted non-production data. Production data should never be copied into this portfolio project.

## Reporting a problem

Do not open a public issue containing a credential or exploitable secret. Revoke the exposed credential immediately, remove it from Git history, and use GitHub's private vulnerability reporting mechanism when enabled.
