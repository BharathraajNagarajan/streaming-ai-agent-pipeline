# streamlit/

The human-facing view. A Streamlit-in-Snowflake app — runs inside Snowflake
itself, no separate hosting, no local server.

## File

- `app.py` — three panels: per-layer freshness meter, a live raw event feed
  from Bronze, and error-rate/P95-latency-by-service from the serving layer
  with the worst-performing service called out explicitly.

## How it connects

```
SERVICE_HEALTH_SERVING  ──┐
BRONZE_SERVICE_EVENTS   ──┼──▶  app.py (get_active_session())  ──▶  browser
GOLD_SERVICE_HEALTH     ──┘
```

No external connection string or credentials — Streamlit-in-Snowflake apps
run under the warehouse/role that deployed them and read via
`get_active_session()`.

## Deploying

```sql
CREATE STAGE IF NOT EXISTS STREAMING_PIPELINE_DB.EVENTS.STREAMLIT_STAGE;
PUT file://streamlit/app.py @STREAMING_PIPELINE_DB.EVENTS.STREAMLIT_STAGE AUTO_COMPRESS=FALSE;

CREATE OR REPLACE STREAMLIT STREAMING_PIPELINE_DB.EVENTS.SERVICE_HEALTH_DASHBOARD
    ROOT_LOCATION = '@STREAMING_PIPELINE_DB.EVENTS.STREAMLIT_STAGE'
    MAIN_FILE = 'app.py'
    QUERY_WAREHOUSE = STREAMING_PIPELINE_WH
    TITLE = 'RetailPulse Service Health';
```

Then open it from **Snowsight \u2192 Projects \u2192 Streamlit**.
