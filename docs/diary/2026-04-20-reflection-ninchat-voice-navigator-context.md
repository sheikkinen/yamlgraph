# Diary: Ninchat Voice — Navigator + Triage Context Read

**Date:** 2026-04-20
**Context:** User asked for a status read of the `ninchat_voice` project's live configuration, navigator graph, and triage graph, then a reflection.
**Boundary touched:** `state` (YAMLGraph node output) and `instruction` (human operator reading an `.env` to decide what runs).

## What the read revealed

- Active mode: `NINCHAT_VOICE_MODE=navigator`, bootstrap graph `graphs/navigator/graph.yaml`.
- Provider: `PROVIDER=vertex`, `VERTEX_MODEL=gemini-2.5-flash`, Express-mode auth via `VERTEX_API_KEY` (skips ADC).
- Navigator: 5 nodes — `opening` (interrupt) → `classify` (router: crisis/elderlycare/medical_triage) → three `passthrough` switch nodes emitting `phase: switch_graph` and a `response` string that carries the *next graph path*. The FSM coordinator (`voice_coordinator.yaml`) reads `payload.response` and remounts.
- Triage: schema-driven (`chief_complaint`, `duration`, `recent_changes`) with NC-219's combined extract+probe single-LLM call, loop-protected probe/recap, terminal `send_results` → farewell.

## Trap spotted: convention overloading on `response`

The same state field `response` carries *user-facing utterance* in every node except the switch nodes, where it carries *a YAML file path*. This is the classic downstream-boundary sin: one field, two semantic meanings, disambiguated only by `phase`. A future refactor of the TTS/assistant-utterance path could happily speak `"graphs/medical_triage/graph.yaml"` aloud to a caller. The guard today is purely a convention inside the coordinator YAML.

The cure from the Scripture applies: **normalize at the boundary**. A first-class `next_graph` state field (or a proper `graph_switch` node type with a typed `target:` attribute) eliminates the dual-meaning at the point where the decision is made, not at the point where it manifests.

## Secondary observations

- `default_route: switch_to_triage` in the classifier node duplicates the prompt's own "jos epäselvä, medical_triage" fallback — two fallbacks, one source of truth preferred.
- Crisis branch is the thinnest path despite being the highest-consequence one: a `passthrough` with a single farewell string, no event logged, no human-handoff hook.
- `.env` contains commented alternative `QUESTIONNAIRE_GRAPH` lines as a dispatch mechanism — drift bait. A `config/` profile per mode would be safer than commented directives.
- The live `.env` holds production-tier secrets (Twilio, ElevenLabs, Azure, Tigris, Vertex). Confirmed gitignored, but "ambient file as primary config" is a pattern that leaks via deploy artifacts. Rotation advisable on any doubt.

## Cure

**Spec-kill candidate:** Introduce `graph_switch` as a node type with an explicit `target` attribute, so the Navigator never overloads `response`. Cheapest bug is the one killed in the spec; today's YAML has no syntactic way to prevent speaking a file path.

**Seed:** Should graph-switching events ship with a typed envelope (`{kind: "graph_switch", target: "...", context: {...}}`) rather than being inferred from a `phase` marker plus a string-typed `response` field? If yes, can `voice_coordinator.yaml` be simplified from "read `phase`, interpret `response`" to "dispatch on event kind" — moving the boundary normalization from the coordinator YAML into the graph contract itself?
