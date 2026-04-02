# Fix: interrupt_output_mapping does not persist to parent state

## Problem

When a subgraph node (mode=invoke) has `interrupt_output_mapping` and the child
graph hits an interrupt, the mapped child state is never visible in the parent's
`get_state().values`. The parent sees `None` for all mapped keys (`response`,
`extracted`, `phase`, etc.) across every interrupt cycle.

Discovered via NV-190 integration test (ninchat_voice) which compiles a real
navigator → triage subgraph flow. The triage subgraph successfully extracts all
3 fields (confirmed by child-side logs), but the parent navigator graph never
sees the extracted data.

This also explains a live call bug where the greeting loops — the FSM reads
parent state to decide the next turn, but `response` and `phase` never update.

## Root Cause

`subgraph_nodes.py` line ~193: the `except GraphInterrupt:` handler uses
`__pregel_send` to push mapped state to the parent, then re-raises
`GraphInterrupt`. **LangGraph discards pending writes when GraphInterrupt
propagates** — the `__pregel_send` tuples are never committed to the
parent's checkpointer.

Proven by debug logging: `__pregel_send` fires with correct values
(e.g. `extracted = {'chief_complaint': 'Päänsärky', ...}`), but
`compiled.get_state(cfg).values` returns `None` for all mapped keys.

## Investigation Timeline

1. **NV-190 condemning test** — 4 passed, 2 failed. Failures: `extracted` is
   `{}` and `response` is stale (still the opening greeting) after multiple
   interrupt/resume cycles.

2. **Debug script** (`tmp/debug_subgraph_state.py`) — 3-turn walkthrough.
   Confirmed T0, T1, T2 all show `extracted: None`, `response` frozen at
   opening, `phase: None`.

3. **Value logging on `__pregel_send`** — Added INFO log after send. Output
   confirms correct values are sent:
   ```
   FR-006: run_triage mapped extracted = {'chief_complaint': 'Päänsärky', 'duration': 'kolme viikkoa', ...}
   FR-006: run_triage mapped phase = 'recap'
   ```
   But `get_state().values` still shows `None`. Proves `__pregel_send` writes
   are discarded on GraphInterrupt.

4. **interrupt() approach** — Replaced catch+re-raise with LangGraph's
   `interrupt()` function to pause parent. Problem: `interrupt(payload)` sends
   the payload as **interrupt value** (visible via `tasks[].interrupts[].value`),
   NOT as state updates. The node never returns, so no state commit.
   Confirmed: `state.tasks[0].interrupts[0].value` contains the mapped dict,
   but `state.values` stays `None`.

5. **Prepare/interrupt split** — Modeled after yamlgraph's own interrupt node
   pattern (FR-060). The subgraph node is split into two functions:
   - `prepare`: runs/resumes child, catches GraphInterrupt, returns mapped state
     (committed because node returns normally)
   - `interrupt`: checks if child is still paused, calls `interrupt()` to pause,
     returns resume value on replay

   This approach works for state persistence but requires:
   - Loop edge from interrupt → prepare (for multi-turn subgraphs)
   - Conditional routing: if child complete → forward, if paused → loop
   - Changes to node_compiler.py and edge_compiler.py
   - Existing `__interrupt__` in return value path (mock tests) coexists

   Prototype partially built in node_compiler and subgraph_nodes but reverted
   due to complexity — needs proper FR/plan/judge cycle.

## Prototype Lessons

During the prototype implementation, three non-obvious issues emerged:

1. **`_child_is_paused` needs ValueError guard** — `compiled.get_state()` raises
   `ValueError("No checkpointer set")` when the compiled graph has no
   checkpointer. The helper must catch this and return False.

2. **MagicMock `get_state().next` is truthy** — The 24 existing subgraph tests
   use MagicMock for the compiled graph. Calling `get_state()` on a MagicMock
   returns a MagicMock, and `.next` is also truthy. This caused `_child_is_paused`
   to return True in mock tests, entering the interrupt loop and calling
   `interrupt()` outside a runnable context. Any guard that checks child state
   must handle mock compiled graphs gracefully.

3. **`parent_checkpointer` is always None at node creation** — The
   `create_subgraph_node` function receives `parent_checkpointer` as a parameter,
   but `node_compiler.py` never passes it. The checkpointer is only set at
   `graph.compile(checkpointer=...)` time. So `parent_checkpointer` cannot be
   used to gate behavior at node creation time.

