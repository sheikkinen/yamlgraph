---
type: feat
scope: examples
req: REQ-YG-584
---
- **FR-782 User Self-Portrait Example**: `examples/demos/self-portrait/` — macOS PersonalizationPortrait → typed rows → consented LLM synthesis → agent-first portrait (`self-portrait.json` + `agent_briefing`, narrative and diff as secondary renderings). Read-only SQLite with drift asserted at the boundary (named FDA remediation, `SchemaDriftError` on unknown categories/missing tables), stdlib-only batched+cached Wikidata label resolution, supplementary DBs as availability probes only, and an exact-payload consent gate: the outbound JSON is written and hashed before the interrupt, then re-verified byte-for-byte before any provider call (`auto_approve=true` is the only opt-in bypass). Every path in the payload is home-relative and `SELF_PORTRAIT_PROBE_HOME` points fixture/demo/test runs at a synthetic home, so neither the account name nor real database availability can reach the provider or the repository. Ships a deterministic synthetic fixture and a no-real-data guard — never a real portrait. (REQ-YG-584)
