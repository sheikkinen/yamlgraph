# Feature Request: Speculative Node Type (Stateless)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-04-14

## Summary

Add a `type: speculative` node that fires an LLM call early in the graph flow and tags
the result with a generation counter. A downstream `type: llm` node consumes the result
when still fresh (`_spec_gen` matches current `generation_key`) or falls back to a normal
LLM call when input changed between speculation and consumption.

## Value Statement

Graph authors who need to overlap LLM processing with a waiting period (VAD silence, human
approval, interrupt resume) can do so declaratively in YAML without writing concurrent Python
code that corrupts LangGraph checkpoints.

## Problem

NC-220 proved that application-layer speculative execution inevitably corrupts LangGraph
checkpoints: two `yamlgraph_async` tasks racing on the same `thread_id` produced 3× duplicate
LLM calls and a 4-bug cascade (NC-226, NC-227). Each fix addressed a downstream symptom rather
than the root cause (see diary `docs/diary/2026-04-13-reflection-nc-220-speculative-execution.md`).

The root cause is architectural: checkpoint write access is not exclusive when two async tasks
share a `thread_id`. The application layer cannot solve this because it does not own the
checkpointer. Only the framework can implement a safe pattern.

For **extraction-style nodes** (the NC-220 use case), full checkpoint forking is unnecessary.
The speculative call extracts fields from already-available partial input, stores the result in
state, and a downstream node validates freshness before accepting. No concurrent actors. No
checkpoint branching. Zero checkpointer changes. This is Option C from the diary.

## Proposed Solution

Two new YAML constructs compose into the speculative pattern:

### 1. `type: speculative` node — fire early, tag with generation

```yaml
nodes:
  spec_extract:
    type: speculative
    prompt: extract_intent
    variables:
      text: "{state.partial_utterance}"
    result_key: spec_extraction      # State key for the speculative result
    generation_key: speech_gen       # State key snapshotted at launch time
```

Execution semantics:
1. Read `state[generation_key]` → `launch_gen` (default `0` when absent)
2. Call `execute_prompt(prompt, variables)` (same as `type: llm`)
3. Write `{result_key: result, "_spec_gen_{result_key}": launch_gen}` to state
4. Respects existing `on_error` semantics (`skip`, `retry`, `fail`, `fallback`)

### 2. `accept_speculative` on `type: llm` — consume or fall back

```yaml
nodes:
  extract_intent:
    type: llm
    prompt: extract_intent
    variables:
      text: "{state.transcription}"
    state_key: extraction
    accept_speculative: spec_extraction   # Key written by the speculative node
    generation_key: speech_gen
```

Execution semantics:
1. Read `state[accept_speculative]` and `state["_spec_gen_spec_extraction"]`
2. Read current `state[generation_key]` → `current_gen`
3. If spec result is present **and** `_spec_gen == current_gen` → write spec result to
   `state_key`, skip LLM call
4. Otherwise → run LLM call normally, write to `state_key`

### Generation invalidation — bump to discard stale results

Any node (passthrough, llm, tool) can invalidate the speculative result by incrementing the
generation counter:

```yaml
nodes:
  new_speech_received:
    type: passthrough
    output:
      speech_gen: "{state.speech_gen + 1}"
```

### Full example (voice extraction overlap)

```yaml
defaults:
  provider: anthropic

nodes:
  # Fired during VAD silence — partial text available, confirmation pending
  spec_extract:
    type: speculative
    prompt: extract_intent
    variables:
      text: "{state.partial_utterance}"
    result_key: spec_extraction
    generation_key: speech_gen

  # VAD confirms; if no new speech arrived, spec result is used directly
  extract_intent:
    type: llm
    prompt: extract_intent
    variables:
      text: "{state.transcription}"
    state_key: extraction
    accept_speculative: spec_extraction
    generation_key: speech_gen
```

### State builder: `_spec_gen_*` key declaration

The state builder in `models/state_builder.py` collects fields by scanning `state_key` on each
node. The speculative node must also register its `result_key` **and** the derived
`_spec_gen_{result_key}` sentinel. The sentinel is declared as `Optional[int]` in the dynamic
TypedDict so that type checking and LangGraph state merging are both sound.

## Acceptance Criteria

- [ ] `NodeType.SPECULATIVE = "speculative"` added to `yamlgraph/constants.py`
- [ ] `NodeType.SPECULATIVE` added to `NodeType.requires_prompt()` in `constants.py` so the
      graph linter and `GraphConfig` validation enforce the `prompt` field on speculative nodes;
      a linter test covers the missing-prompt case
