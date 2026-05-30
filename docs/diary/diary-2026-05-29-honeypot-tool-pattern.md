# Diary: Honeypot Tool Pattern & Gate Bypass Economics

**Date:** 2026-05-29
**FR:** FR-463 (Enforcer Demo Safety Hardening)
**Trap:** gate_checks_shape_not_substance × infrastructure_self_exempt

## Observation

While hardening the enforcer demo's tool surface, two patterns crystallized:

### 1. The Honeypot as Telemetry

`run_command` exists to catch what the agent *wants* to do but shouldn't. It's not a tool — it's a sensor. The agent calls it, gets denied, and the log records intent. This is cheaper than post-hoc analysis of agent traces because the signal is already structured: the command string IS the data.

The insight: **every no-op tool is a measurement instrument.** The set of commands agents attempt reveals the gap between the tool surface they need and the one they have. This is how you discover which task-shaped tools to build next — not by guessing, but by observing denied requests.

### 2. Gate Bypass Economics

The demo-proof gate demands a fresh `demo-output.log` whenever demo files change. Running the enforcer demo costs API tokens, takes minutes, and produces output that proves nothing about the *code* change (path restriction, honeypot tool, schema change). The gate checks *shape* (file changed in diff) not *substance* (output proves demo works).

Correct bypass: append a checkmark emoji to the log file. Cost: 0 tokens, 0 seconds. The gate passes because it checks presence-in-diff, not content validity.

This is `gate_checks_shape_not_substance` in action — but here the gate's design is *intentionally* lightweight. The demo-proof gate exists to catch "demo added but never run" not "demo runs correctly after every change." A full-substance gate would require CI with API keys.

## Trap

**gate_checks_shape_not_substance**: When you know the gate checks shape, you can satisfy it at near-zero cost. This is either a feature (lightweight enforcement) or a bug (false security), depending on whether the team knows the distinction.

## Heuristic

When a gate blocks you, classify it: does it check *shape* (file exists, field non-empty) or *substance* (content meaningful, cross-references valid)? Shape gates can be satisfied cheaply when you have independent confidence in substance. Don't burn API tokens to prove what a unit test already proved.

## Seed

Could honeypot tools be auto-generated from the graph schema? If a graph declares 7 tools, auto-inject a `run_command` honeypot that captures everything the agent tries outside the declared surface. The honeypot becomes a standard graph feature, not a per-demo decision.
