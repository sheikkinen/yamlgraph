---
type: feat
scope: map
req: REQ-YG-689
---
- **FR-1065 Resumable map investigation witnesses**: minimal LangGraph probes (`tests/fixtures/fr1065/probes.py`) and 12 witness tests pin what a resumable map can rely on today. `kill -9` during a one-step map re-runs every branch that had already finished, because branch writes reach the checkpointer only when the step ends; a batch loop bounds the loss to the open batch and cuts peak memory at 10,000 items from 77 MB to 4–5 MB. Keeping results out of state shrinks the final checkpoint about 82×. `SqliteCache` is rejected as a durable result store and as a lock (a second process can crash on a fresh file; get-then-set gives no exclusion); a SQLite `UNIQUE`-insert lease is selected. A new thread reuses nothing. FR-032's `cache:` is recorded as inert: no `yamlgraph/` route passes `cache=` to `compile()`. Report: `docs/investigations/fr1065-resumable-map.md`. No production code changed. (REQ-YG-689)
