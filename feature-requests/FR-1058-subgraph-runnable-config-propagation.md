# Feature Request: Restore RunnableConfig propagation and native `mode: direct` subgraphs

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS; R-1..R-5 folded; authority active
**Effort:** 1 day
**Requested:** 2026-09-23
**First consumer / first event:** the next author who writes `type: subgraph`
in a graph YAML — today `mode: direct` crashes on the first invoke, and
`mode: invoke` silently aliases every parent thread's child to one checkpoint.
**Research:** in-body dispositioned alternatives table (§Alternatives
Considered) — a mixture of executed probes (rows 2, 3, 5) and deductions from
probes cited elsewhere in this FR (rows 1, 4); each row states which it is, per
FR-890's equivalent-committed-record allowance.
**`is_this_a_graph`:** No — this is a deterministic compiler/runtime bug fix.
There is no per-item LLM work, no multi-stage LLM pipeline, and no agent
fan-out. No existing graph in `yamlgraph graph list` applies.

## Prior art

| FR | Status | Disposition |
|---|---|---|
| FR-759 | Judged, authority active | Introduced the unconditional per-node OTel wrapper and claimed `subgraph` among its instrumented node types. This FR **narrows** that claim for `mode: direct` only (§Accepted regression) and preserves its disabled-path no-op contract. |
| FR-797 | Enforced 2026-08-15 | Owns the invoke-mode commit-before-pause relay. This FR **preserves** it: item 3 exists precisely so that restoring config does not hand `__pregel_send` to a separately invoked child and bypass the relay. Relay topology is untouched. |
| FR-210 | Judged — monolithic scope **rejected**, decomposition required | Not reopened. FR-210 died for bundling relay topology with edge and state compilation. This FR changes neither: no edge rewriting, no state-field synthesis, no interrupt-flow change. It is a wrapper-contract repair confined to three call sites. |

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
   `checkpoint_map`), **without mutating the parent config**. Propagating
   `__pregel_send` into a separately invoked child would bypass the FR-797
   commit-before-pause relay.

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
Defect 1. The narrowing must be recorded in **all three** canonical surfaces,
not only the reference doc (R-2): `reference/otel-observability.md`,
`capabilities/CAP-212-otel-observability-boundary.yaml`, and the REQ-YG-570
text in `ARCHITECTURE.md`. Each must distinguish invoke/relay subgraph
functions (outer span retained) from native direct subgraphs (child-node spans
only).

## Acceptance Criteria

- [ ] AC-01: R-1..R-5 folded before enforcement (this revision).
- [ ] AC-02: A parent with a `mode: direct` child compiles and invokes without
      `TypeError`, with `YAMLGRAPH_OTEL_EXPORT` unset **and** with
      `YAMLGRAPH_OTEL_EXPORT=otlp`; registration preserves the native compiled
      graph rather than wrapping it in a callable adapter.
- [ ] AC-03: With OTel enabled, a direct subgraph emits no synthetic outer
      subgraph-node span while its executed child nodes remain instrumented.
- [ ] AC-04: A direct child that interrupts is resumable through a
      `SqliteSaver` after the parent's connection is closed and reopened. An
      in-memory saver is not an equivalent witness for this persistence claim.
- [ ] AC-05: All four wrapper cases, exercised through a compiled LangGraph
      and asserted on the **received payload**, never on `inspect.signature`:
      (a) config-aware node, OTel off → non-`None` config;
      (b) config-aware node, OTel on → same config, span emitted;
      (c) state-only node, OTel off → called with state only, no `config=`;
      (d) state-only node, OTel on → state only, span emitted.
      Case (c)/(d) protect FR-759's disabled no-op contract against a `config=`
      leak into state-only callables.
- [ ] AC-06: Two parent threads through one `mode: invoke` parent produce
      `parent-a:child` and `parent-b:child` and resume independently without
      reading or corrupting the other's checkpoint.
- [ ] AC-07: One table-driven `_build_child_config` witness proves all of:
      outer keys (`tags`, `metadata`, callbacks) retained; ordinary user
      `configurable` keys retained; thread id derived as
      `{parent_thread}:{node_name}`; every `__pregel_*` key plus
      `checkpoint_id`/`checkpoint_ns`/`checkpoint_map` absent from the child;
      and **the parent config is not mutated**.
- [ ] AC-08: `reference/otel-observability.md`, CAP-212, and the REQ-YG-570
      text in `ARCHITECTURE.md` all distinguish invoke/relay outer spans from
      direct-subgraph child-node-only instrumentation.
- [ ] AC-09: `yamlgraph/node_timeout.py` and `_maybe_wrap_timeout()` are
      unchanged; no hand-composed timeout-plus-OTel test is introduced (F-1).
