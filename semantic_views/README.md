# semantic_views/

The business-context layer that sits between `SERVICE_HEALTH_SERVING` (raw
columns) and the Cortex Agent (natural-language questions).

## Why this exists

An LLM agent can technically query raw tables directly, but at any
non-trivial scale that means burning tokens (and risking wrong guesses) on
"which table has error rate, and what does `ERROR_RATE` actually mean here?"
A semantic view answers that once, explicitly, so every future question is
grounded in a reviewed definition instead of an inference.

## File

- `service_health_semantic_view.sql` — defines `SERVICE_HEALTH_SV`: which
  columns are dimensions (`SERVICE`, `MINUTE_BUCKET`) vs. facts
  (`REQUEST_COUNT`, `ERROR_COUNT`, `ERROR_RATE`, `P95_LATENCY_MS`), the
  aggregate metrics built on top of them, and natural-language synonyms
  ("latency", "traffic", "failure rate") so the agent can match casual
  phrasing to the right column.

## Important caveat

This file is authored as a reasonable starting point for a demo dataset —
not a production-ready governance artifact. In a real deployment, metric
formulas and synonyms should be reviewed and signed off by whoever owns the
actual business definitions (what counts as an "error," which latency
percentile matters, etc.) before an agent is allowed to treat this as ground
truth. See `docs/production_considerations.md`.
