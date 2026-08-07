# OpsReady Advanced Mastery V5

OpsReady now combines five complementary layers instead of replacing prior work:

1. Production Control Room and incident recovery.
2. 30-defect broken-pipeline repair bay.
3. Advanced SQL, PySpark, Python testing, dbt, API, CI/CD and triage labs.
4. V4 architecture reasoning, Jinja mastery and AgentOps.
5. V5 Business Project Quest for business missions, portfolio projects, ML projects and model scoring.

## V5 Business Project Quest

### Business Missions — 12
Each mission follows a production progression: business brief → architecture decision → why/why-not reasoning → build plan/code patterns → validation evidence → business debrief.

Mission domains include loyalty freshness, Snowflake FinOps, governed revenue, slot streaming, point-in-time ML features, low-latency serving, bounded backfills, DEV/QA/PROD promotion, schema drift, profitability marts, fraud-review capacity and governed conversational analytics.

### Casino Repo Portfolio Projects — 10
The quest maps directly to existing repository assets:

- End-to-End Casino Data Product — `airflow/ + dbt/ + snowflake/`
- Real-Time Slot Streaming Pipeline — `spark/jobs/slot_stream.py + ingestion/`
- Snowflake Native CDC Platform — `snowflake/ddl + snowflake/ops`
- Governed Profitability Mart — `dbt/models/gold`
- Player Feature Platform — `dbt/models/features`
- MLflow Player Value Training — `ml/training/train_player_value.py`
- Model Drift Monitoring — `ml/monitoring/drift.py`
- Feature & Score API — `services/feature_api`
- Production Validation Suite — `tests/ + dbt/tests + snowflake/tests`
- Infrastructure & Release Platform — `terraform/ + .github/ + docker-compose.yml`

### ML Projects — 10
Projects cover player value regression, churn classification, next-best-offer ranking, digital fraud, slot anomaly detection, labor/footfall forecasting, bounded dynamic pricing, profitability forecasting, redemption propensity and model monitoring.

Each ML project grades model choice, point-in-time feature design, technical/business evaluation, leakage/drift/operating risk, and scoring/deployment provenance.

### Model Scoring & Decisioning — 10
Drills cover batch vs online scoring, provenance contracts, capacity-based thresholds, freshness protection, canary promotion, retry-safe idempotency, drift with delayed labels, training-serving feature parity and score-API SLO triage.

### Repository Capability Map
The V5 repo map connects the major folders visible in the repository to production responsibilities and quest projects: `.github`, Airflow, contracts, dbt, docs, ingestion, local demo, ML, observability, OpsReady, scripts, services, simulators, Snowflake, Spark, Terraform and tests.

## Scoring philosophy

OpsReady V5 is designed around the question: **Can the engineer solve the business problem and prove the result, not merely recognize syntax?**

Business missions score architecture choice, reasoning, implementation, validation and business debrief separately. ML and model-scoring projects also require operating constraints, provenance and acceptance evidence. Scores persist locally and emit evidence into the existing OpsReady manager dashboard.

The static Vercel experience remains a simulated execution environment. A future enterprise edition can swap selected modules for isolated real SQL/Python/Spark/cloud sandboxes while preserving the same mission and evidence model.
