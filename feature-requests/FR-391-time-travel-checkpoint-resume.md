# Feature Request: Time Travel — Declarative Checkpoint Rewind and Branch

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved (pending scope corrections)
**Effort:** 4 days
**Requested:** 2026-05-15

## Summary

Expose LangGraph's native time-travel capabilities (`get_state_history`, `checkpoint_id`-based
resume, `update_state` branching) as declarative YAML constructs and CLI commands, so graph
authors can rewind, branch, and inspect past execution states without writing Python glue code.

## Value Statement

Graph authors and operators get point-in-time rewind and parallel-timeline branching for any
checkpointed graph — enabling undo, speculative retries, and post-mortem replay — without
touching Python.

## Problem

LangGraph fully supports time travel:

```python
# All native LangGraph — works today
history = list(app.get_state_history(config))
earlier = history[-2]

# Resume from a prior checkpoint (genuine rewind)
result = app.invoke(None, earlier.config)

# Branch: modify state at a prior point, create parallel timeline
new_cfg = app.update_state(earlier.config, {"field": "corrected"})
result = app.invoke(None, new_cfg)
```

YAMLGraph provides no declarative access to these primitives. The only rollback mechanism is
`on_error: fallback`, which invokes a **separate compensation graph from its own start node** —
Saga-style, not a rewind. Any state from intermediate steps must be explicitly forwarded.

This means:
- Debugging a failed production run requires writing Python to inspect history
- Retrying from a mid-graph checkpoint requires Python boilerplate
- Creating an A/B test from a fork point requires Python
- "What would have happened if step N had different input?" requires Python

## Proposed Solution

### 1. CLI: `yamlgraph graph history` — inspect checkpoint timeline

```bash
# List all checkpoints for a thread
yamlgraph graph history graph.yaml --thread session-123

# Output:
# step  checkpoint_id                          next_node       timestamp
# 3     1f1500e7-2b2a-65a2-8000-abc123def456  (complete)      2026-05-15 06:30:01
# 2     1f1500e6-1a1b-54b1-7fff-...           summarize       2026-05-15 06:29:58
# 1     1f1500e5-0909-...                      analyze         2026-05-15 06:29:55
# 0     1f1500e4-...                           generate        2026-05-15 06:29:52
```

### 2. CLI: `yamlgraph graph run --resume-from` — rewind to prior step

```bash
# Resume from step 1 (re-run from 'analyze' forward with original state)
yamlgraph graph run graph.yaml \
  --thread session-123 \
  --resume-from step=1

# Or by checkpoint_id directly
yamlgraph graph run graph.yaml \
  --thread session-123 \
  --resume-from checkpoint=1f1500e5-0909-...
```

### 3. CLI: `yamlgraph graph run --branch-from` — fork with state override

```bash
# Fork from step 1 with a modified state value
yamlgraph graph run graph.yaml \
  --thread session-123 \
  --branch-from step=1 \
  --set topic="alternative input"
# Creates new thread: session-123:branch-1 (or --branch-thread to name it)
```

### 4. YAML: `on_error: rewind` — automatic rewind to prior checkpoint

```yaml
nodes:
  risky_llm_call:
    type: llm
    prompt: risky_operation
    state_key: result
    on_error: rewind          # rewind to the checkpoint before this node
    rewind_max: 2             # max rewind attempts before escalating to fallback
```

Execution semantics:
1. Node fails → look up `get_state_history()` for the checkpoint immediately preceding this node
2. Resume from that checkpoint — effectively re-running this node with the same input
3. After `rewind_max` attempts, fall through to `fallback` graph if configured

This is distinct from `on_error: retry` (re-runs same node in-place, no checkpoint step back).

### 5. Python API: `get_checkpoint_history()` helper

```python
from yamlgraph.storage.checkpointer import get_checkpoint_history

history = get_checkpoint_history(app, thread_id="session-123")
# Returns list of CheckpointEntry(step, checkpoint_id, timestamp, next_nodes, state_summary)
```

## Acceptance Criteria

- [ ] `REQ-YG-391` added to `ARCHITECTURE.md`
- [ ] `yamlgraph graph history <graph> --thread <id>` command prints checkpoint timeline in tabular format
- [ ] `yamlgraph graph run --resume-from step=N` resumes execution from step N of the given thread
- [ ] `yamlgraph graph run --resume-from checkpoint=<uuid>` resumes from exact checkpoint UUID
- [ ] `yamlgraph graph run --branch-from step=N --set key=value` forks a new thread from step N with state override
- [ ] `on_error: rewind` node attribute implemented; node re-runs from preceding checkpoint on failure
- [ ] `on_error: rewind` respects `rewind_max:` (default 1); escalates to `fallback` after exhaustion
- [ ] `get_checkpoint_history(app, thread_id)` helper exported from `yamlgraph.storage.checkpointer`
- [ ] All features require a non-memory checkpointer; memory checkpointer emits a clear error
- [ ] Unit tests tagged `@pytest.mark.req("REQ-YG-391")`:
  - `get_checkpoint_history` returns steps in reverse order with correct metadata
  - `--resume-from step=N` invokes graph with old checkpoint config
  - `--branch-from` creates a new thread with modified state
  - `on_error: rewind` re-runs node from prior checkpoint
  - `on_error: rewind` with `rewind_max: 1` escalates to fallback on second failure
  - Memory checkpointer raises `ConfigurationError` when rewind is requested
