# producer/

A synthetic log producer that simulates request-level logs from eight
fictional RetailPulse microservices and streams them into Snowflake via the
**Snowpipe Streaming Python SDK**.

## Files

| File | Purpose |
|---|---|
| `log_producer.py` | The producer itself — event generation, fault injection, and the streaming client |
| `profile.example.json` | Template for the connection profile. Copy to `profile.json`, fill in your account identifier and PAT, and **never commit the real file** (`profile.json` is gitignored) |
| `requirements.txt` | Python dependency: the `snowpipe-streaming` SDK |

## How it connects

```
log_producer.py --profile profile.json
        │
        │  StreamingIngestClient.open_channel()
        ▼
BRONZE_SERVICE_EVENTS-streaming   (auto-created default pipe)
        │
        ▼
BRONZE_SERVICE_EVENTS   (Snowflake table, see sql/01_bronze_raw_events.sql)
```

Each call to `channel.append_row()` sends one JSON event over an open
streaming channel. No staging files, no `COPY INTO`, no explicit pipe — rows
are typically queryable within seconds.

## Running it

```bash
python -m venv .venv
source .venv/bin/activate          # .venv\Scripts\activate on Windows
pip install -r requirements.txt

cp profile.example.json profile.json
# edit profile.json: account identifier + PAT from sql/00_bootstrap.sql

# healthy traffic
python log_producer.py --profile profile.json --rps 200

# trigger a cascading fault on inventory-service after 30s
python log_producer.py --profile profile.json --rps 200 \
    --fault inventory_cascade --fault-after 30

# try it with no Snowflake connection at all
python log_producer.py --dry-run --fault inventory_cascade --fault-after 10
```

## Fault scenarios

Two scenarios are built in (`FAULTS` dict in `log_producer.py`):

- **`inventory_cascade`** — `inventory-service` starts timing out against a
  simulated `warehouse-api` dependency: error rate and P95 latency climb.
- **`auth_cascade`** — `auth-service` backs up against a simulated
  `identity-provider`.

Both exist to give the Silver/Gold Dynamic Tables, the Streamlit dashboard,
and the Cortex Agent something real to detect and explain — see
`docs/incident_walkthrough.md`.
