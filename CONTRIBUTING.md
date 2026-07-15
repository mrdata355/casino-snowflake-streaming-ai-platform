# Contributing

## Branching

Create focused branches such as `feat/snowflake-rbac`, `feat/slot-stream`, or `fix/point-in-time-join`. Do not push feature work directly to `main`.

## Pull-request standard

Every pull request should explain:

1. Business problem and affected data product
2. Architecture decision and alternatives considered
3. Grain, keys, idempotency, and replay behavior
4. Security and PII impact
5. Testing and reconciliation evidence
6. Deployment, rollback, and observability changes

## Required checks

- Python linting and compilation
- Unit, contract, integration, and reconciliation tests
- Terraform formatting and validation
- dbt parsing or compilation when credentials are available
- Secret and dependency scanning

Use Conventional Commit messages, for example `feat(streaming): add watermark and replay-safe merge`.