- [ ] AC-10: Every new test carries `REQ-YG-042` (subgraph behaviour/config)
      and/or `REQ-YG-570` (wrapper/observability); a cross-boundary end-to-end
      witness may carry both. `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: RED commit precedes GREEN; `changelog/unreleased/` carries a
      `type: fix` fragment naming FR-1058 and the governing requirements.

## Alternatives Considered

| # | Alternative | Probe executed | Disposition |
|---|---|---|---|
| 1 | Skip OTel wrapping for direct mode only; leave `otel_wrapped(state)` alone | *Deduction from PROBE A* (not separately executed): the wrapper signature is unchanged, so `wrapped: None` still holds | **Rejected** — fixes Defect 1, leaves the silent cross-thread corruption, which is the worse of the two |
| 2 | Preserve the wrapped function's signature via `functools.wraps` instead of `call_func_with_variable_args` | Built it and invoked through a compiled graph: signatures report `(state)` and `(state, config=None)` correctly, but the run dies `TypeError: cfg_fn() got an unexpected keyword argument 'config'` | **Rejected** — see note below; the probe falsified the reason I first wrote down |
| 3 | Wrap the `CompiledStateGraph` in a `RunnableLambda` to keep the outer span | `isinstance(compiled, Pregel)` → `True`; `isinstance(RunnableLambda(compiled.invoke), Pregel)` → `False` | **Rejected** — LangGraph detects native subgraphs by `Pregel` instance, so this loses exactly the checkpoint-namespace inheritance `mode: direct` exists to provide |
| 4 | Do nothing; document `mode: direct` as unsupported | *Probed post-judgement and **falsified my own row**:* the mode is shipped and schema-valid but documented **nowhere** — see §Documentation and example gap | **Rejected** — and for a stronger reason than first written: the reference doc actively names a *different*, non-existent mode in its place |
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

## Documentation and example gap (found post-judgement, 2026-09-23)

Surveying committed artifacts for witnesses to this mechanism turned up the
reason the defect survived from #465 to now: **nothing exercises or describes
`mode: direct`.**

### G-1 — zero examples

Seven committed YAML files declare `type: subgraph`. Every one that names a
mode names `mode: invoke`; the rest default to it. `mode: direct` appears in no
committed graph, no demo, and no snippet.

```text
PROBE G  git ls-files '*.yaml' | xargs grep -l "type: subgraph"
  examples/demos/interrupt/interrupt-parent-redis.yaml
  examples/demos/interrupt/interrupt-parent-with-checkpointer-child.yaml
  examples/demos/interrupt/interrupt-parent.yaml
  examples/demos/subgraph/graph.yaml                  -> mode: invoke
  examples/image_pipeline/graph.yaml                  -> mode: invoke
  examples/plot_modeller/graphs/perspective_l5.yaml   -> mode: invoke
  examples/yamlgraph_gen/snippets/nodes/subgraph-basic.yaml
  (occurrences of `mode: direct`: 0)
```

A mode that no example invokes is a mode no CI run invokes. `mode: direct` has
been raising `TypeError` on every possible use since #465, and the suite stayed
green because nothing ever called it.

### G-2 — the reference doc documents a mode that does not exist

`reference/graph-yaml.md:879` describes the subgraph `mode` field as:

> `invoke` (default) or `stream`

The schema is `Literal["invoke", "direct"]`
(`yamlgraph/models/node_schema.py:28`). Probed against the model rather than
read off the docs:

```text
PROBE H  SubgraphNodeConfig(type=subgraph, graph=c.yaml, mode=...)
    mode=invoke   -> OK
    mode=direct   -> OK
    mode=stream   -> REJECTED (ValidationError)
