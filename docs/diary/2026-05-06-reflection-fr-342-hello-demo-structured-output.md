# Reflection: FR-342 Structured Hello Output

**Date:** 2026-05-06
**FR:** FR-342
**Branch:** feat/watcher2-gh-342

## What was done

Added an inline `schema:` to `examples/demos/hello/prompts/greet.yaml` to return structured output
(`greeting`, `emoji`, `formality_level`). Updated demo artifact, README, and directly-coupled tests.

## Cognitive traps encountered

**working_system_inertia** — The hello demo "worked" (returned text) so the absence of a schema was easy
to overlook. Inventory of _fit_ (typed contract) vs _function_ (non-empty output) revealed the gap.

**scope_creep temptation** — Similar greet prompts exist in `hellograph-speed` and `mastra-integration`.
The impulse to update them all at once was resisted; the FR explicitly bounds scope to the canonical
hello demo only.

## Heuristics learned

- The smallest demo is the highest-signal: if the canonical starter lacks a typed contract, every user
  who follows it learns untyped habits from the start.
- Demo-gate + diary-gate enforce proof before merge; writing the `demo-output.log` first surfaced a
  test assertion mismatch that would have been invisible in batch CI.

## Seed

Could a static analyser scan all `prompts/*.yaml` files and flag those missing a `schema:` block,
producing a coverage report analogous to `req_coverage.py`? This would make "typed prompt" a
continuously enforced property rather than a per-FR audit item.