- [ ] `create_speculative_node()` factory created in `yamlgraph/node_factory/llm_nodes.py` (or
      a new `yamlgraph/node_factory/speculative_nodes.py` if `llm_nodes.py` would exceed 400
      lines after the addition)
- [ ] Speculative node writes `result_key` and `_spec_gen_{result_key}` to state on every
      execution
- [ ] Speculative node respects existing `on_error` semantics (`skip`, `retry`, `fail`,
      `fallback`)
- [ ] State builder in `models/state_builder.py` registers `result_key` as `Any` and
      `_spec_gen_{result_key}` as `Optional[int]` for every `type: speculative` node, making
      both fields first-class TypedDict members
- [ ] `accept_speculative` and `generation_key` parameters accepted by `create_node_function()`
      in `type: llm` nodes
- [ ] LLM node skips LLM call and promotes spec result to `state_key` when
      `_spec_gen_{accept_speculative}` matches current `state[generation_key]`
- [ ] LLM node runs normally when spec result is absent, `_spec_gen` mismatches, or
      `accept_speculative` is not configured
- [ ] `NodeType.SPECULATIVE` dispatched in `compile_node()` in `yamlgraph/node_compiler.py`
- [ ] Linter check `check_speculative_references` added to
      `yamlgraph/linter/checks_semantic.py`; emits a `LintIssue(severity="error", ...)` when
      `accept_speculative` names a key not produced by any `type: speculative` node in the same
      graph
- [ ] Unit tests tagged `@pytest.mark.req("REQ-YG-219")`:
  - Spec hit: `_spec_gen` matches `generation_key` → LLM skipped, spec result promoted to `state_key`
  - Spec miss: `_spec_gen` mismatches → LLM runs, result overwrites `state_key`
  - Spec absent: no speculative key in state → LLM runs normally
  - Spec node writes correct `_spec_gen_*` sentinel alongside `result_key`
  - Missing `prompt` on `type: speculative` → linter emits error
  - `accept_speculative` referencing unknown key → `check_speculative_references` emits error
- [ ] Integration test: full graph with `type: speculative` → `type: llm` with
      `accept_speculative` runs end-to-end with mocked LLM
- [ ] `REQ-YG-219` added to the requirement table in `ARCHITECTURE.md`
- [ ] Changelog fragment added to `changelog/unreleased/`
- [ ] Diary reflection added to `docs/diary/`

## Alternatives Considered

**Option A: Disposable namespace + replay** — fork to `{thread_id}:spec:{gen}`, on acceptance
replay the state delta onto the real checkpoint. Covers interrupt-resume speculation. Requires
extending the LangGraph checkpointer interface. Over-engineered for the NC-220 extraction
pattern. Deferred to a follow-up FR.

**Option B: Custom checkpointer with branching** — store/restore checkpoint snapshots, promote
branch atomically. Most general solution. Significant infrastructure investment. Not needed for
stateless extraction; revisit if Option C proves insufficient.

**Option C (this FR): Stateless speculation** — early LLM call + generation-tagged state key +
downstream validation. Zero checkpointer changes. Covers extraction-style nodes which represent
~80% of speculative use cases (diary estimate). No concurrent actors on the same `thread_id`.

**Why not `type: map`?** Map provides parallel fan-out over a list. Speculative execution is a
single-path early-compute pattern with conditional promotion; it has no list to fan out over.

**Why not `type: subgraph`?** Subgraph nodes create isolated `thread_id` namespaces but still
participate sequentially in the parent checkpoint cycle. They do not provide early-fire-late-
validate semantics.

**Why not `skip_if_exists` alone?** `skip_if_exists` prevents re-execution when a state key
already has a truthy value, but it provides no generation-based invalidation. A speculative
result from a prior turn would never be discarded regardless of changed input.

## Related

- NC-226 FR: checkpoint corruption from concurrent `thread_id` access
- NC-227 FR: 4-bug cascade and rollback of NC-220 speculative execution
- Diary: `docs/diary/2026-04-13-reflection-nc-220-speculative-execution.md`
- FR-170: `yamlgraph_async` action type (concurrent actor root cause)
- FR-210: subgraph-interrupt-state-commit (related checkpoint isolation work)
- `yamlgraph/node_factory/llm_nodes.py`: `create_node_function()`, `_should_skip_if_exists()`
- `yamlgraph/node_factory/subgraph_nodes.py`: `_build_child_config()` (thread_id namespace pattern)
- `yamlgraph/models/state_builder.py`: TypedDict generation (needs `result_key` + sentinel registration)
- `yamlgraph/linter/checks_semantic.py`: `LintIssue` pattern for `check_speculative_references`
