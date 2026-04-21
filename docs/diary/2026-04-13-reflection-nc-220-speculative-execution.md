# Reflection: NC-220 Speculative Extraction — The Concurrent Actor Trap

**Date:** 2026-04-13
**Trigger:** NC-220 (speculative extraction during VAD silence) implemented, caused 4-bug cascade, rolled back via NC-227. User asked to consider speculative LLM execution as framework-supported feature.

## Cognitive Process

NC-220's *insight* was correct: the VAD silence confirmation phase (1.5–3s) is dead time where the LLM could already be processing. Promoting this hidden phase to an explicit FSM state (`graph_vad_confirming`) was clean design — debuggable, traceable, standard action lifecycle.

The *implementation* failed because it introduced a second concurrent actor (the speculative `yamlgraph_async` task) that shared mutable state (the LangGraph checkpoint) with the primary actor (`graph_processing`). Four bugs cascaded:

1. **Flag lifecycle** — `_call_min_silence_fired` never cleared across cycles
2. **Action ordering** — `accumulate_text` orphaned its own sibling's guard on the same entry transition
3. **State clearing** — `yamlgraph_async` cleared `accumulated_utterance`, breaking silence_detector's pre-speech logic
4. **Missing transitions** — `ack_speaking` had no transitions for result events arriving during ack TTS

Each fix revealed a deeper layer. The terminal discovery: NC-226 showed that concurrent tasks racing on the same `thread_id` corrupt the LangGraph checkpoint — 3x duplicate LLM calls per turn.

## The Trap: Downstream Fix

Every bug fix was a **downstream fix** — patching symptoms where they manifested rather than addressing the root cause. The Knowledge Graph calls this `downstream_fix`: "Guard added where symptom manifests → normalize at entry boundary instead."

The boundary here is the **checkpoint**. NC-220 violated the One Law: "Normalize at the boundary where external data enters, not downstream where it manifests." The concurrent actor *entered* through the checkpoint boundary without checkpoint isolation. No amount of flag-fixing, transition-adding, or action-reordering downstream could fix this.

## The Pattern: Speculative Execution Requires Resource Forking

NC-226's diagnosis is architecturally fundamental:

- **Speculative execution requires:** advancing state concurrently, with the option to discard
- **Interrupt-based graphs require:** exclusive sequential checkpoint access
- **These are contradictory** when the checkpoint is shared

The fix cascade (flag → action order → param → transition → checkpoint) is a diagnostic fingerprint: when each fix reveals a deeper bug in the same subsystem, the root cause is at the resource ownership level.

**Graduated heuristic:** Before adding a concurrent actor to any system, verify it has exclusive ownership of every shared mutable resource it touches — or fork the resource.

## Framework Opportunity: Speculative Node Type

NC-220 failed because it was implemented at the application layer (ninchat_voice FSM) where checkpoint isolation is impossible. But the *pattern* — "fire LLM optimistically, use result if still valid, discard if invalidated" — is universally useful:

- Voice bots: start extraction during VAD silence
- Chat UIs: pre-generate likely follow-up responses
- Multi-step workflows: speculatively process the most likely branch
- Approval flows: pre-compute result while waiting for human approval

YAMLGraph already has the building blocks:
- **Subgraph nodes** create isolated thread_id namespaces (`parent:child`)
- **Map nodes** provide fork/join with reducer-based fan-in
- **`skip_if_exists`** provides idempotent resume
- **`task_generation`** provides stale result gating

What's missing: a **speculative node type** that:
1. **Forks the checkpoint** — runs on `{thread_id}:spec:{gen}` (subgraph pattern)
2. **Is cancellable** — discards fork on invalidation signal
3. **Promotes on success** — merges fork into parent checkpoint on acceptance
4. **Is declarative** — expressed in YAML, not custom Python coordination

```yaml
# Hypothetical syntax
nodes:
  speculative_extract:
    type: speculative
    graph: medical_triage          # subgraph to run speculatively
    trigger: min_silence_reached   # when to start spec execution
    cancel_on: transcribed         # when to discard
    accept_on: speech_complete     # when to promote fork to real checkpoint
    thread_suffix: "spec"          # checkpoint isolation namespace
    state_key: speculative_result
```

### Why Framework, Not Application

NC-220 proves that speculative execution requires checkpoint-level coordination that the application layer cannot safely provide. The four-bug cascade and NC-226 checkpoint corruption are *inherent* to doing this outside the framework. The framework owns the checkpointer; only the framework can fork/promote/discard checkpoint branches safely.

### Relationship to Existing Primitives

| Existing Primitive | Speculative Analogue |
|---|---|
| Subgraph thread isolation | Spec fork namespace |
| Map fan-out/fan-in | Spec launch/promote |
| `task_generation` stale gating | Spec cancel/discard |
| `skip_if_exists` idempotency | Spec result reuse |

The speculative node is not a new concept — it's the *composition* of existing primitives into a coherent concurrent execution pattern with proper resource isolation.

### LangGraph Checkpoint Branching

LangGraph doesn't natively support checkpoint fork-and-promote. Implementing this requires either:
- **Option A:** Disposable namespace + replay — fork to `{thread_id}:spec`, on acceptance replay the state delta onto the real checkpoint
- **Option B:** Custom checkpointer with branching — store/restore checkpoint snapshots, promote branch atomically
- **Option C:** Stateless speculation — extract without advancing checkpoint (works for extraction, not for interrupt-resume patterns)

Option C is simplest and covers the NC-220 use case: the speculative call extracts fields from text without needing to resume from an interrupt. The extraction result is pure output — the checkpoint is never touched.

## Traps Encountered

| Trap | Instance |
|---|---|
| `downstream_fix` | 4 consecutive fixes patching symptoms of shared checkpoint |
| `quick_confidence` | NC-220 v2 approval felt solid — explicit states, standard actions — but missed the checkpoint concurrency angle |
| `partial_remediation` | Each bug fix addressed one symptom, not the concurrent actor root cause |
| `working_system_inertia` | After bug 1 fix "worked", pushed forward instead of questioning the design |

## What Survived the Rollback

- NC-220 A1: Generalized `_graph_running_*` prefix scan — independently correct, re-applied standalone
- NC-226: Documentation of checkpoint isolation problem — preserved for future reference
- The graduated heuristic: concurrent actor → exclusive resource ownership → or fork

**Seed:** Can a `type: speculative` node in yamlgraph provide checkpoint-forked execution that the application layer provably cannot implement safely? If so, what is the minimal LangGraph checkpointer extension needed — and does Option C (stateless speculation) cover 80% of use cases without any checkpointer changes?
