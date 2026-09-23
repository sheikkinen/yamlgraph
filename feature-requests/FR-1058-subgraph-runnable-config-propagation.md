# Feature Request: Restore RunnableConfig propagation and native `mode: direct` subgraphs

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-23
**First consumer / first event:** the next author who writes `type: subgraph`
in a graph YAML — today `mode: direct` crashes on the first invoke, and
`mode: invoke` silently aliases every parent thread's child to one checkpoint.
**Research:** in-body dispositioned alternatives table (§Alternatives
Considered); every row carries an executed probe, per FR-890's
equivalent-committed-record allowance.

## Summary

The FR-759 per-node OpenTelemetry wrapper is applied unconditionally to every
compiled node. Subgraph nodes are not ordinary node functions, and the wrapper
breaks them two ways: it calls a `CompiledStateGraph` as if it were a function
(`mode: direct` fails 100% of the time), and its one-parameter signature
suppresses LangGraph's `RunnableConfig` injection (`mode: invoke` / relay
children lose parent thread identity). Reported externally as issue #474 with
a tested patch attached.

## Value Statement

Subgraph composition — the framework's only unit of graph reuse — is currently
unusable in one mode and silently data-corrupting in the other.

## Problem

### Defect 1 — `mode: direct` never runs

`compile_subgraph_node()` passes the `CompiledStateGraph` returned by
`create_subgraph_node()` through `_maybe_wrap_otel()`, whose wrapper body is
`return node_fn(state)`.

Probe (executed 2026-09-23, main @ `432ce1b4`, langgraph 1.2.10):

```text
$ python -c "compile parent with a mode: direct child; invoke"
REPRO: TypeError 'CompiledStateGraph' object is not callable
```

The wrapper is unconditional by FR-759 design, so this fires with OTel
disabled. There is no configuration under which `mode: direct` works.

### Defect 2 — config injection is suppressed, children collide

LangGraph decides whether to inject `RunnableConfig` by inspecting the
registered callable's parameters. `subgraph_node` and `run_fn` both declare
`config: RunnableConfig | None = None` and are correct. `otel_wrapped(state)`
declares one parameter and sits in front of them.

Probe — the same function, bare and wrapped:

```text
PROBE A  bare: T-bare   wrapped: None
```

`config` arrives `None`, the `config = config or {}` guard converts it to `{}`,
and `_build_child_config` falls to its no-parent-thread branch, yielding
`thread_id = node_name` for every parent.

End-to-end probe, two parent threads through one relay-mode parent:

```text
invoke parent-a:
  child thread_id -> child
invoke parent-b:
  child thread_id -> child
UnboundLocalError: cannot access local variable 'resume_is_map' ...
During task with name 'child__run'
```

Worth recording precisely: the second thread does **not** fail cleanly. It
reaches a LangGraph internal that was never written to expect a foreign
checkpoint and dies on an unbound local — an error text that names nothing
about thread identity. Any user hitting this in production would file a
LangGraph bug, not a YAMLGraph one.

Both defects share one cause: a wrapper that mis-declares its own call
contract on behalf of the function it hides.

## Ideal Result

`type: subgraph` behaves as the LangGraph-native composition it claims to be:
direct children are registered as `CompiledStateGraph` objects so the engine
owns their checkpoint namespace and interrupt semantics, and separately
invoked children inherit a thread identity derived from their parent. Node
instrumentation observes nodes; it never alters how the engine may call them.

The minimal path back: make the wrapper signature-transparent, and stop
wrapping the one node kind that is not a function.

## Proposed Solution

Adopt three of the reporter's patch's four changes (§Findings against the
submitted patch).

1. `_maybe_wrap_otel()` declares `(state, config=None)` and dispatches through
   `call_func_with_variable_args()`, so config-aware nodes receive config and
   state-only nodes keep their existing contract — in both the enabled and
   disabled branches.
