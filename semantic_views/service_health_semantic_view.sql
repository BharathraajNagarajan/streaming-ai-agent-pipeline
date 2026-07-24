-- ============================================================================
-- service_health_semantic_view.sql
-- Gives the Cortex Agent business-level vocabulary over GOLD_SERVICE_HEALTH /
-- SERVICE_HEALTH_SERVING: which columns are facts vs. dimensions, how metrics
-- are computed, and what plain-English terms map to which fields.
--
-- This file is a STARTING POINT, not a finished artifact. A semantic view is
-- a governance decision as much as a technical one — before pointing an
-- agent at this in anything beyond a demo, have someone who owns the actual
-- business definitions review the metric formulas and synonyms below.
-- ============================================================================

USE ROLE STREAMING_PIPELINE_ROLE;
USE DATABASE STREAMING_PIPELINE_DB;
USE SCHEMA EVENTS;

CREATE OR REPLACE SEMANTIC VIEW SERVICE_HEALTH_SV
    TABLES (
        health AS SERVICE_HEALTH_SERVING
            PRIMARY KEY (SERVICE, MINUTE_BUCKET)
    )
    DIMENSIONS (
        health.SERVICE       AS SERVICE       WITH SYNONYMS ('service name', 'microservice', 'component'),
        health.MINUTE_BUCKET AS MINUTE_BUCKET WITH SYNONYMS ('time', 'minute', 'timestamp')
    )
    FACTS (
        health.REQUEST_COUNT   AS REQUEST_COUNT,
        health.ERROR_COUNT     AS ERROR_COUNT,
        health.ERROR_RATE      AS ERROR_RATE      WITH SYNONYMS ('error percentage', 'failure rate'),
        health.P95_LATENCY_MS  AS P95_LATENCY_MS  WITH SYNONYMS ('latency', 'response time', 'p95')
    )
    METRICS (
        health.TOTAL_REQUESTS  AS SUM(health.REQUEST_COUNT)  WITH SYNONYMS ('traffic', 'volume'),
        health.TOTAL_ERRORS    AS SUM(health.ERROR_COUNT),
        health.AVG_ERROR_RATE  AS AVG(health.ERROR_RATE)     WITH SYNONYMS ('average error rate'),
        health.WORST_P95_LATENCY AS MAX(health.P95_LATENCY_MS) WITH SYNONYMS ('worst latency', 'peak latency')
    )
    COMMENT = 'Business-level view over service health for the RetailPulse SRE Cortex Agent.';

-- Sanity check: total requests, total errors, and average error rate by
-- service — this is the query the agent effectively runs under the hood
-- when asked something like "what's the error rate per service right now?"
SELECT
    SERVICE,
    total_requests,
    total_errors,
    avg_error_rate
FROM SEMANTIC_VIEW(
    SERVICE_HEALTH_SV
    METRICS total_requests, total_errors, avg_error_rate
    DIMENSIONS SERVICE
)
ORDER BY avg_error_rate DESC;
