# Agent Grounding Flow

```mermaid
flowchart TD
    A[SERVICE_HEALTH_SERVING<br/>Interactive Table] --> B[SERVICE_HEALTH_SV<br/>Semantic View]
    B -->|facts, dimensions,<br/>metrics, synonyms| C[Cortex Agent<br/>RetailPulse SRE Co-Pilot]
    D[On-call engineer question:<br/>'which service is worst right now?'] --> C
    C --> E[Agent queries semantic view,<br/>not raw tables]
    E --> F[Natural-language answer +<br/>optional RCA report]
```

The agent never sees `SERVICE_HEALTH_SERVING`'s raw column names directly —
it reasons in terms of the facts, dimensions, and metrics the semantic view
exposes. This is what keeps answers grounded and keeps token spend down as
the number of underlying tables grows well past what fits in a demo account.
