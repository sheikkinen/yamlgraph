# Feature Request: Map Branch Timeout Lifecycle — condemn-or-absolve witness and mechanism verdict

**Priority:** HIGH
**Type:** Bug investigation / witness test
**Status:** Judged — APPROVED WITH REVISIONS
([FR-956-map-branch-timeout-lifecycle-investigation.judgement.md](FR-956-map-branch-timeout-lifecycle-investigation.judgement.md),
2026-09-02, sole route). Revisions R-1–R-6 **not yet folded**; no
implementation authority until they are folded and the judgement is
human-reviewed (C-1, C-7). Headline revisions: preserve a concrete
dissent in the in-body research record (R-1); delete the
bounded-leak absolution path — accepting a known unbounded leak is not
an outcome (R-2); split the LLM evidence into constructor witness vs
deterministic fake, no mocked SDK-bound claim (R-3); attribution stays
in `PipelineError`/reducer row, no route-log event (R-4); FR-706-style
suite-safe `xfail(strict=True)` condemned witnesses with pinned
absolute deadlines (R-5); per-sub-node witnesses and a broader CAP-11
requirement (R-6).
**Effort:** 1.5 days
**Requested:** 2026-09-02
**First consumer / first event:** the fi-catalog pilot (component D,
`docs/plan-web-toolkit.md`) — the first long-lived map run where a
realistic timeout rate compounds over hours. Nearer-term: any FastAPI
worker or scheduled runner (`examples/daily_digest`, `examples/booking`)
executing map nodes with `timeout` set.
**Research:** in-body dispositioned alternatives table below (FR-889
style, sanctioned by `TEMPLATE.md`). The FR-890 route was run on
2026-09-02 against `feature-requests/research-briefs/fr956-map-timeout-lifecycle-brief.md`
(preflight passed, five personas executed) and failed in the reducer:
`precedent names nonexistent FR-069`. FR-069 exists as
`feature-requests/069-map-node-timeout.md`; the checker at
`examples/demos/research-route/nodes/research_tools.py:391-395` globs
only `FR-{number}` filenames — the legacy-filename blind spot FR-701
recorded for the capability registry. Any brief that names FR-069 as
prior art (this one must) fails the same way. The defect is parked in
FR-936's adjacent findings; no persona output was persisted.
**Prior art:** [069-map-node-timeout.md](069-map-node-timeout.md) — the
origin; its Known Limitations records this leak and defers it to "a
follow-on FR". This is that FR. [FR-936-map-node-hardening.md](FR-936-map-node-hardening.md)
— SPLIT parent, deliverable **D-3**; its judgement R-5 **rejected** the
bounded shared executor (starvation by design) and its rejudgement
AC-06/C-4 requires termination or isolation, reclamation, and a
fixed-deadline liveness witness. [FR-708-llm-client-request-timeout.md](FR-708-llm-client-request-timeout.md)
(Completed) — bounds every `create_llm` client with a request timeout
and `max_retries=2`; it caps how long an *LLM* branch can leak, and is
the "terminate at the client boundary" half the judgement names.
[FR-271-async-race-node-cancellable-2.md](FR-271-async-race-node-cancellable-2.md)
(Implemented), [FR-706-race-timeout-loop-liveness.md](FR-706-race-timeout-loop-liveness.md)
(Completed, CONDEMNED verdict), [FR-720-close-trace-spans-on-loser-cancel.md](FR-720-close-trace-spans-on-loser-cancel.md)
(Completed) — the `race` node's arc through the same failure class:
asyncio cancellation at await points, then the discovery that
cancel-only still blocks the caller, then span hygiene. That arc is the
nearest mechanism precedent and FR-706's condemn-or-absolve witness is
the shape this FR copies. [030-map-concurrency-control.md](030-map-concurrency-control.md)
(Won't Fix) — concurrency, not lifecycle. [FR-390](FR-390-watcher-validate-fix-context-and-sanity-timeout.md),
[FR-454](FR-454-eval-timeout-config.md) — watcher/eval wall-clock knobs,
vocabulary only. No REJECTED FR governs map-branch cancellation.

## Summary

Investigation-first, per the judgement: witness the full lifecycle of a
timed-out map branch (submission → timeout → return or termination →
executor disposal → reclamation), prove or disprove that a later
healthy branch completes within a fixed deadline after more hangs than
any bound, classify hang sources by sub-node type, and render a
mechanism verdict that an implementation FR can enforce. No mechanism
is authorized here except in-band attribution of a leaked branch.

## Value Statement

Operators learn, from witnesses rather than belief, whether a map
timeout is a resource boundary or only a reporting boundary — and the
implementation FR that follows inherits a proven target instead of a
design guess (the fate of FR-936's rejected shared pool).

## Problem

`_execute_node_fn` (`yamlgraph/compile/map_compiler.py:93-113`) waits on
`Future.result(timeout)`; on `TimeoutError` it calls
`shutdown(wait=False, cancel_futures=True)` and returns.
`cancel_futures` cancels only *queued* futures; the running one keeps
its thread, its HTTP connection, its provider quota and its LangSmith
span until the callable returns. The graph records a `TimeoutError`
row (`map_compiler.py:142-160`) and moves on. The same primitive backs
non-map nodes (`yamlgraph/node_timeout.py:41-58`). Nothing owns the
thread afterwards: not `errors`, not the route log, not the operator.

What is *not* yet known, and what this FR exists to establish:

1. **How long a leaked branch actually lives.** For `llm` sub-nodes,
   FR-708 bounds each request (`request_timeout` + `max_retries=2`), so
   the leak should be bounded at roughly `request_timeout × 3` — but
   nobody has measured it. For `python`, `tool_call`, `agent` and
   `subgraph` sub-nodes there is no client boundary: the leak is
   unbounded.
2. **Whether liveness holds.** The one-shot pool per branch means k
   hung branches cost k threads but should not starve the (k+1)th —
   the property the rejected shared pool would have broken. Unproven.
3. **Whether a late-returning branch can corrupt the reduce.** A leaked
   branch that eventually returns is inside a dead LangGraph task; its
   return value should be discarded, but a `python` sub-node with side
   effects (file writes, `write_data_file`) completes them after the
   reduce ran.
4. **Which of the mechanism classes below is even applicable** given
   that node functions are synchronous on both execution paths (FR-069
   rationale) and that the race node's asyncio route still blocked the
   caller until FR-706/707.

## Ideal Result

A committed witness suite states, per sub-node type, exactly what
happens to a timed-out branch and for how long; a later healthy branch
is proven to complete within a fixed deadline after more permanent
hangs than any proposed bound; every leaked branch is attributed
in-band (node, `_map_index`, elapsed) so operators can see it; and a
single mechanism class is chosen with evidence, handed to an
implementation FR with the fence already drawn.

## Proposed Solution

### 1. Lifecycle witness (RED first, `@pytest.mark.slow` where sleeping)

`tests/unit/test_fr956_map_timeout_lifecycle.py`, modelled on FR-706's
condemn-or-absolve shape:

- **Reclamation**: after `k` branches hang (`time.sleep` mocks, k > any
  pool size a design might propose, e.g. k = 8), assert thread
  population returns to baseline within the hang duration + ε, and
  record whether it does so *before* (termination) or *only after*
  (natural return) the mock finishes. Expected today: CONDEMNED on
  termination, ABSOLVED on eventual return.
- **Liveness**: after the same k hangs, a healthy branch completes
  within `timeout × 2`. Expected today: ABSOLVED (one-shot pools);
  this witness is what forbids any future shared-pool design.
- **Late return**: a hung `python` sub-node that writes a marker file
  after the reduce has run; assert the marker appears (documents the
  side-effect hazard) and that the collected results do not change.
- **Attribution**: the `errors` entry and the route decision log line
  for the timed-out branch carry node name and `_map_index`. Expected
  today: node name is the literal `"map_subnode"`
  (`map_compiler.py:156`) — CONDEMNED; this is the one production
  change authorized below.
- **Bounded-leak measurement (llm)**: with a mocked provider client
  whose request honours `request_timeout`, measure leaked-thread
  lifetime against FR-708's bound.

### 2. The one authorized production change

Attribute the timeout error to the real map node and branch:
`PipelineError.from_exception(e, node=f"{map_name}[{index}]", …)` and
include `elapsed` in `_error`. No executor, thread, or cancellation
change.

### 3. Mechanism verdict (recorded in this FR's Implementation Status)

| class | mechanism | precedent | fits sync node fns? | what the witness must show | disposition (to be filled by the investigation) |
|---|---|---|---|---|---|
| A. Client-boundary bound + attribution | Rely on FR-708 request timeouts for `llm`; attribute leaks in-band; accept bounded leak | FR-708; judgement "real cure is client-level request timeouts" | yes | leak lifetime ≤ FR-708 bound for llm; unbounded for python/agent | candidate — cheapest; leaves non-LLM sub-nodes uncovered |
| B. Cooperative deadline in state | `_deadline` injected into the branch payload (FR-069 deferred it); python/agent tools check it | FR-069 alternatives ("`_deadline: float` in state") | yes | tools that honour it stop; tools that don't still leak | candidate — opt-in, composes with A; conflicts with FR-955's key set (must be an always-key) |
| C. Terminable execution unit for non-LLM sub-nodes | Run `python`/`agent`/`tool_call` branches in a subprocess (or interpreter) that can be killed | judgement R-5 "isolate it in a genuinely terminable execution unit"; FR-936 rejected process isolation as heavyweight *for all branches* | yes | kill reclaims capacity; state must be picklable; cost per branch | candidate — heavy; measure spawn cost vs branch duration |
| D. Cancellable async branch | Run the sub-node as a coroutine and cancel at an await point | FR-271-2 (race node), FR-706 (cancel-only still blocked the caller), FR-707 | **no** — node fns are sync (FR-069); would require an async node contract | n/a | REJECTED for this scope — not a map-node change; belongs to an async-node FR if ever |
| E. Daemon threads + accounting | Mark branch threads daemon; count and report | #169 workaround (race) | yes | count only | REJECTED — helps process exit only; judgement C-3 forbids count-only |
| F. Bounded shared executor | One pool per map node | FR-936 §3 | yes | — | **REJECTED by the judgement (R-5)**: converts leakage into starvation; the liveness witness above is its permanent tombstone |

`is_this_a_graph`: no. A watchdog node or a race-against-timer edge
runs in the same superstep machinery and cannot reclaim a thread the
executor abandoned; the boundary is the executor call at
`map_compiler.py:110`.

## Acceptance Criteria

- [ ] AC-01 RED: reclamation witness committed and failing on
      termination (thread alive after `TimeoutError`) for `python` and
      `llm` sub-node mocks; k ≥ 8 hangs.
- [ ] AC-02: liveness witness — after k hangs a healthy branch completes
      within `timeout × 2`; committed as a permanent guard against any
      shared-pool design (judgement C-3, rejudgement AC-06).
- [ ] AC-03: late-return witness documents the side-effect hazard;
      collected results unchanged.
- [ ] AC-04 RED→GREEN: timeout `errors` entry names `"<map_node>[<index>]"`
      not `"map_subnode"`; `_error` carries `elapsed`; route log line
      for the branch carries the same attribution.
- [ ] AC-05: bounded-leak measurement for an `llm` sub-node against a
      client honouring `request_timeout`; result recorded in the FR
      with numbers.
- [ ] AC-06: per-sub-node-type lifecycle table (submission → timeout →
      return/termination → disposal → reclamation) recorded in this FR's
      Implementation Status with the witness that produced each row.
- [ ] AC-07: mechanism verdict recorded: exactly one of A–C (or a named
      composition) chosen, each other class dispositioned with the
      witness evidence; F and E remain rejected; D routed out of scope.
- [ ] AC-08: an implementation FR is filed (or this FR's status becomes
      ABSOLVED with rationale if class A is judged sufficient), citing
      this FR's witnesses as its RED.
- [ ] AC-09: one new CAP-11 requirement (branch timeout attribution);
      `@pytest.mark.req` on every new test; `req_coverage.py --strict` green.
- [ ] AC-10: no change to `_execute_node_fn`'s executor, to
      `node_timeout.py`, to race-node timeouts, to `llm_providers.py`
      (FR-708), or to overflow/payload/retry surfaces (FR-939/955/957).
- [ ] AC-11: `reference/graph-yaml.md:643` known-limitation paragraph
      updated to cite this FR and the measured bound; one changelog
      fragment (`fix`, attribution) and one diary reflection.

## Alternatives Considered

The table in §3 is the dispositioned record. In addition: **doing
nothing until D** (rejected — the leak compounds in every long-lived
process today, and D's chunked driver would *increase* the number of
timeouts per process); **removing the per-branch timeout and relying
solely on FR-708** (rejected — `python`/`agent`/`tool_call` branches
have no client boundary, and FR-069's `on_error: skip` semantics are in
use).

## Related

- `yamlgraph/compile/map_compiler.py:93-113,139-160`
- `yamlgraph/node_timeout.py:15-60`
- `tests/unit/test_map_node_timeout.py:90-156` (reporting-boundary witnesses, kept)
- `yamlgraph/utils/llm_providers.py` (FR-708 `_request_timeout`, `_bounded`)
- `docs/plan-web-toolkit.md` audit item 3
- `docs/2026-09-02-brainstorm-business-use-cases.md` §5.2

### Questions for the human (as options, or 'none')

1. If the investigation shows class A bounds `llm` leaks to ≤ 3 ×
   `request_timeout` and only `python`/`agent` sub-nodes leak
   unbounded: **file class C for non-LLM sub-nodes only** (recommended
   — smallest terminable unit where it is needed) vs **accept bounded
   leak + attribution and close** vs **class B cooperative deadline
   first**. Evidence arrives with AC-05/AC-06.
