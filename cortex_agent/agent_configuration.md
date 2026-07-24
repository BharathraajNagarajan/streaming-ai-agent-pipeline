# Cortex Agent Configuration — RetailPulse SRE Co-Pilot

Cortex Agents are configured through Snowsight (**AI & ML \u2192 Agents**), not
through a SQL script checked into this repo — this file documents the
configuration so it's reviewable and reproducible by hand.

## Grounding

The agent is grounded on `semantic_views/service_health_semantic_view.sql`
(`SERVICE_HEALTH_SV`), not on raw tables directly. At demo scale (a handful
of tables) an agent can usually find the right data by exploring raw schemas.
That stops being true once an account has thousands of tables — grounding in
a semantic view keeps token cost down and removes the guesswork about what a
column actually means.

## Instructions given to the agent

```
You are an on-call SRE co-pilot for RetailPulse, a consumer shopping app.
You have access to SERVICE_HEALTH_SV, which reports request volume, error
rate, and P95 latency per service per minute.

When asked about service health, query the semantic view rather than
guessing. When a service is degrading, summarize the likely cause using
recent error messages from that service, and offer concrete next steps.
When asked for a root-cause report, structure it as: summary, start time,
impact, timeline, suspected root cause, and recommended next steps.
```

## Model

Left on **auto** by default so Snowflake selects a model available to the
account. To pin a specific model, set it explicitly under
**Configuration \u2192 Model** in the agent's Snowsight page (e.g. the latest
Claude Sonnet).

## Where to talk to it

Snowsight \u2192 **AI & ML \u2192 Agents \u2192 RETAILPULSE_SRE** \u2192 the chat panel on
the agent's own detail page (sometimes labeled **Preview**). Not the generic
assistant in Snowsight's sidebar — that one doesn't know this agent, its
grounding, or RetailPulse's services.

## Publishing

An agent only needs to be **Published** once you're satisfied with its
answers and want to share it with other users in the account. During
development, the Preview panel is sufficient — see `sample_prompts.md` for
the walkthrough used to validate this one.
