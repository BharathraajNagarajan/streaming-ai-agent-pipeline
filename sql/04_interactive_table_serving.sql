-- ============================================================================
-- 04_interactive_table_serving.sql
-- Interactive Table: a low-latency, high-concurrency serving copy of Gold,
-- purpose-built for the Streamlit dashboard and the Cortex Agent to query
-- simultaneously without contending with the Dynamic Table refresh.
-- ============================================================================

USE ROLE STREAMING_PIPELINE_ROLE;
USE DATABASE STREAMING_PIPELINE_DB;
USE SCHEMA EVENTS;

CREATE OR REPLACE INTERACTIVE TABLE SERVICE_HEALTH_SERVING
    TARGET_LAG = '1 minute'
    WAREHOUSE = STREAMING_PIPELINE_WH
    CLUSTER BY (SERVICE)
AS
SELECT * FROM GOLD_SERVICE_HEALTH;

COMMENT ON TABLE SERVICE_HEALTH_SERVING IS
    'Fast-read serving copy of Gold. Backs both the Streamlit dashboard and the Cortex Agent.';
