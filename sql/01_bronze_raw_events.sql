-- ============================================================================
-- 01_bronze_raw_events.sql
-- The Bronze landing table. Insert-only, raw VARIANT payload, written to
-- directly by the Snowpipe Streaming SDK in producer/log_producer.py.
--
-- No CREATE PIPE statement is needed — Snowflake's high-performance Snowpipe
-- Streaming architecture auto-creates a managed pipe the first time data is
-- streamed into this table (named "<TABLE_NAME>-streaming").
-- ============================================================================

USE ROLE STREAMING_PIPELINE_ROLE;
USE DATABASE STREAMING_PIPELINE_DB;
USE SCHEMA EVENTS;
USE WAREHOUSE STREAMING_PIPELINE_WH;

CREATE TABLE IF NOT EXISTS BRONZE_SERVICE_EVENTS (
    RAW_PAYLOAD   VARIANT,
    LANDED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE BRONZE_SERVICE_EVENTS IS
    'Raw, insert-only landing table for service event logs streamed via Snowpipe Streaming. One row per event; no transformation applied yet.';
