# sql/

Every SQL object in this project, in the order you'd run them. Each file is
idempotent (`CREATE OR REPLACE` / `IF NOT EXISTS`) so re-running is safe.

| File | Creates | Notes |
|---|---|---|
| `00_bootstrap.sql` | Role, user, PAT, network policy, warehouse, database, schema | Run once as `ACCOUNTADMIN` |
| `01_bronze_raw_events.sql` | `BRONZE_SERVICE_EVENTS` | Insert-only landing table; the Snowpipe Streaming SDK writes here directly |
| `02_silver_clean_events.sql` | `SILVER_SERVICE_EVENTS` (Dynamic Table) | Flatten, type, filter, dedupe |
| `03_gold_service_health.sql` | `GOLD_SERVICE_HEALTH` (Dynamic Table) | Per-service, per-minute health metrics |
| `04_interactive_table_serving.sql` | `SERVICE_HEALTH_SERVING` (Interactive Table) | Low-latency serving copy for the dashboard + agent |
| `05_cleanup.sql` | — | Drops everything, in dependency order |

No `CREATE PIPE` statement appears anywhere — the Bronze table's ingestion
pipe is auto-created by Snowflake the first time the producer streams a row
into it (`BRONZE_SERVICE_EVENTS-streaming`).