2. `compile_subgraph_node()` registers `mode: direct` values with
   `add_node()` directly, unwrapped.
3. `_build_child_config()` keeps user configurable keys but strips parent
   executor routing values (`__pregel_*`, `checkpoint_id`, `checkpoint_ns`,
   `checkpoint_map`). Propagating `__pregel_send` into a separately invoked
   child would bypass the FR-797 commit-before-pause relay.

The patch's fourth change — threading config through `_maybe_wrap_timeout()` —
is **not adopted** (F-1). `yamlgraph/node_timeout.py` is not touched by this FR.

Item 3 is not defensive coding against hypothetical keys. Probe — the
`configurable` dict LangGraph actually delivers to a node under a checkpointer:

```text
PROBE C  __pregel_call  __pregel_checkpointer  __pregel_read
         __pregel_replay_state  __pregel_runtime  __pregel_scratchpad
         __pregel_send  __pregel_task_id
         checkpoint_id  checkpoint_map  checkpoint_ns
         tenant  thread_id          (tenant/thread_id = the caller's own)
```

Every key the filter names is present on every invocation. Today this is inert
because config never arrives; the moment item 1 lands, all eight `__pregel_*`
handles begin flowing into separately invoked children. Item 3 is what keeps
item 1 from trading a silent-aliasing bug for a state-corruption one.

### Findings against the submitted patch

- **F-1 (cut): the timeout-wrapper change has no reachable caller.** The patch
  also rewrites `_maybe_wrap_timeout()` to forward config. Probed before
  accepting:

  ```text
  PROBE D  config-aware node fns in yamlgraph/:
      node_factory/subgraph_nodes.py:210  subgraph_node(state, config=None)
      node_factory/subgraph_nodes.py:251  run_fn(state, config=None)
  PROBE E  _maybe_wrap_timeout call sites (node_compiler.py):
      127 tool · 139 python · 168 agent · 194 tool_call · 258 llm
  PROBE F  grep -c _maybe_wrap_timeout yamlgraph/compile/subgraph_relay.py -> 0
  ```

  The only two config-aware node functions are the subgraph ones, and the
  subgraph compile path never applies the timeout wrapper. The two wrappers
  cannot compose on any path the compiler can produce. For the five node types
  that *are* timeout-wrapped, all state-only, `call_func_with_variable_args(fn,
  state, {})` is exactly `fn(state)` — so the change alters five live node
  types to buy no behavior on any of them.

  The patch's own evidence is the tell: its
  `test_timeout_and_otel_wrappers_preserve_runnable_config` hand-composes the
  two wrappers over a locally-defined `def node_fn(state, config)`. It is green
  against a shape the compiler cannot emit.

  Cutting this dissolves the patch's REQ mis-tag as a side effect: it tags that
  test `REQ-YG-069` (CAP-16 linter cross-reference) where the per-node timeout
  requirement is `REQ-YG-078` (CAP-96). That test is the tag's only occurrence
  in the patch, so deleting the change deletes the defect rather than
  correcting it. Recorded so the next reader does not re-derive the correction.

- **F-2 (resolved, no action): the thread-hop concern is moot.** I had flagged
  that `_maybe_wrap_timeout` runs its node inside a `ThreadPoolExecutor`, where
  contextvar-carried `RunnableConfig` is historically lossy. PROBE B showed the
  patch passes config explicitly rather than via contextvar, so the hop was
  safe anyway; with F-1 cut, no thread boundary is crossed by this FR at all.

### Accepted regression

`mode: direct` subgraph nodes lose their synthetic outer
`yamlgraph.node.execute` span; their child nodes still emit spans. FR-759
listed `subgraph` in its instrumented node set, so this narrows a shipped
claim. It is accepted because a function wrapper cannot represent a
`CompiledStateGraph` without breaking its semantics — which is precisely
Defect 1. `reference/otel-observability.md` must state the narrowed set.

## Acceptance Criteria

