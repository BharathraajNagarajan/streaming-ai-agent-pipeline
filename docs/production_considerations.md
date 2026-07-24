# Production Considerations

This project is a learning/demo pipeline. Several things are deliberately
simplified, and would need to be addressed before anything like this ran
against real services:

## Security

- **Single role for everything.** `STREAMING_PIPELINE_ROLE` both ingests and
  reads. In production, split this: an ingest-only role for the producer, a
  read-only role for the dashboard, a separate role for the agent.
- **PAT stored in a local JSON file.** Fine for a demo; in production, use
  RSA key-pair (JWT) auth backed by a real secrets manager, not a token file
  on disk. (Snowflake's own Snowpipe Streaming quickstart defaults to
  key-pair auth for exactly this reason.)
- **Network policy allows `0.0.0.0/0`.** Should be scoped to known egress
  IP ranges.

## Data quality

- **No schema registry / contract enforcement.** A real deployment reading
  from Kafka would use the Kafka Connector's client-side schema validation,
  or Snowflake's server-side error table (a DLQ for schema mismatches), so
  malformed events are captured and reviewed rather than silently dropped.
- **No CDC.** Snowpipe Streaming is insert-only — this project never needs
  to update or delete an event, but a real source system would. That needs
  a CDC tool (e.g. Debezium) upstream, merged downstream via a Dynamic Table
  or a scheduled `MERGE` task.

## Operations

- **No CI/CD.** SQL objects here are applied by hand. In production, these
  would be version-controlled and deployed through a pipeline (dbt, or plain
  SQL migrations run via GitHub Actions).
- **No infrastructure as code.** Warehouse, database, and role definitions
  would be managed via Terraform rather than a bootstrap script run once by
  hand.
- **No monitoring/alerting.** Nothing here watches ingestion lag, error-table
  volume, or agent answer quality over time — all necessary before trusting
  this in an actual on-call rotation.

## Governance

- **Semantic view needs sign-off.** `service_health_semantic_view.sql` is a
  reasonable starting point, but the metric definitions and synonyms should
  be reviewed by whoever owns the real business definitions before an agent
  is allowed to treat it as ground truth in production.

## Known Limitations / Verify Before Running

A few things in this repo are best-effort reconstructions rather than
verified against Snowflake's current SQL reference, because Interactive
Tables and Semantic Views were newer/preview-era features at the time this
was written:

- **`sql/00_bootstrap.sql`** grants `CREATE TABLE, CREATE DYNAMIC TABLE,
  CREATE STREAMLIT, CREATE STAGE, CREATE SEMANTIC VIEW` but not whatever
  privilege governs creating an Interactive Table — `04_interactive_table_serving.sql`
  will likely fail on privileges alone until this is confirmed and added.
- **`CREATE INTERACTIVE TABLE ... AS SELECT`** in
  `sql/04_interactive_table_serving.sql` is written to match how the concept
  was described, not copied from a confirmed SQL reference. If Interactive
  Tables require a primary key or unique constraint for their low-latency
  guarantees (similar to Hybrid Tables), this DDL doesn't declare one.
- **`CREATE SEMANTIC VIEW`** in `semantic_views/service_health_semantic_view.sql`,
  including whether `METRICS` should reference `FACTS` by their declared
  alias rather than re-deriving from the base table column, is unverified.
- **`PERCENTILE_CONT` inside a Dynamic Table** (`sql/03_gold_service_health.sql`)
  is valid SQL, but percentiles can't be incrementally maintained — Gold is
  likely doing a full recompute every refresh cycle rather than a true
  incremental one. Functionally correct, just worth knowing it's not free.
- **The dashboard's "P95 Latency" panel** (`streamlit/app.py`) takes
  `MAX()` of five already-computed per-minute P95 values over a 5-minute
  window, which is not the same number as a true P95 over that window. It's
  a reasonable approximation for a demo but shouldn't be read as an exact
  statistic.

None of these block the pipeline from being *understood* — they're flagged
here so they get verified against a live account before being presented as
"tested and working," rather than discovered by someone else first.



## Cortex Agent: A Real Platform Limitation Hit During Testing

The Cortex Agent (`RETAILPULSE_SRE`) is fully built and configured — grounded
on `SERVICE_HEALTH_SV`, with orchestration and response instructions set —
but live chat queries against it consistently return:

> `Error: Access denied for trial accounts.`

This was investigated methodically rather than assumed:

- **Cross-region inference** — enabled (`ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'`), no change
- **`ENABLE_CORTEX_ANALYST`** — confirmed already `TRUE` at the account level, no change
- **Model swap** — tested across three different models from three different providers (Claude, OpenAI-family, Gemini-family), same error on all three, ruling out a single-model restriction

This points to Cortex Agents being gated at the account-entitlement level for
standard self-serve trial accounts specifically — not a configurable setting.
Snowflake's own VHOL session (the inspiration for this project) used a
special AI-enabled trial invite, not the public signup flow used here, which
likely carries different entitlements.

**What this means practically:** the semantic view layer is proven working
end-to-end (`SEMANTIC_VIEW()` queries return correct results — see
`screenshots/05_semantic_view.png`), and the agent is fully configured and
ready to serve queries the moment it's running on an account with the right
entitlement (a paid/ODSS account, or a Snowflake-provisioned AI trial). The
gap here is a platform access boundary, not a gap in the implementation.