## Constraints

- Must not break existing subgraph tests (24 tests in test_subgraph.py) which
  use MagicMock compiled graphs with `__interrupt__` in return dict
- Must not break subgraphs without checkpointer (no-interrupt path)
- Must not break mode=direct subgraphs (LangGraph handles natively)
- Multi-turn child interrupts must work (triage has 3+ interrupt points)
- Parent state must reflect child progress at each interrupt boundary

## Alternative Approaches

### A) Fix the bug — prepare/interrupt node split

The approach prototyped in the Investigation Timeline (item 5). Split each
`mode=invoke` subgraph node into two parent-graph nodes at compile time:

1. **`{name}__prepare`** — runs/resumes child graph, catches `GraphInterrupt`,
   reads child state via checkpointer, returns mapped dict **normally** (so
   LangGraph commits the state update).
2. **`{name}__interrupt`** — checks if child is still paused (`get_state().next`
   truthy). If yes, calls `interrupt()` to pause parent. On resume, returns the
   resume value so the prepare node can forward it to the child.

Edges: `prepare → interrupt → prepare` (loop) with conditional exit when child
completes normally (no more `.next`).

**Pros:**
- Surgically fixes the root cause (`__pregel_send` discarded on re-raise).
- Preserves the subgraph YAML contract — no graph author changes.
- Works with all stream modes (node returns normally → committed to state).

**Cons:**
- Complexity: loop edges, conditional routing, mock graph guards.
- Prototype revealed 3 non-obvious issues (see above) that need careful handling.
- Every `mode=invoke` subgraph with interrupts gets 2 extra internal nodes and
  loop edges — visible in graph exports/visualizations.
- LangGraph internal assumption: `interrupt()` re-raises from within a node —
  need to verify this works cleanly with the prepare/interrupt split across
  different LangGraph versions.

**Effort:** 3-5 days (includes existing test migration, mock guards, edge
compiler changes).

### B) Graph rewrite behind the scenes — inline or passthrough expansion

Instead of fixing the subgraph interrupt mechanism, eliminate the subgraph
boundary entirely at compile time. Two sub-options:

#### B1: Inline expansion

At `compile_graph()` time, detect subgraph nodes with `interrupt_output_mapping`
and expand them into the parent graph. The child graph's nodes are prefixed with
the subgraph node name (e.g., `run_triage__extract_fields`) and wired into the
parent graph directly. State mapping becomes simple key aliasing.

This is essentially what FR-049 (`interactive_tool`) does for the
start/step/end pattern, but generalized to arbitrary subgraphs.

**Pros:**
- No `__pregel_send`, no state mapping — child nodes ARE parent nodes.
- Works with all stream modes by definition.
- No loop edges or extra internal nodes.

**Cons:**
- Massive complexity: must handle child tools, prompts, edges, conditions,
  loop limits — all namespaced and rewired into parent.
- State collisions: parent and child may use same key names (e.g., `messages`).
  Need rename/alias layer.
- Breaks subgraph encapsulation — the parent graph's visualization shows all
  child nodes.
- Tool resolution: child tools are relative to child graph's directory.
  Inlining must preserve path resolution.
- FR-049 already exists for the common case (interactive tools). Generalizing
  to arbitrary subgraphs is an order of magnitude harder.

#### B2: Passthrough bridge nodes

Add transparent passthrough nodes around the subgraph that commit state before
and after interrupts:

```
→ {name}__pre (passthrough: copy input_mapping) → {name} (subgraph) → {name}__post (passthrough: copy output_mapping) →
```

The pre/post nodes ensure state is committed at the parent level. On interrupt,
the passthrough captures the mapped state before the interrupt propagates.

**Problem:** This doesn't actually solve the issue. The subgraph node itself
still re-raises `GraphInterrupt`, which discards all pending writes including
the passthrough's. The passthrough runs BEFORE the subgraph, not after the
interrupt.

**Verdict:** B1 is theoretically correct but impractically complex for a
general solution. B2 doesn't work. B1 might work for specific known patterns
(like questionnaires) where the child graph structure is predictable — but
that's what FR-049 already is.

### C) Fix the requirement — concurrent intent graph

The ninchat_voice problem is specifically: navigator needs to route user intent
to a questionnaire subgraph and track progress. The subgraph interrupt mapping
exists because the navigator wants to see `extracted`, `response`, and `phase`
from the child.

