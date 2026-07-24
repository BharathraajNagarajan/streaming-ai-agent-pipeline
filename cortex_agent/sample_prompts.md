# Sample Prompts — RetailPulse SRE Co-Pilot

A representative session, used to validate the agent after wiring it up to
`SERVICE_HEALTH_SV`. Run these in order against the agent's Preview panel in
Snowsight, ideally while `producer/log_producer.py` is running with
`--fault inventory_cascade`.

## 1. Baseline check (before triggering a fault)

> In the last 5 minutes, what is the error rate and P95 latency for each service?

Expected: a per-service table pulled live off `SERVICE_HEALTH_SV`, all
services near their normal baseline. This confirms the agent is actually
querying live data rather than reciting something static.

## 2. After triggering the fault

Restart the producer with `--fault inventory_cascade --fault-after 30`, wait
roughly a minute for Silver/Gold to reflect it, then ask:

> In the last 5 minutes, which service is the worst right now?

Expected: `inventory-service` called out, with its error rate and P95
latency, worse on both dimensions than any other service.

## 3. Root cause

> What's the likely root cause for inventory-service right now?

Expected: a plausible explanation referencing `warehouse-api` timeouts and
the `dependency`/`message` fields carried through from the raw events —
inferred from the data itself, without being told the architecture.

## 4. Mitigation

> What should I check first to mitigate this?

Expected: concrete, generic-but-relevant SRE next steps — check the
downstream dependency's health, consider a circuit breaker, check
connection-pool exhaustion.

## 5. Incident report

> Draft a root-cause report for my team: summary, impact, timeline, suspected
> root cause, and next steps.

Expected: a structured RCA suitable for pasting into a Slack channel or an
incident ticket, generated entirely from the live streaming data.
