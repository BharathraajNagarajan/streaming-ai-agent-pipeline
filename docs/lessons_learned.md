# Lessons Learned

Building this from scratch (rather than just following the original lab
click-by-click) surfaced a few things worth writing down:

- **Declarative transformation is a bigger shift than it first looks.**
  Writing `TARGET_LAG = '1 minute'` instead of a scheduled Spark job removes
  an entire category of orchestration bugs — but it also means giving up
  fine-grained control over exactly how the incremental refresh executes.
  That's a real trade-off, not a strict upgrade.
- **Dedup logic has to live somewhere, and it might as well be explicit.**
  Snowpipe Streaming makes no promise about exactly-once delivery, so Silver
  needs a `ROW_NUMBER() ... QUALIFY RN = 1` (or equivalent) from day one, not
  as an afterthought.
- **A semantic view is a governance artifact wearing a technical hat.** It
  was tempting to treat `service_health_semantic_view.sql` as "just some more
  SQL" — but every synonym and metric formula in it directly shapes what the
  agent tells an on-call engineer during an actual incident. That deserves
  the same review rigor as a schema migration, not less.
- **Insert-only is the default, and that's fine — as long as you plan for
  it.** The instinct is to look for an "UPDATE" story immediately; the more
  useful question is "where does reconciliation happen downstream," which
  Dynamic Tables answer cleanly here.
