# System Architecture

```mermaid
flowchart TD
    A[RetailPulse Services<br/>synthetic log producer] -->|Snowpipe Streaming SDK<br/>append_row| B[BRONZE_SERVICE_EVENTS<br/>raw, insert-only, ~seconds]
    B -->|Dynamic Table<br/>target lag 1 min| C[SILVER_SERVICE_EVENTS<br/>typed, deduped, filtered]
    C -->|Dynamic Table<br/>target lag 1 min| D[GOLD_SERVICE_HEALTH<br/>per-service, per-minute metrics]
    D --> E[SERVICE_HEALTH_SERVING<br/>Interactive Table]
    E --> F[SERVICE_HEALTH_SV<br/>Semantic View]
    E --> G[Streamlit Dashboard]
    F --> H[Cortex Agent<br/>RetailPulse SRE Co-Pilot]
    H --> I[AI Answer /<br/>Root Cause Report]
    G --> J[On-call Engineer]
    I --> J
```

Bronze is insert-only and typically queryable within seconds of being
streamed. Silver and Gold are Dynamic Tables — declarative SQL plus a
freshness target, not a scheduled job — refreshing within roughly a minute.
The Interactive Table exists purely to give the dashboard and the agent a
fast, high-concurrency read path that doesn't contend with the Dynamic Table
refresh itself.
