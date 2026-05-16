# YAMLGraph × Design Patterns — Integration Brainstorm

*Date: 2026-05-14*

## Already Embedded (native patterns)

| Pattern | YAMLGraph Implementation |
|---------|------------------------|
| **Strategy** | `provider:` swaps LLM backend; `prompt:` swaps behavior |
| **Template Method** | Node factory: pre-check → loop-guard → execute → return |
| **Observer** | LangSmith tracing, streaming callbacks |
| **Chain of Responsibility** | Edge routing, `on_error: skip\|retry\|fallback` |
| **Composite** | Subgraph nodes — graphs contain graphs |
| **Factory Method** | `node_factory/` dispatches by `type:` |
| **State** | Checkpointer + interrupt/resume = FSM persistence |
| **Builder** | `state_builder.py` constructs TypedDict dynamically |

## Unmapped GoF Patterns Worth Exploring

| Pattern | Integration Idea |
|---------|-----------------|
| **Decorator** | Wrap nodes with cross-cutting concerns: logging, caching, retry, rate-limiting — as YAML `decorators:` list |
| **Proxy** | Lazy-load expensive subgraphs; cost-router as proxy for LLM calls |
| **Mediator** | Central state object already mediates; could formalize event bus between nodes |
| **Memento** | Checkpointer IS memento — expose "undo to checkpoint N" in YAML |
| **Visitor** | Graph traversal for lint/audit/visualization — `yamlgraph graph lint` already does this partially |
| **Flyweight** | Shared prompt cache across graph instances (`graph_cache.py` is close) |
| **Command** | Each node invocation as undoable command object — enables replay |

## Game Architecture Patterns

| Pattern | YAMLGraph Mapping |
|---------|-------------------|
| **Game Loop** | `loop_until:` condition on edges = tick-based loop. A "game engine" graph could run `perceive → decide → act → update_world` in a cycle with interrupt for player input |
| **Entity-Component-System** | Entities = state keys, Components = node outputs, Systems = node types. Map nodes already process entity lists in parallel |
| **Event Queue** | Interrupt nodes + checkpointer = event queue with persistence. Could formalize `event_queue:` state key with reducer |
| **Double Buffer** | `draft → review → revised_draft` pattern is double-buffering. The `reflexion_demo` already does this |
| **Service Locator** | `create_llm()` factory + tool registry = service locator |
| **Update Method** | Map nodes call same logic on each entity — classic update method |

## Novel Integration Ideas

### 1. Saga Pattern (distributed transactions)
Each subgraph = saga step with compensating action on failure. Add `compensate:` edge for rollback graphs.

### 2. Circuit Breaker
Track consecutive failures per provider in state; `race` node already has timeout — add `circuit_breaker: {threshold: 3, cooldown: 60s}`.

### 3. CQRS (Command Query Responsibility Segregation)
Separate read-path graphs (RAG, search) from write-path graphs (generation, mutation). State reducers already distinguish append vs overwrite.

### 4. Blackboard Pattern
State IS the blackboard — multiple specialist nodes read/write shared state. Already native but could be made explicit with `knowledge_sources:` declarations.

### 5. Pipes and Filters
Pipeline templates are exactly this. Could add typed port contracts between stages.

### 6. Reactor Pattern
MCP server + graph discovery = reactor dispatching to graph handlers based on tool invocation events.

## Highest-Value Unexplored

| Priority | Pattern | Why |
|----------|---------|-----|
| 🥇 | **Decorator** (node wrappers in YAML) | Most practical, broadest reuse |
| 🥈 | **Game Loop** (cyclic agent with world state) | Most interesting for autonomous agents |
| 🥉 | **Saga** (compensating subgraphs) | Most needed for production reliability |
| 4 | **Command/Memento** (replay + undo) | Checkpointer is 80% there |

---

## Deep Dive: Memento / Command × Speculative Execution

### The Real Problem (ninchat_voice)

In voice telephony, **VAD silence confirmation** takes 1.5–3 seconds after a caller stops speaking. During this dead time the LLM could already be processing. But if the caller resumes speaking, the speculative result must be **discarded** — the utterance changed.

**Pattern:** Fire LLM optimistically → use result if still valid → discard if invalidated.

### Why Memento / Command Fits

| GoF Pattern | Voice Analogue |
|---|---|
| **Command** | Each speculative LLM call is a command object — encapsulates the request, can be cancelled before its result is consumed |
| **Memento** | The generation counter (`speech_gen`) is a memento snapshot — captures "what was true when we started", enables comparing against "what is true now" |

The combination: **Command with Memento-based invalidation.**

### What Failed: NC-220 → NC-226 → NC-227

NC-220 tried to implement speculative execution at the **application layer** (FSM Python code). It launched a second `yamlgraph_async` task sharing the same `thread_id`. Result: 4-bug cascade, 3× duplicate LLM calls, checkpoint corruption.

**Root cause:** Two concurrent actors writing to the same LangGraph checkpoint. Each fix was a *downstream fix* — the trap from the Knowledge Graph.

**The One Law violated:** "Normalize at the boundary where external data enters." The boundary is the checkpoint; speculation entered without checkpoint isolation.

### FR-219: The Framework Solution (Option C — Stateless)

Already approved (`feature-requests/FR-219-speculative-node-type.md`). Two YAML constructs:

