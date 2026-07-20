USE DATABASE ${DATABASE_NAME};
USE SCHEMA BRONZE;

CREATE FILE FORMAT IF NOT EXISTS JSON_FF
  TYPE = JSON
  STRIP_OUTER_ARRAY = FALSE
  ENABLE_OCTAL = FALSE;

-- Internal stage enables a first Snowflake demo without requiring S3, Azure, or GCS.
CREATE STAGE IF NOT EXISTS LOCAL_DEMO_STAGE
  FILE_FORMAT = JSON_FF
  COMMENT = 'Internal stage for authorized synthetic demonstration files';

-- High-performance Snowpipe Streaming custom pipe with server-side transformations.
CREATE OR REPLACE PIPE SLOT_EVENT_STREAMING_PIPE
AS
COPY INTO BRONZE.SLOT_EVENTS_RAW (
  RAW_PAYLOAD,
  EVENT_ID,
  EVENT_TIME,
  INGESTION_TIME,
  PROPERTY_ID,
  LOCATION_ID,
  MACHINE_ID,
  EVENT_TYPE,
  AMOUNT,
  CURRENCY,
  SOURCE_SYSTEM,
  SCHEMA_VERSION,
  LOAD_BATCH_ID,
  RECORD_HASH
)
FROM (
  SELECT
    $1,
    $1:event_id::STRING,
    TRY_TO_TIMESTAMP_TZ($1:event_time::STRING),
    CURRENT_TIMESTAMP(),
    $1:property_id::STRING,
    $1:location_id::STRING,
    $1:machine_id::STRING,
    $1:event_type::STRING,
    TRY_TO_DECIMAL($1:amount, 18, 2),
    COALESCE($1:currency::STRING, 'USD'),
    'SNOWPIPE_STREAMING',
    COALESCE($1:schema_version::NUMBER, 1),
    UUID_STRING(),
    SHA2(TO_JSON($1), 256)
  FROM TABLE(DATA_SOURCE(TYPE => 'STREAMING'))
);
