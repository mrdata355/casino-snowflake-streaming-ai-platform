USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS ${DATABASE_NAME}
  DATA_RETENTION_TIME_IN_DAYS = ${DATA_RETENTION_DAYS}
  COMMENT = 'Synthetic casino data platform ${ENVIRONMENT} environment';

USE DATABASE ${DATABASE_NAME};

CREATE SCHEMA IF NOT EXISTS BRONZE COMMENT = 'Immutable source-aligned landing and replay history';
CREATE SCHEMA IF NOT EXISTS SILVER COMMENT = 'Validated, deduplicated, and conformed enterprise entities';
CREATE SCHEMA IF NOT EXISTS GOLD COMMENT = 'Certified domain data products and business facts';
CREATE SCHEMA IF NOT EXISTS SEMANTIC COMMENT = 'Governed metrics and conversational business semantics';
CREATE SCHEMA IF NOT EXISTS FEATURES COMMENT = 'Point-in-time correct reusable ML feature products';
CREATE SCHEMA IF NOT EXISTS ML COMMENT = 'Training sets, model registry metadata, and governed scores';
CREATE SCHEMA IF NOT EXISTS OPS COMMENT = 'Pipeline audit, quality, contracts, lineage, and access metadata';
CREATE SCHEMA IF NOT EXISTS QUARANTINE COMMENT = 'Rejected records and contract violations';
CREATE SCHEMA IF NOT EXISTS TEMP DATA_RETENTION_TIME_IN_DAYS = 0 COMMENT = 'Ephemeral deployment and merge staging';
