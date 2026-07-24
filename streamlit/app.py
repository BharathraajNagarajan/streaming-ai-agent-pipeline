"""
app.py — RetailPulse Service Health Dashboard

A Streamlit-in-Snowflake app with three panels:
  1. Per-layer freshness meter (Bronze / Silver / Gold / Serving)
  2. Live raw event feed from Bronze
  3. Error rate + P95 latency by service from the serving layer, worst
     service highlighted

Runs natively inside Snowflake via `get_active_session()` — no separate
server, no local Streamlit install required. Deploy with:

    CREATE STREAMLIT STREAMING_PIPELINE_DB.EVENTS.SERVICE_HEALTH_DASHBOARD
        ROOT_LOCATION = '@STREAMING_PIPELINE_DB.EVENTS.STREAMLIT_STAGE'
        MAIN_FILE = 'app.py'
        QUERY_WAREHOUSE = STREAMING_PIPELINE_WH;

See the repo root README for the full deploy sequence.
"""

import time

import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="RetailPulse Service Health", layout="wide")
session = get_active_session()

DB = "STREAMING_PIPELINE_DB"
SCHEMA = "EVENTS"
REFRESH_SECONDS = 10

st.title("RetailPulse — Service Health Dashboard")
st.caption(f"Bronze \u2192 Silver \u2192 Gold \u2192 Serving  ·  auto-refreshes every {REFRESH_SECONDS}s")


def q(sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()


# ---------- Panel 1: per-layer freshness ----------
st.subheader("Freshness by Layer")

freshness_sql = f"""
    SELECT 'Bronze' AS LAYER, DATEDIFF('second', MAX(LANDED_AT), CURRENT_TIMESTAMP()) AS SECONDS_BEHIND
    FROM {DB}.{SCHEMA}.BRONZE_SERVICE_EVENTS
    UNION ALL
    SELECT 'Silver', DATEDIFF('second', MAX(LANDED_AT), CURRENT_TIMESTAMP())
    FROM {DB}.{SCHEMA}.SILVER_SERVICE_EVENTS
    UNION ALL
    SELECT 'Gold', DATEDIFF('second', MAX(MINUTE_BUCKET), CURRENT_TIMESTAMP())
    FROM {DB}.{SCHEMA}.GOLD_SERVICE_HEALTH
    UNION ALL
    SELECT 'Serving', DATEDIFF('second', MAX(MINUTE_BUCKET), CURRENT_TIMESTAMP())
    FROM {DB}.{SCHEMA}.SERVICE_HEALTH_SERVING
"""
fresh_df = q(freshness_sql)

cols = st.columns(4)
for i, row in fresh_df.iterrows():
    cols[i].metric(row["LAYER"], f'{row["SECONDS_BEHIND"]}s behind')

# ---------- Panel 2: live raw feed ----------
st.subheader("Live Raw Event Feed (Bronze)")

raw_df = q(f"""
    SELECT
        RAW_PAYLOAD:service::STRING     AS SERVICE,
        RAW_PAYLOAD:level::STRING       AS LEVEL,
        RAW_PAYLOAD:status_code::NUMBER AS STATUS_CODE,
        RAW_PAYLOAD:endpoint::STRING    AS ENDPOINT,
        DATEDIFF('second', LANDED_AT, CURRENT_TIMESTAMP()) AS SECONDS_AGO
    FROM {DB}.{SCHEMA}.BRONZE_SERVICE_EVENTS
    ORDER BY LANDED_AT DESC
    LIMIT 15
""")
st.dataframe(raw_df, use_container_width=True, hide_index=True)

# ---------- Panel 3: error rate + latency by service ----------
st.subheader("Error Rate & P95 Latency by Service (last 5 minutes)")

health_df = q(f"""
    SELECT
        SERVICE,
        SUM(REQUEST_COUNT) AS REQUESTS,
        SUM(ERROR_COUNT) AS ERRORS,
        DIV0(SUM(ERROR_COUNT), SUM(REQUEST_COUNT)) AS ERROR_RATE,
        MAX(P95_LATENCY_MS) AS P95_LATENCY_MS
    FROM {DB}.{SCHEMA}.SERVICE_HEALTH_SERVING
    WHERE MINUTE_BUCKET >= DATEADD('minute', -5, CURRENT_TIMESTAMP())
    GROUP BY SERVICE
    ORDER BY ERROR_RATE DESC
""")

if not health_df.empty:
    worst = health_df.iloc[0]
    st.warning(
        f"Worst service right now: **{worst['SERVICE']}** — "
        f"{worst['ERROR_RATE']:.1%} error rate, P95 latency {worst['P95_LATENCY_MS']:.0f}ms"
    )

    left, right = st.columns(2)
    left.bar_chart(health_df.set_index("SERVICE")["ERROR_RATE"])
    right.bar_chart(health_df.set_index("SERVICE")["P95_LATENCY_MS"])
    st.dataframe(health_df, use_container_width=True, hide_index=True)
else:
    st.info("No health data yet — start the producer and wait for Gold to refresh.")

time.sleep(REFRESH_SECONDS)
st.rerun()
