# Medallion Flow: Bronze → Silver → Gold

```mermaid
flowchart LR
    subgraph Bronze
        B1[RAW_PAYLOAD: VARIANT]
        B2[LANDED_AT]
    end
    subgraph Silver
        S1[Flatten JSON to typed columns]
        S2[Filter out HEARTBEAT]
        S3[Dedupe on EVENT_ID,<br/>keep latest by LANDED_AT]
    end
    subgraph Gold
        G1[Group by SERVICE +<br/>1-minute bucket]
        G2[REQUEST_COUNT, ERROR_COUNT,<br/>ERROR_RATE, P95_LATENCY_MS]
    end
    Bronze --> Silver --> Gold
```

Each layer does one job. Bronze never transforms anything — it exists purely
to get data into Snowflake as fast and reliably as possible. Silver is where
correctness lives (types, dedup, noise filtering). Gold is where business
meaning lives (the metrics an SRE or an agent actually cares about).
