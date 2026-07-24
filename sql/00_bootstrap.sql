-- ============================================================================
-- 00_bootstrap.sql
-- Creates the identity, database, warehouse, and network policy this project
-- runs under. Run once, as ACCOUNTADMIN, before anything else.
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Keep the account on UTC so producer event timestamps (emitted in UTC) line
-- up with CURRENT_TIMESTAMP() when computing per-layer freshness later.
ALTER ACCOUNT SET TIMEZONE = 'UTC';

-- Dedicated role + user for this project, scoped narrowly rather than reusing
-- a personal login. In production this would be split further (an ingest-only
-- role for the producer, a read-only role for the dashboard, etc.) — see
-- docs/production_considerations.md for that discussion.
CREATE ROLE IF NOT EXISTS STREAMING_PIPELINE_ROLE;

CREATE USER IF NOT EXISTS STREAMING_PIPELINE_USER
    DEFAULT_ROLE = STREAMING_PIPELINE_ROLE
    COMMENT = 'Service account for the streaming-ai-agent-pipeline project';

GRANT ROLE STREAMING_PIPELINE_ROLE TO USER STREAMING_PIPELINE_USER;

-- Programmatic Access Tokens require the user to sit behind a network policy.
CREATE NETWORK POLICY IF NOT EXISTS STREAMING_PIPELINE_NP
    ALLOWED_IP_LIST = ('0.0.0.0/0');  -- tighten to a real CIDR range in production

ALTER USER STREAMING_PIPELINE_USER SET NETWORK_POLICY = STREAMING_PIPELINE_NP;

ALTER USER STREAMING_PIPELINE_USER
    ADD PROGRAMMATIC ACCESS TOKEN STREAMING_PIPELINE_PAT
    ROLE_RESTRICTION = 'STREAMING_PIPELINE_ROLE'
    DAYS_TO_EXPIRY = 14
    COMMENT = 'Token used by the Python producer and local tooling';
-- The token_secret is shown exactly once in the result grid.
-- Copy it into producer/profile.json (see producer/profile.example.json) — never commit it.

-- Warehouse, database, schema
CREATE WAREHOUSE IF NOT EXISTS STREAMING_PIPELINE_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS STREAMING_PIPELINE_DB;
CREATE SCHEMA IF NOT EXISTS STREAMING_PIPELINE_DB.EVENTS;

GRANT USAGE ON WAREHOUSE STREAMING_PIPELINE_WH TO ROLE STREAMING_PIPELINE_ROLE;
GRANT USAGE ON DATABASE STREAMING_PIPELINE_DB TO ROLE STREAMING_PIPELINE_ROLE;
GRANT USAGE ON SCHEMA STREAMING_PIPELINE_DB.EVENTS TO ROLE STREAMING_PIPELINE_ROLE;
GRANT CREATE TABLE, CREATE DYNAMIC TABLE, CREATE STREAMLIT, CREATE STAGE, CREATE SEMANTIC VIEW
    ON SCHEMA STREAMING_PIPELINE_DB.EVENTS TO ROLE STREAMING_PIPELINE_ROLE;

-- Confirm your account identifier for the producer profile:
SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME() AS account_identifier;