**Alternative architecture:** Don't nest triage inside navigator. Instead:

1. **Navigator graph** — handles opening, intent classification, crisis
   detection. Produces `{intent: "medical_triage", user_message: "..."}` and
   completes.
2. **Triage graph** — runs independently (not as subgraph). The FSM coordinator
   starts it as a separate graph with its own thread, passing `user_message` and
   `skip_opening=true`.
3. **FSM coordinator** — already exists in the voice pipeline. It manages the
   conversation state machine. Instead of delegating to a single navigator graph
   that contains subgraphs, it orchestrates multiple graphs sequentially:
   - Start navigator → get intent
   - Start intent-specific graph (triage, interrai, etc.) → run to completion

The coordinator already tracks `phase`, `extracted`, `response` in its own
state. It reads these from `get_state()` after each interrupt/resume cycle.
The subgraph state mapping problem disappears because there IS no subgraph —
each graph runs at the top level with its own checkpointer.

**Pros:**
- Zero framework changes. No new node types, no compile-time rewrites.
- Each graph is simpler. Navigator is ~10 nodes (no subgraph nodes). Triage
  stays as-is.
- State visibility is trivial: `get_state()` on the active graph's thread.
- Scales to N questionnaires without nesting complexity.
- Works with all stream modes — no `interrupt_output_mapping` needed.
- Testable independently: navigator test and triage test don't depend on each
  other.

**Cons:**
- Requires FSM coordinator changes to manage graph hand-off (start navigator →
  read intent → start triage).
- Loses the "single graph invocation" abstraction — the conversation is now
  split across multiple graph runs.
- Thread management: each graph needs its own thread ID. Coordinator must track
  which graph is active.
- `skip_opening` and `user_message` pass-through must be explicit in coordinator
  logic, not YAML-declared.
- If there's ever a case where the navigator needs to resume after triage
  (e.g., "anything else?"), it needs its own checkpoint to return to — adds
  coordinator complexity.

**Effort:** 1-2 days for coordinator changes + graph simplification. The
triage graph is unchanged. Navigator drops 2 subgraph nodes and their mappings.

## Recommendation

**Option C is the pragmatic choice for ninchat_voice.** The FSM coordinator
already manages the conversation lifecycle — asking it to also manage graph
hand-off is a natural extension, not a new abstraction. This bypasses the
framework limitation entirely.

**Option A remains the correct framework-level fix** for the general case where
subgraph interrupts must map state to the parent. It should be tracked as a
separate yamlgraph FR for when other consumers need it (e.g., graphs without an
FSM coordinator).

**Option B1 is subsumed by FR-049** for the interactive tool pattern. A general
subgraph inlining mechanism is not justified by current evidence.

## Proposed Approaches

### A: Prepare/Interrupt Split (recommended)

Split subgraph nodes with `interrupt_output_mapping` into prepare + interrupt,
matching the existing FR-060 pattern for interrupt nodes.

- `create_subgraph_node` returns `(prepare_fn, interrupt_fn)` tuple when
  `interrupt_output_mapping` is set (single fn otherwise — no breakage)
- `node_compiler.py` detects tuple, registers both nodes, adds to
  `interrupt_nodes` set
- `edge_compiler.py` adds automatic loop edge: interrupt → prepare (conditional
  on child still paused)
- Prepare fn: checks `_child_is_paused()`, resumes via `Command(resume=...)` or
  starts fresh via `invoke(child_input, ...)`, catches `GraphInterrupt`, returns
  mapped state dict
- Interrupt fn: checks `_child_is_paused()`, calls `interrupt()` if yes,
  passes through if no

### B: Return-based with auto-interrupt node

Subgraph node always returns normally (never raises). Returns mapped state +
`_subgraph_paused: True` flag. Compiler auto-injects an interrupt node after
every subgraph with `interrupt_output_mapping`. Conditional edge loops back.

Simpler node factory, more compiler changes.

### C: mode=direct with state adapters

Convert navigator subgraphs to mode=direct. LangGraph handles interrupt
propagation natively. Requires shared state schema or adapter layer.

Smallest framework change but constrains consumer graph design.

## Files Affected

- `yamlgraph/node_factory/subgraph_nodes.py` — core fix
- `yamlgraph/node_compiler.py` — split registration
- `yamlgraph/edge_compiler.py` — loop edge for split nodes
- `tests/unit/test_subgraph.py` — new tests for interrupt mapping persistence
