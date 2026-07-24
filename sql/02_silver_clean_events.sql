-- ============================================================================
-- 02_silver_clean_events.sql
-- The Silver layer: a Dynamic Table that flattens, types, filters, and
-- deduplicates the raw Bronze stream. This is declarative — no scheduled job
-- to write or maintain. Snowflake computes the incremental refresh plan to
-- keep this within the TARGET_LAG we specify.
-- ============================================================================

USE ROLE STREAMING_PIPELINE_ROLE;
USE DATABASE STREAMING_PIPELINE_DB;
USE SCHEMA EVENTS;

CREATE OR REPLACE DYNAMIC TABLE SILVER_SERVICE_EVENTS
    TARGET_LAG = '1 minute'
    WAREHOUSE = STREAMING_PIPELINE_WH
AS
WITH flattened AS (
    SELECT
        RAW_PAYLOAD:event_id::STRING          AS EVENT_ID,
        RAW_PAYLOAD:event_ts::TIMESTAMP_NTZ   AS EVENT_TS,
        RAW_PAYLOAD:service::STRING           AS SERVICE,
        RAW_PAYLOAD:level::STRING             AS LOG_LEVEL,
        RAW_PAYLOAD:status_code::NUMBER       AS STATUS_CODE,
        RAW_PAYLOAD:latency_ms::NUMBER        AS LATENCY_MS,
        RAW_PAYLOAD:endpoint::STRING          AS ENDPOINT,
        RAW_PAYLOAD:region::STRING            AS REGION,
        RAW_PAYLOAD:trace_id::STRING          AS TRACE_ID,
        RAW_PAYLOAD:dependency::STRING        AS DEPENDENCY,
        RAW_PAYLOAD:message::STRING           AS MESSAGE,
        LANDED_AT,
        -- A streaming pipeline can redeliver the same event on retry/restart,
        -- so rank duplicates and keep only the most recently landed copy.
        ROW_NUMBER() OVER (
            PARTITION BY RAW_PAYLOAD:event_id::STRING
            ORDER BY LANDED_AT DESC
        ) AS RN
    FROM BRONZE_SERVICE_EVENTS
    WHERE RAW_PAYLOAD:level::STRING != 'HEARTBEAT'  -- drop keepalive noise before it costs storage/compute
)
SELECT
    EVENT_ID, EVENT_TS, SERVICE, LOG_LEVEL, STATUS_CODE, LATENCY_MS,
    ENDPOINT, REGION, TRACE_ID, DEPENDENCY, MESSAGE, LANDED_AT
FROM flattened
WHERE RN = 1;

COMMENT ON DYNAMIC TABLE SILVER_SERVICE_EVENTS IS
    'Typed, deduplicated, heartbeat-filtered service events. Refreshes within 1 minute of Bronze.';
