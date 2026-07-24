-- ============================================================================
-- 03_gold_service_health.sql
-- The Gold layer: per-service, per-minute health metrics. This is the
-- business-level aggregate that the semantic view and Cortex Agent reason
-- over — nobody queries raw logs during an incident, they query health.
-- ============================================================================

USE ROLE STREAMING_PIPELINE_ROLE;
USE DATABASE STREAMING_PIPELINE_DB;
USE SCHEMA EVENTS;

CREATE OR REPLACE DYNAMIC TABLE GOLD_SERVICE_HEALTH
    TARGET_LAG = '1 minute'
    WAREHOUSE = STREAMING_PIPELINE_WH
AS
SELECT
    SERVICE,
    DATE_TRUNC('minute', EVENT_TS)                                   AS MINUTE_BUCKET,
    COUNT(*)                                                          AS REQUEST_COUNT,
    SUM(IFF(STATUS_CODE >= 500, 1, 0))                                AS ERROR_COUNT,
    DIV0(SUM(IFF(STATUS_CODE >= 500, 1, 0)), COUNT(*))                AS ERROR_RATE,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY LATENCY_MS)          AS P95_LATENCY_MS
FROM SILVER_SERVICE_EVENTS
GROUP BY SERVICE, DATE_TRUNC('minute', EVENT_TS);

COMMENT ON DYNAMIC TABLE GOLD_SERVICE_HEALTH IS
    'One row per service per minute: request volume, error rate, and P95 latency. The AI-ready dataset.';
