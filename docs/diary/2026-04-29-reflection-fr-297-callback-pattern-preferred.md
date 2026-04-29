# Diary: FR-297 Navigator + callback_* Is the Preferred Pattern

**Date:** 2026-04-29
**FR:** FR-297
**Outcome:** Enforced (callback_marketing replaces probe_recap marketing graph)

## Cognitive Process

FR-297 started with a probe_recap-based marketing graph. The probe_recap pattern
uses `transcript` as state key and relies on first-turn routing (`transcript == ""`
vs `transcript != ""`) to decide whether to probe or extract. This seemed reasonable
in isolation — until plugged into the navigator FSM.

The FSM's `yamlgraph_async` action passes `input_key: user_message` and
`input_value: "{accumulated_utterance}"`. The graph state key `transcript` never
receives data. Because Python evaluates `None != ""` as `True`, the graph skipped
the opening and jumped straight into extraction with no input — crashing immediately.

The fix was not to patch the probe_recap pattern. The fix was to discard it entirely
and reimplement as `callback_marketing` using the interrupt-based `callback_*` pattern
that already works in production (`callback_other_topic`, `callback_soittopyynto`).

## Trap Encountered

**downstream_fix** — The first instinct was to rename `transcript` → `user_message`
in the probe_recap graph. But probe_recap's architecture is fundamentally different:
it accumulates a full transcript and re-processes it each turn. The callback_* pattern
processes incremental user messages via interrupts with checkpointed state. Renaming
the key would have hidden the architectural mismatch.

**working_system_inertia** — The probe_recap pattern "worked" in standalone testing
(where transcript was injected directly). This blocked seeing that it was the wrong
pattern for the FSM integration boundary.

## Heuristic

**The navigator FSM + callback_* interrupt pattern is the preferred architecture
for all voice questionnaire graphs.** This should be the default choice, not an
alternative. Key reasons:

1. **FSM contract alignment**: The FSM passes `input_key: user_message` — callback_*
   uses `user_message` as state key with `resume_key: user_message` on interrupts.
   No translation layer needed.
2. **Incremental processing**: Each turn processes one user message, not the full
   transcript. Cheaper, faster, no re-extraction drift.
3. **Schema-driven**: Field definitions live in `schema.yaml`, not in pipe-delimited
   env vars. Structured, validatable, versionable.
4. **Proven in production**: callback_other_topic and callback_soittopyynto run
   live calls daily.
5. **Checkpointed state**: Interrupt-resume with memory checkpointer preserves
   extraction progress across turns without re-parsing.

Any new voice questionnaire graph should clone `callback_other_topic/` and adapt —
never start from probe_recap.

## Seed

Should the probe_recap pattern be formally deprecated in ninchat_voice, with a
lint rule or pre-commit check that flags new graphs using `transcript` as state key
when `user_message` is the FSM contract?