```yaml
nodes:
  # Fire during VAD silence — partial text available
  spec_extract:
    type: speculative
    prompt: extract_intent
    variables:
      text: "{state.partial_utterance}"
    result_key: spec_extraction
    generation_key: speech_gen         # memento: snapshot gen at launch

  # After silence confirmed — consume spec result or re-run
  extract_intent:
    type: llm
    prompt: extract_intent
    variables:
      text: "{state.transcription}"
    state_key: extraction
    accept_speculative: spec_extraction  # command: consume or discard
    generation_key: speech_gen

  # Any new speech bumps generation → invalidates stale spec results
  new_speech_received:
    type: passthrough
    output:
      speech_gen: "{state.speech_gen + 1}"  # memento: new snapshot
```

**Lifecycle:**
1. VAD silence starts → `spec_extract` fires, snapshots `speech_gen=3`, stores result + `_spec_gen_spec_extraction=3`
2a. Silence confirmed → `extract_intent` reads `_spec_gen=3`, current `speech_gen=3` → match → **skip LLM, promote spec result** (Command executed)
2b. Caller resumes → `new_speech_received` bumps `speech_gen=4` → `extract_intent` reads `_spec_gen=3 ≠ 4` → **discard, run fresh LLM** (Command cancelled)

### Why This IS Memento + Command

| Concept | Implementation |
|---|---|
| **Memento (snapshot)** | `_spec_gen_{key}` — the generation counter frozen at speculation time |
| **Memento (restore check)** | Compare `_spec_gen` vs current `generation_key` — "has the world changed since I started?" |
| **Command (execute)** | `accept_speculative` promotes spec result to `state_key` — command completes |
| **Command (cancel)** | Generation mismatch → spec result ignored, fresh LLM call → command discarded |
| **Caretaker** | The graph itself — orchestrates when to snapshot, when to validate, when to discard |

### What's Still Missing (Future Options)

| Option | Pattern | Coverage | Complexity |
|---|---|---|---|
| **C (FR-219)** | Stateless spec — gen counter | ~80% of cases (extraction) | Zero checkpointer changes |
| **A (deferred)** | Fork checkpoint namespace | Full (incl. interrupt-resume) | New checkpointer API |
| **B (deferred)** | Checkpoint branching | Complete undo/redo | Significant infrastructure |

Option A would give true **Memento** — save checkpoint state, fork to speculative branch, promote or discard the entire branch. This maps to database savepoints or git branches.

Option B **cannot give Command + Undo** in any useful sense — see constraint below.

### Fundamental Constraint: YAMLGraph Rollback Starts Over

**Correction from initial assessment:** LangGraph *does* support time travel natively — `get_state_history()` returns all past checkpoints and you can resume from any of them by passing an old `checkpoint_id` in the config. `update_state()` creates a branch (parallel timeline) from any prior checkpoint.

```python
# LangGraph native — fully works
history = list(app.get_state_history(config))
earlier = history[-2]                              # step before failure
result = app.invoke(None, earlier.config)          # resume from that point

# Or: branch with modified state (two coexisting timelines)
new_cfg = app.update_state(earlier.config, {"field": "corrected"})
result = app.invoke(None, new_cfg)
```

**What YAMLGraph does NOT expose declaratively:** This capability is only available via raw Python API on the compiled graph. There is no YAML syntax for:
- `resume_from_checkpoint: step_n`
- `rollback_to: before_node_X`
- `on_error: rewind` (distinct from `on_error: fallback`)

The `on_error: fallback` pattern in YAMLGraph invokes a **separate compensation graph** — which starts from its own `__start__` node. No automatic context inheritance; state from the failed graph must be explicitly passed via state mapping. This is Saga-style compensation (a forward-running undo workflow), not true checkpoint rewind.

```
LangGraph native time travel:
  [A] → [B] → [FAIL C]
                  ↑
       resume from [B]'s checkpoint_id → continue forward

YAMLGraph on_error: fallback (Saga):
  [A] → [B] → [FAIL C]
                  ↓
  [compensate_start] → [undo_C] → [undo_B]
  ↑ starts here — fresh graph invocation, not a rewind
```

**True compensation still requires:** stateless idempotent actions that record enough context at write-time for the compensator to reverse them — because the compensation graph starts fresh and has no access to intermediate state unless it was explicitly written to the shared state.

**Unexplored opportunity:** Expose LangGraph's `get_state_history()` + `checkpoint_id`-based resume as YAML-level primitives — enabling declarative rewind patterns without Python glue code.

### Beyond Voice: Universal Applications

The fire-early-validate-later pattern appears everywhere:

| Domain | Speculative Action | Invalidation Signal |
|---|---|---|
| **Voice bots** | Extract intent during VAD silence | Caller resumes speaking |
| **Chat UIs** | Pre-generate likely follow-up | User types different message |
| **Approval flows** | Pre-compute result | Approver modifies input |
| **Multi-step forms** | Pre-validate next step | User goes back |
| **Game AI** | Pre-compute NPC response | Player changes action |

### Relationship to Game Loop

The voice FSM already IS a game loop:

```
perceive (STT)  →  decide (LLM classify)  →  act (TTS speak)  →  update (state)
    ↑                                                                    │
    └────────────────── next turn ──────────────────────────────────────┘
```

Speculative execution is **predictive frame rendering** from game engines — start rendering the next frame before input is confirmed, discard if prediction was wrong.

---

## Key Insight

YAMLGraph's state-passing architecture naturally maps to **Blackboard** + **Chain of Responsibility**, while its compilation pipeline maps to **Builder** + **Factory**. The gap is in *runtime resilience patterns* (Circuit Breaker, Saga, Bulkhead) and *structural decoration* (wrapping nodes without modifying them).

The **Memento + Command** combination is the most immediately actionable pattern — FR-219 is already approved and maps directly to the ninchat_voice speculative execution problem.
