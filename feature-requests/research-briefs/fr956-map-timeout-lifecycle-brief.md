# Problem brief: a timed-out map branch keeps running with nobody owning it

**Prior art:** FR-069 (`feature-requests/069-map-node-timeout.md`)
introduced the per-branch timeout deliberately and recorded the leak as
a Known Limitation ("the submitted thread is **not** cancelled … a
follow-on FR may address this") — this brief is that follow-on. FR-936
(`feature-requests/FR-936-map-node-hardening.md`) bundled the concern
with three others and was SPLIT; its judgement
(`feature-requests/FR-936-map-node-hardening.judgement.md`, R-5, C-3,
AC-07/AC-08) **rejected** the bounded shared executor FR-936 proposed,
because a blocking timed-out callable keeps occupying its worker and
after `pool_size` permanent hangs later work queues forever — thread
count bounded, leakage converted into starvation. This brief is
deliverable D-3 and inherits the fence: overflow (D-2, FR-939), payload
projection (D-1), native retry (D-4) are out of bounds. FR-030
(`feature-requests/030-map-concurrency-control.md`, Won't Fix — "wrong
layer") declined concurrency control in the orchestrator; this brief
is not about how many branches run, only about what happens to one
that overran. FR-267/FR-270 (`feature-requests/FR-267-race-node-timeout-double-wrap-2.md`)
and FR-271 (`feature-requests/FR-271-async-race-node-cancellable.md`,
Proposed) fought the same class of problem in the `race` node —
abandoned loser threads holding provider connections — and FR-709
(`feature-requests/FR-709-race-loser-teardown-integration.md`,
Completed) landed loser teardown for race; those are the nearest
in-repo precedent and must be dispositioned, not repeated. A
REJECTED-FR sweep found no prior proposal on map-branch cancellation
specifically.

## Problem statement

`_execute_node_fn` runs a map branch under a one-shot
`ThreadPoolExecutor(max_workers=1)` and waits with
`Future.result(timeout=timeout)`; on `TimeoutError` the `finally`
clause calls `pool.shutdown(wait=False, cancel_futures=True)` and
returns (`yamlgraph/compile/map_compiler.py:93-113`). `cancel_futures`
only cancels *queued* futures; the one that timed out is already
running, so the worker thread continues until the callable returns on
its own — holding its LLM HTTP connection, its provider quota, its GIL
slices and its LangSmith span — while the graph has already recorded a
`TimeoutError` branch result (`map_compiler.py:142-160`) and moved on.

Nothing owns that thread afterwards. It is not in `errors`, not in the
route log, not reclaimable, and not visible to the operator. In a
short-lived CLI run the process exit reaps it. In a long-lived process
— a FastAPI worker, a scheduled census runner, the fi-catalog pilot's
500k-item fan-out — a realistic timeout rate accumulates orphan threads
for the life of the process, each still costing tokens against the
provider and each capable of completing *after* the reduce has already
been computed without it.

The problem: the map branch timeout is a *reporting* boundary, not a
*resource* boundary. It decides what the graph believes; it does not
decide what the process is doing.

## Classification

enforcement/latency-critical

## Constraints

- The FR-936 judgement scope fence applies (C-1, C-6): this concern
  ships alone — no overflow, payload-projection, retry, durability or
  concurrency-control changes ride along. Provider-wide client timeout
  refactors need their own judged scope (C-6 of the judgement).
- Investigation-first (FR-936 judgement R-5; rejudgement R-4, AC-06):
  before any mechanism is chosen, the lifecycle of one branch must be
  traced and witnessed from submission → timeout → cancellation or
  natural return → executor disposal → reclamation, and a *later
  healthy branch* must be shown to complete within a fixed deadline
  after more permanent hangs than any bound proposed.
- A thread-count ceiling, a bounded pool, or a recorded timeout error
  does not satisfy the contract (judgement C-3; rejudgement C-4). The
  accepted end state must either terminate the running work at the
  provider/client boundary or isolate it in an execution unit that can
  actually be terminated and whose capacity is reclaimed.
- Every leaked or reclaimed branch must be observable: attributed to
  node name and `_map_index`, surfaced in-band (state `errors` and/or
  the route decision log), never log-only (Commandment 6).
- Existing timeout semantics visible to graph authors must be
  preserved: `timeout` on the map node, `TimeoutError` classified as
  `ErrorType.TIMEOUT_ERROR` not `LLM_ERROR`, `on_error: skip` still
  collecting the survivors (FR-069 acceptance criteria, all `[x]`).
  The non-map `_maybe_wrap_timeout` path (FR-069 step 4) shares the
  primitive and must not regress; race nodes keep their native timeout
  (FR-267 lesson: do not double-wrap).
- Sync and async execution paths both run synchronous node functions
  (FR-069 rationale) — whatever the end state is, it must hold on
  `invoke()` and `ainvoke()` alike.
- Witnesses must not depend on network I/O; hangs must be simulated
  deterministically (the FR-069 tests already use `time.sleep`-based
  mocks: `tests/unit/test_map_node_timeout.py:90-156`).
- `is_this_a_graph`: must be answered — the research must state whether
  any graph-shaped construct (a watchdog node, a race-against-timer
  edge) could own branch lifecycle, or whether this is necessarily an
  executor-boundary contract.

## Witnessed incidents

- FR-069 Known Limitations (`feature-requests/069-map-node-timeout.md`,
  "When `Future.result(timeout=N)` raises `TimeoutError`, the submitted
  thread is **not** cancelled"): the defect was known and deferred at
  the moment the timeout shipped.
- 2026-08-31 FR-936 audit item 3 and judgement "What is sound": leak
  confirmed at `yamlgraph/compile/map_compiler.py:93-113`; the proposed
  bounded shared pool rejected in R-5 as starvation-by-design.
- 2026-09-02 FR-936 rejudgement AC-06/C-4: fixed-deadline liveness
  witness after excess hangs required; termination or isolation
  required; thread count alone insufficient.
- `race` node history (`feature-requests/FR-271-async-race-node-cancellable.md`
  "Symptom witnesses"): NV-240 integration suite paid ~60 s of post-exit
  pause draining orphan vertex HTTP calls; production races emitted
  `N-1` inferences nobody read, billed anyway; LangSmith showed orphan
  spans without parent correlation — the same failure class, in the
  sibling node, with production cost attached.
- `docs/plan-web-toolkit.md` "Existing map node audit" item 3: "At
  scale, zombie threads holding LLM connections"; the fi-catalog pilot
  (component D) is a long-lived run where the leak compounds.
- `tests/unit/test_map_node_timeout.py::TestWrapForReducerTimeout`
  (lines 90-156) asserts the *report* (timeout error result) and says
  nothing about the *thread* — the suite currently witnesses the
  reporting boundary only.
