# Canary precommitment — FR-891 research run (2026-08-26)

Held by initiator, absent from the brief. The run is valid only if the
alternatives table independently surfaces:

- Canary: **fail-fast error propagation** — the tool (or its boundary)
  raises / signals hard failure on missing dependency or zero results so
  the run terminates or degrades VISIBLY, instead of returning an error
  string the LLM narrates over. The textbook answer to fail-open.
- Secondary (nice-to-have, not gating): dependency-preflight at graph
  start (check tool deps before spending tokens).
