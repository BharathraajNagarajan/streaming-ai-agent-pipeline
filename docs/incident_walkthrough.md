# Incident Walkthrough

A worked example of what this pipeline is actually for: catching and
explaining a service degradation quickly, using nothing but the live
streaming data.

## 1. Trigger the fault

```bash
python log_producer.py --profile profile.json --rps 200 \
    --fault inventory_cascade --fault-after 30
```

`inventory-service` starts returning elevated 500s/503s with 2.5–5s latency
against a simulated `warehouse-api` dependency, 30 seconds after start.

## 2. Watch it propagate

- **Bronze** — the first errored events appear within seconds
  (`docs/setup_guide.md` step 3 query, or the dashboard's raw feed panel)
- **Silver / Gold** — within roughly a minute, `GOLD_SERVICE_HEALTH` shows
  `inventory-service`'s `ERROR_RATE` and `P95_LATENCY_MS` climbing
- **Dashboard** — the error-rate bar chart and the "worst service" callout
  update to highlight `inventory-service`

## 3. Ask the agent

Using the prompts in `cortex_agent/sample_prompts.md`:

1. *"Which service is worst right now?"* → `inventory-service` called out
   with its error rate and P95 latency
2. *"What's the likely root cause?"* → an explanation referencing the
   `warehouse-api` dependency and timeout pattern in the raw event messages
3. *"What should I check first?"* → concrete mitigation suggestions
4. *"Draft a root-cause report"* → a structured RCA: summary, impact,
   timeline, suspected cause, next steps

## What this demonstrates

The agent's root-cause hypothesis in step 2 comes entirely from correlating
live log fields (`dependency`, `message`, `status_code`, `latency_ms`) — it
was never given RetailPulse's service architecture. That's the payoff of
pairing fresh streaming data with a semantic layer that tells the agent what
the columns mean.
