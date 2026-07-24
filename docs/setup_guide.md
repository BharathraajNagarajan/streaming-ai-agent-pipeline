# Setup Guide

## Prerequisites

- A Snowflake account with `ACCOUNTADMIN` access (a free trial works —
  Interactive Tables require a region that supports them, e.g. AWS
  `us-west-2`)
- Python 3.9+
- Git

## 1. Bootstrap Snowflake objects

Run, in order, as `ACCOUNTADMIN` in a Snowsight worksheet:

```sql
-- sql/00_bootstrap.sql   → role, user, PAT, warehouse, database, schema
-- sql/01_bronze_raw_events.sql
-- sql/02_silver_clean_events.sql
-- sql/03_gold_service_health.sql
-- sql/04_interactive_table_serving.sql
```

Copy the PAT `token_secret` printed by `00_bootstrap.sql` — it's shown once.

## 2. Set up the producer

```bash
cd producer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp profile.example.json profile.json
# edit profile.json with your account identifier + the PAT from step 1
```

## 3. Start streaming

```bash
python log_producer.py --profile profile.json --rps 200
```

Give it ~30–60 seconds, then confirm data is flowing:

```sql
SELECT COUNT(*) FROM STREAMING_PIPELINE_DB.EVENTS.BRONZE_SERVICE_EVENTS;
SELECT * FROM STREAMING_PIPELINE_DB.EVENTS.SILVER_SERVICE_EVENTS LIMIT 10;
SELECT * FROM STREAMING_PIPELINE_DB.EVENTS.GOLD_SERVICE_HEALTH ORDER BY MINUTE_BUCKET DESC LIMIT 10;
```

## 4. Deploy the semantic view and agent

Run `semantic_views/service_health_semantic_view.sql`, then follow
`cortex_agent/agent_configuration.md` to create the agent in Snowsight
(agents are configured through the UI, not SQL).

## 5. Deploy the dashboard

Follow the deploy steps in `streamlit/README.md`.

## 6. Try the incident scenario

```bash
python log_producer.py --profile profile.json --rps 200 \
    --fault inventory_cascade --fault-after 30
```

Then walk through `docs/incident_walkthrough.md` against the dashboard and
the agent.

## 7. Clean up

```sql
-- sql/05_cleanup.sql, run as STREAMING_PIPELINE_ROLE, then the commented
-- ACCOUNTADMIN lines from a separate session
```