- [ ] A parent with a `mode: direct` child compiles and invokes without
      `TypeError`, under both `YAMLGRAPH_OTEL_ENABLED` settings.
- [ ] A direct child that interrupts is resumable through a `SqliteSaver`
      after the parent's connection is closed and reopened.
- [ ] `_maybe_wrap_otel` on a `(state, config)` function forwards a non-`None`
      config when invoked through a compiled LangGraph — asserted on the
      received payload, not on the wrapper's signature.
- [ ] Two parent threads through one `mode: invoke` parent produce distinct
      child thread ids (`parent-a:child`, `parent-b:child`) and resume
      independently.
- [ ] `_build_child_config` retains user keys and drops `__pregel_*`,
      `checkpoint_id`, `checkpoint_ns`, `checkpoint_map`.
- [ ] `yamlgraph/node_timeout.py` is unmodified by this FR (F-1).
- [ ] `reference/otel-observability.md` records the narrowed instrumented set.
- [ ] RED commit precedes GREEN; changelog fragment in `changelog/unreleased/`.

## Alternatives Considered

| # | Alternative | Probe executed | Disposition |
|---|---|---|---|
| 1 | Skip OTel wrapping for direct mode only; leave `otel_wrapped(state)` alone | Ran PROBE A after mentally applying it: `wrapped: None` is unchanged | **Rejected** — fixes Defect 1, leaves the silent cross-thread corruption, which is the worse of the two |
| 2 | Preserve the wrapped function's signature via `functools.wraps` instead of `call_func_with_variable_args` | Built it and invoked through a compiled graph: signatures report `(state)` and `(state, config=None)` correctly, but the run dies `TypeError: cfg_fn() got an unexpected keyword argument 'config'` | **Rejected** — see note below; the probe falsified the reason I first wrote down |
| 3 | Wrap the `CompiledStateGraph` in a `RunnableLambda` to keep the outer span | `isinstance(compiled, Pregel)` → `True`; `isinstance(RunnableLambda(compiled.invoke), Pregel)` → `False` | **Rejected** — LangGraph detects native subgraphs by `Pregel` instance, so this loses exactly the checkpoint-namespace inheritance `mode: direct` exists to provide |
| 4 | Do nothing; document `mode: direct` as unsupported | `git log` shows the mode shipped and is referenced in reference docs | **Rejected** — a shipped, documented mode that raises `TypeError` on every invoke is a defect, not a documentation gap |
| 5 | Adopt the reporter's patch verbatim, all four changes | PROBE D/E/F: the only config-aware node fns are the two subgraph ones; the subgraph compile path calls `_maybe_wrap_timeout` zero times | **Rejected** — change 4 has no reachable caller; it perturbs five live node types to serve a composition the compiler cannot emit |
| 6 | Adopt changes 1–3, drop change 4 | PROBE A, PROBE C, PROBE D/E/F, and the reproduction above | **Accepted** |

Note on alternative 2: my first written rejection claimed `inspect.signature`
would follow `__wrapped__` and over-report parameters for state-only nodes.
The probe says otherwise — signature reporting is correct in both directions.
The real failure is worse and only visible by running it: `functools.wraps`
makes the wrapper *advertise* a `config` parameter it does not accept, so
LangGraph passes `config=` and the call raises `TypeError`. The signature
becomes a promise the wrapper cannot keep. Recorded because the plausible
wrong reason would have survived review.

## Related

- Issue #474 (reporter: `sergesha`), including the tested patch
- #465 — introduced the unconditional OTel node wrapper
- FR-759 — per-node OTel spans; its instrumented-node claim narrows here
- FR-797 — the relay two-node split whose contract item 3 protects
- `yamlgraph/compile/node_otel.py`, `yamlgraph/compile/subgraph_relay.py`,
  `yamlgraph/node_factory/subgraph_nodes.py`
- REQ-YG-042 (CAP-11), REQ-YG-570 (CAP-212)