- [ ] Integration test: SQLite checkpointer, 3-node graph, `--resume-from step=1` re-runs steps 1–3
- [ ] `reference/checkpointers.md` updated with time-travel section
- [ ] `reference/cli.md` updated with `history`, `--resume-from`, `--branch-from` flags
- [ ] Changelog fragment added to `changelog/unreleased/`
- [ ] Diary reflection added to `docs/diary/`

## Judgement

**Status: APPROVED with scope reduction**

### Strengths

1. **Grounded in existing primitives.** `get_state_history()` already exists in
   `yamlgraph/storage/checkpointer.py`. The FR wraps native LangGraph capabilities — no new state
   machinery.
2. **Clear value.** Debugging and retrying from mid-graph checkpoints currently requires Python
   boilerplate. CLI access to `history` and `--resume-from` directly serves the YAML-first mission.
3. **Clean separation.** CLI commands (§1–3) are thin wrappers. `on_error: rewind` (§4) extends the
   existing `ErrorHandler` enum and `llm_execution.py` handler flow.

### Issues to Address Before Enforce

| # | Issue | Resolution |
|---|-------|------------|
| 1 | **`on_error: rewind` semantic ambiguity.** "Re-running with same input" is identical to `retry`. True rewind must invoke `graph.invoke(None, prior_config)` — resuming from the prior checkpoint forward, not re-executing the single node in-place. | AC clarified: rewind calls `graph.invoke(None, prior_checkpoint_config)`. This is the semantic distinction from `retry`. |
| 2 | **`rewind_max` vs `max_retries` precedence.** Both are retry-like counters on the same node. | `on_error: rewind` ignores `max_retries`; `rewind_max` is the sole counter. Document explicitly. |
| 3 | **`--branch-from` thread auto-naming is fragile.** `session-123:branch-1` collides on repeat runs. `--branch-thread` is mentioned but not in AC. | `--branch-thread` flag is **required** when `--branch-from` is used; no auto-naming. Add to AC. |
| 4 | **Memory checkpointer guard is over-broad.** `MemorySaver` supports `get_state_history` in-process; the guard only applies cross-process CLI invocations. `on_error: rewind` works with any checkpointer including memory. | Split guard: CLI `--resume-from`/`--branch-from` require persistent checkpointer. `on_error: rewind` works with all backends. |
| 5 | **`get_checkpoint_history()` helper (§5) is redundant.** `get_state_history()` already exists in `checkpointer.py`. `CheckpointEntry` wrapper adds a mapping layer without benefit over raw `StateSnapshot`. | Drop §5 from scope. CLI commands format `StateSnapshot` directly. |

### Scope Freeze

**In scope (enforce):**
- `yamlgraph graph history` CLI command — tabular checkpoint timeline
- `--resume-from step=N|checkpoint=<uuid>` on `graph run`
- `--branch-from step=N --set key=val --branch-thread <name>` on `graph run`
- `on_error: rewind` + `rewind_max` in `ErrorHandler` enum and `llm_execution.py`
- Tests, changelog, diary

**Out of scope (deferred):**
- `get_checkpoint_history()` Python helper — redundant with `get_state_history()`
- Auto-naming for branch threads — require explicit `--branch-thread`

### Boundary with ninchat_voice / FR-219

Cross-check against the ninchat_voice voice pipeline confirms that **FR-391 does not address and
must not claim to address** the "analyze immediately, discard if caller continues speaking" pattern.

That pattern is **fire-and-forget with generation-gated acceptance**, already implemented in
ninchat_voice via:
- `task_generation` counter in FSM context
- `accumulate_text` action bumps generation on orphaned `_graph_running_*` guard detection
- `yamlgraph_async` discards result silently when `current_gen != launch_generation` at completion
- FSM transitions `graph_processing → graph_listening` on `transcribed`/`recognizing`

This is **external-invalidation-driven discard of a concurrent in-flight result** — the opposite
direction from FR-391's **internal-failure-driven rewind of a completed sequential step**:

| Dimension | FR-391 (rewind) | Voice pattern (discard) |
|-----------|-----------------|-------------------------|
| Trigger | Node failure / CLI flag | External FSM event during execution |
| Direction | Backward (undo to prior checkpoint) | Forward (ignore arriving stale result) |
| Actor model | Sequential | Concurrent (FSM + async task) |
| Checkpoint touch | Yes — resume from prior checkpoint_id | No — checkpoint never involved |
| Correct FR | This FR | FR-219 (`type: speculative`) |

