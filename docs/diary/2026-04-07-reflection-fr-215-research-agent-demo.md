# FR-215: Reflection — Research Agent Demo

**Date:** 2026-04-07
**FR:** FR-215
**Scope:** `examples/demos/research-agent/` — 5-step agentic pipeline demo

---

## What happened

Built a research agent demo implementing the canonical 5-step agentic pattern (Extract Intent → Plan → Execute → Validate → Respond) using `type: agent` and `type: llm` nodes in pure YAML. The demo proves that bounded, tool-using agents can perform multi-phase research entirely through declarative configuration.

---

## Cognitive trap: infrastructure_self_exempt

The `demo-proof-check` hook caught `examples/demos/tests/` as a "demo" because the path matched `examples/demos/[^/]+/`. The `tests/` directory is test infrastructure, not a demo — but the hook didn't distinguish. This is the **infrastructure_self_exempt** trap: the guardrail tool itself had a gap. Fixed by excluding `tests/` from the demo detection pattern.

---

## Heuristic: boundary exclusions need explicit allowlists

When writing path-based enforcement scripts, enumerate what is NOT the target (test infrastructure, shared utilities) rather than assuming everything under a parent path is uniform. The regex `[^/]+` is too greedy when sibling directories serve different purposes.

---

## Seed

Can the demo-proof hook be made graph-aware — only requiring `demo-output.log` when a `graph.yaml` exists in the directory — rather than relying on path exclusion heuristics?
