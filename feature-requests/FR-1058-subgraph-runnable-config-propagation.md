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

Adopt the reporter's patch with two corrections (§Findings against the
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
4. `_maybe_wrap_timeout()` threads the same config through, so composing the
   two wrappers cannot re-hide it.

### Findings against the submitted patch

- **F-1 (must fix): wrong REQ tag.** The patch tags its timeout test
  `REQ-YG-069`. That ID exists but belongs to CAP-16 linter-cross-reference.
  The per-node timeout requirement is **REQ-YG-078** (CAP-96, FR-069) — the FR
  number was transcribed as a REQ number. `req_coverage.py --strict` cannot
  catch this: the tag is well-formed and resolvable, just attached to an
  unrelated capability.
- **F-2 (resolved, no action): the thread-hop concern.** `_maybe_wrap_timeout`
  runs the node inside a `ThreadPoolExecutor`, and contextvar-carried
  `RunnableConfig` is historically lossy across threads. Probed rather than
  assumed:

  ```text
  PROBE B  across thread: T-thread
  ```

  The patch passes config as an explicit argument, not via contextvar, so the
  hop is safe. Recorded here so the next reader does not re-litigate it.

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
- [ ] Config survives `_maybe_wrap_timeout` composed with `_maybe_wrap_otel`.
- [ ] Timeout-related tests tag **REQ-YG-078**, not REQ-YG-069 (F-1).
- [ ] `reference/otel-observability.md` records the narrowed instrumented set.
- [ ] RED commit precedes GREEN; changelog fragment in `changelog/unreleased/`.

## Alternatives Considered

| # | Alternative | Probe executed | Disposition |
|---|---|---|---|
| 1 | Skip OTel wrapping for direct mode only; leave `otel_wrapped(state)` alone | Ran PROBE A after mentally applying it: `wrapped: None` is unchanged | **Rejected** — fixes Defect 1, leaves the silent cross-thread corruption, which is the worse of the two |
| 2 | Preserve the wrapped function's signature via `functools.wraps` instead of `call_func_with_variable_args` | Built it and invoked through a compiled graph: signatures report `(state)` and `(state, config=None)` correctly, but the run dies `TypeError: cfg_fn() got an unexpected keyword argument 'config'` | **Rejected** — see note below; the probe falsified the reason I first wrote down |
| 3 | Wrap the `CompiledStateGraph` in a `RunnableLambda` to keep the outer span | `isinstance(compiled, Pregel)` → `True`; `isinstance(RunnableLambda(compiled.invoke), Pregel)` → `False` | **Rejected** — LangGraph detects native subgraphs by `Pregel` instance, so this loses exactly the checkpoint-namespace inheritance `mode: direct` exists to provide |
| 4 | Do nothing; document `mode: direct` as unsupported | `git log` shows the mode shipped and is referenced in reference docs | **Rejected** — a shipped, documented mode that raises `TypeError` on every invoke is a defect, not a documentation gap |
| 5 | Adopt the reporter's patch with F-1 corrected | PROBE A, PROBE B, and the reproduction above | **Accepted** |

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
  `yamlgraph/node_factory/subgraph_nodes.py`, `yamlgraph/node_timeout.py`
- REQ-YG-042 (CAP-11), REQ-YG-570 (CAP-212), REQ-YG-078 (CAP-96)