`--branch-from` is useful for **post-mortem replay** ("what if input had been different?") but is
a debugging tool, not a runtime discard mechanism. Do not conflate.

### Appendix: How ninchat_voice navigator actually implements the discard

Tracing `projects/ninchat_voice/actions/real/yamlgraph_async_action.py` and
`config/voice_coordinator_navigator.yaml`:

```
graph_listening (accumulate_text + silence_detector, repeatable)
  │
  [speech_complete]
  ▼
ack_speaking  ← TRANSIENT (NC-229)
  1. voice_speak "Kiitos. Kirjaan tietoja."  → emits ack_speak_done (unconsumed)
  2. set_context _ack_fired=true             → emits ack_done IMMEDIATELY
  │
  [ack_done]
  ▼
graph_processing
  YamlgraphAsyncAction.execute():
    1. Captures launch_generation = context["task_generation"] (e.g. 3)
    2. Snapshots accumulated_utterance into frozen SnapshotParams.initial_state
    3. Clears accumulated_utterance in context (fresh for next utterance)
    4. Sets _graph_running_graph_processing = True (guard)
    5. asyncio.create_task(_run_and_dispatch(...))
    6. Returns None  ← FSM is FREE immediately, ack TTS plays concurrently

  If caller speaks again → transcribed/recognizing event arrives:
    graph_processing ──[transcribed]──► graph_listening

graph_listening — accumulate_text detects orphaned _graph_running_graph_processing:
    - context["task_generation"] bumped 3 → 4
    - guard key cleared

... LLM finishes in background ...

_run_and_dispatch() completion:
    current_gen = context["task_generation"]  # now 4
    if current_gen != launch_generation:       # 4 != 3 → True
        logger.warning("🗑️ discarding stale result")
        return  # FsmEventSender.send_event() never called
```

**Key facts:**
- The LangGraph checkpoint **advances normally** even when the FSM discards the result. Next turn
  detects `state.next` (interrupt) and resumes with `Command(resume=new_input)`.
- The discard happens at `send_event` callsite — no graph rollback, no state mutation.
- `SnapshotParams` is a frozen dataclass — the background task cannot observe live context changes.
- `task_generation` is in FSM context (shared), not in the task (isolated) — one-way invalidation
  signal: FSM writes, task reads once on completion.
- This is **not a rewind**. Both graph and FSM move forward. The discard is purely suppression of
  the outbound DGRAM event.

### Effort Revised

4 days (was 3). Five touch points: CLI, constants, node_factory, storage, docs.

### Files to Touch

| File | Change |
|------|--------|
| `yamlgraph/constants.py` | Add `REWIND = "rewind"` to `ErrorHandler` |
| `yamlgraph/models/graph_schema.py` | Add `rewind_max: int` field to `NodeConfig` |
| `yamlgraph/node_factory/llm_execution.py` | Add rewind error handler branch |
| `yamlgraph/cli/graph_commands.py` | Add `history` subcommand; `--resume-from`, `--branch-from`, `--branch-thread`, `--set` flags |
| `reference/checkpointers.md` | Time-travel section |
| `reference/cli.md` | New flags documentation |

---

## Alternatives Considered

**Expose raw `checkpoint_id` as an env/config var only** — `--checkpoint-id` flag on existing `run`
command. Simpler but requires users to discover IDs externally; no `history` command. Insufficient
for operator workflows.

**`on_error: rewind` only, no CLI** — Most immediately useful but leaves debugging and branching
workflows as Python-only. The full surface is cohesive and the CLI additions are thin wrappers
over the same primitives.

**Saga compensation only (`on_error: fallback`)** — Already implemented. Compensation is a
separate forward-running workflow; rewind is a true time reversal. They are complementary, not
alternatives. Rewind is cheaper when the node can simply be retried with the same inputs.

## Relationship to Other FRs

- **FR-219** (`type: speculative`) — Addresses *future* speculation (fire-early-validate-later).
  This FR addresses *past* rewind (resume from a prior known-good state). Complementary.
  **Important boundary:** The ninchat_voice "analyze immediately, discard if caller continues
  speaking" pattern belongs to FR-219, not here. That pattern is concurrent fire-and-forget with
  generation-gated acceptance — it does not touch checkpoints. FR-391 is sequential and
  failure-driven; FR-219 is concurrent and invalidation-driven.
- **FR-210** (subgraph-interrupt-state-commit) — Subgraph thread namespace pattern used here
  for `--branch-from` thread ID derivation.
- **NC-226** (checkpoint corruption) — Root cause was concurrent writes to same `thread_id`.
  Time travel operates sequentially; no concurrent actor concern.

## Related

- `yamlgraph/storage/checkpointer_factory.py` — checkpointer backends
- `yamlgraph/storage/checkpointer.py` — `get_state_history` wrapper
- `reference/checkpointers.md` — existing checkpointer docs
- `docs/brainstorming-design-pattern-integration.md` — Memento/Command pattern analysis
- LangGraph docs: `graph.get_state_history()`, `graph.update_state()`, `checkpoint_id` config key
