---
type: feat
scope: cli
req: REQ-YG-671
---
- **FR-1028 `graph run --provider/--model` override of graph defaults**: two
optional flags override the root graph's `defaults.provider` / `defaults.model`
at the load boundary (`load_graph_config(provider_override=, model_override=)`
→ `yamlgraph/compile/default_overrides.py`, copy-not-mutate); explicit per-node pins keep precedence and provider/model
resolve independently; graph-tool child graphs are unaffected.
`scripts/research.sh` forwards the `RESEARCH_PROVIDER`/`RESEARCH_MODEL` pair
(half-set exits 64 before the executor) and stamps exactly one
`- provider/model:` line into the draft artifact, which
`research_preflight.py --verify-artifact` validates. (REQ-YG-671)