```

The doc is wrong in both directions at once: it advertises `stream`, which
fails validation, and omits `direct`, which is the only other accepted value.
A user following the reference cannot reach `mode: direct` at all, and a user
who guesses it correctly hits the `TypeError`.

This also **corrects this FR's own alternative 4**, which asserted the mode is
"referenced in reference docs". It is not. I had labelled that cell a deduction
from the cited record; the cell was wrong, and only the probe caught it.

### G-3 — no witness for the parent-thread identity contract

`tests/unit/test_subgraph.py::TestThreadIdPropagation` exercises
`_build_child_config` as a unit, but no committed test or example drives two
parent threads through one compiled parent. That is the defect-2 seam, and it
is precisely the shape a unit test cannot condemn: the helper is correct in
isolation and never receives real input.

### Proposed samples — REQUIRES SEPARATE AUTHORITY

Condition **C-6** of the judgement forbids creating or modifying graph/prompt
artifacts under this FR's authority, and D-5 freezes the doc surface to the
three OTel span-narrowing files. The `mode` field documentation at
`reference/graph-yaml.md:879` is **not** in that set. So the following are
recorded as a proposal, not adopted here:

| # | Proposal | Rationale |
|---|---|---|
| S-1 | Correct `reference/graph-yaml.md:879` to `invoke` (default) or `direct`, and state what each means: `invoke` calls the child separately and maps state; `direct` registers it natively so the engine owns its checkpoint namespace | The doc is factually false today, independent of this FR's code fix |
| S-2 | `examples/demos/subgraph-direct/` — a parent with a `mode: direct` child, modelled on `examples/demos/subgraph/`, wired into `demo.sh` as `demo_subgraph_direct` | Gives `mode: direct` its first executable witness; a demo that crashes is a defect nobody can miss |
| S-3 | Extend `examples/demos/interrupt/` with a direct-mode parent whose child interrupts, resumed through a checkpointer | Demonstrates the actual reason to prefer `direct` over `invoke` — native interrupt and checkpoint-namespace inheritance — which no current artifact shows |
| S-4 | Keep the two-thread invoke-mode witness (test, not example) as a permanent regression test: one compiled parent, `parent-a`/`parent-b`, distinct child identities | Closes G-3. AC-06 covers it for this FR; S-4 proposes it outlive the fix |

S-1 is the cheapest and highest-value: the doc defect is live on `main` now and
misroutes every reader of the subgraph section. S-2 is what would have caught
this bug at authoring time.

Any S-2/S-3 artifact must be authored through `scripts/author.sh` per the
graph-authoring doctrine, not hand-written.

**Recommendation:** S-1 and S-2 as a small follow-up FR. Folding them into
FR-1058 would require re-judgement, since both cross frozen scope (C-6, D-5).

## Judgement (2026-09-23)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1058-subgraph-runnable-config-propagation.judgement.md](FR-1058-subgraph-runnable-config-propagation.judgement.md).
Classified a **framework primitive**. Authority activates only with R-1..R-5
folded, which they now are.

| # | Finding | Resolution (folded) |
|---|---|---|
| R-1 | Header claimed "every row carries an executed probe"; alternative 1 was a *mental* application, and prior art was listed, not dispositioned. | Header now states honestly which rows are executed probes (2, 3, 5) and which are deductions (1, 4). Added `is_this_a_graph` (No) and a §Prior art table dispositioning FR-759, FR-797, and rejected FR-210. |
| R-2 | AC named `YAMLGRAPH_OTEL_ENABLED` — a switch that **does not exist**. Verified: `otel.py:60` reads `YAMLGRAPH_OTEL_EXPORT`, enabled value `otlp`; the invented name appears nowhere in the repo. | AC-02 now names the two real states. The span narrowing also propagates to all three canonical surfaces (reference doc, CAP-212, REQ-YG-570 in ARCHITECTURE.md), not just the first. |
| R-3 | One config-forwarding AC could not condemn a `config=` leak into state-only callables — the regression that would break FR-759's no-op contract. | AC-05 expanded to a four-case matrix (config-aware × state-only) × (OTel on/off), asserted on received payload through a compiled graph. |
| R-4 | `_build_child_config` ACs proved filtering but not **non-mutation** of the parent config. | Item 3 and AC-07 now require non-mutation, outer-key retention, and exact filtering in one table-driven witness. |
| R-5 | Traceability unpinned; durable witness could be silently weakened to an in-memory saver. | AC-10 pins REQ-YG-042/570 plus `req_coverage.py --strict`; AC-04 states an in-memory saver is not an equivalent witness. |

**Scope frozen:** D-1..D-6 per the judgement. Not authorised: `node_timeout.py`
or `_maybe_wrap_timeout()` changes, new timeout-wrapper tests, FR-797 relay
topology/edge/state/interrupt changes, graph or prompt artifact
creation/modification, LangGraph dependency changes, new config flags, OTel
span-schema changes beyond the accepted narrowing, streaming/async subgraph
expansion, or unrelated node types.

**Conditions:** C-1..C-6 GATE, all accepted. C-2 is worth restating because it
is the tempting shortcut: the lost outer span must **not** be recovered with a
`RunnableLambda` or any adapter that hides the compiled-graph type —
alternative 3's probe showed that is exactly what breaks native detection.

**Independent confirmation of the F-1 cut.** The judge reached the same
conclusion from the committed record alone, freezing it as AC-09 and as an
explicit not-authorised item. The cut is now doctrine for this FR, not a
preference.

### Questions for the human

None blocking.
