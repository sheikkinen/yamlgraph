# Feature Request: Map Branch Timeout Lifecycle — condemn-or-absolve witness and mechanism verdict

**Priority:** HIGH
**Type:** Bug investigation / witness test
**Status:** Judged — APPROVED WITH REVISIONS
([FR-956-map-branch-timeout-lifecycle-investigation.judgement.md](FR-956-map-branch-timeout-lifecycle-investigation.judgement.md),
2026-09-02, sole route). **R-1–R-6 folded 2026-09-02** into the body
below; the judgement's revised acceptance criteria AC-01–AC-13 and
gates C-1–C-7 are the frozen contract. Authority activates on human
review of the judgement (C-1, C-7).
**Effort:** 1.5 days
**Requested:** 2026-09-02
**First consumer / first event:** the fi-catalog pilot (component D,
`docs/plan-web-toolkit.md`) — the first long-lived map run where a
realistic timeout rate compounds over hours. Nearer-term: any FastAPI
worker or scheduled runner (`examples/daily_digest`, `examples/booking`)
executing map nodes with `timeout` set.
**Research:** in-body dispositioned alternatives table below (FR-889
style, sanctioned by `TEMPLATE.md:17-20`; the judgement accepted this
form). The FR-890 route was run on 2026-09-02 against
`feature-requests/research-briefs/fr956-map-timeout-lifecycle-brief.md`
(preflight passed, five personas executed) and failed in the reducer:
`precedent names nonexistent FR-069`. FR-069 exists as
`feature-requests/069-map-node-timeout.md`; the checker at
`examples/demos/research-route/nodes/research_tools.py:391-395` globs
only `FR-{number}` filenames — the legacy-filename blind spot FR-701
recorded for the capability registry. **No persona output was
persisted; nothing below is attributed to that run** (R-1). The defect
is parked in FR-936's adjacent findings.
**Prior art:** [069-map-node-timeout.md](069-map-node-timeout.md) — the
origin; its Known Limitations records this leak and defers it to "a
follow-on FR". This is that FR. [FR-936-map-node-hardening.md](FR-936-map-node-hardening.md)
— SPLIT parent, deliverable **D-3**; its judgement R-5 **rejected** the
bounded shared executor (starvation by design) and its rejudgement
AC-06/C-4 requires termination or isolation, reclamation, and a
fixed-deadline liveness witness. [FR-708-llm-client-request-timeout.md](FR-708-llm-client-request-timeout.md)
(Completed) — bounds every `create_llm` client with a request timeout
and `max_retries=2`; it is the "terminate at the client boundary" half
the judgement names, and it rules that a mocked hang cannot validate
SDK timeout behaviour (`FR-708:86-88,102-104`). [FR-271-async-race-node-cancellable-2.md](FR-271-async-race-node-cancellable-2.md)
(Implemented), [FR-706-race-timeout-loop-liveness.md](FR-706-race-timeout-loop-liveness.md)
(Completed, CONDEMNED verdict), [FR-720-close-trace-spans-on-loser-cancel.md](FR-720-close-trace-spans-on-loser-cancel.md)
(Completed) — the `race` node's arc through the same failure class;
FR-706's condemn-or-absolve witness contract is the shape this FR
copies. [030-map-concurrency-control.md](030-map-concurrency-control.md)
(Won't Fix) — concurrency, not lifecycle. [FR-390](FR-390-watcher-validate-fix-context-and-sanity-timeout.md),
[FR-454](FR-454-eval-timeout-config.md) — watcher/eval wall-clock knobs,
vocabulary only. No REJECTED FR governs map-branch cancellation.

## Summary

Investigation-first, per the judgement: witness the full lifecycle of a
timed-out map branch (submission → timeout → return or termination →
executor disposal → reclamation), prove or disprove that a later
healthy branch completes before a pinned absolute deadline after more
hangs than any bound, classify hang sources by sub-node type, and
render a mechanism verdict that an implementation FR can enforce. The
only production change authorized is truthful in-band attribution of a
timed-out branch. **A known unbounded leak is not an acceptable
outcome** (R-2).

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
row (`map_compiler.py:142-160`) whose `PipelineError.node` is the
literal `"map_subnode"` (`map_compiler.py:156`) and moves on. The same
primitive backs non-map nodes (`yamlgraph/node_timeout.py:41-58`).
Nothing owns the thread afterwards.

What is *not* yet known, and what this FR exists to establish:

1. **How long a leaked branch actually lives, per sub-node class.** For
   `llm` sub-nodes FR-708 configures a finite request timeout and
   bounded retries on the client; whether and how that bounds the
   *map thread's* lifetime is unmeasured, and a mock cannot measure the
   SDK's behaviour (R-3). `python`, `tool_call`, `agent` and `subgraph`
   branches have no client boundary; agents and tools may perform many
   calls or non-LLM work, so an agent's lifetime cannot be inferred from
   one request timeout (R-6).
2. **Whether liveness holds.** One-shot pools should not starve the
   (k+1)th branch after k hangs — the property the rejected shared pool
   would have broken. Unproven.
3. **Whether a late-returning branch can corrupt the reduce.** A leaked
   `python` branch with side effects completes them after the reduce.
4. **Which mechanism class is applicable** given synchronous node
   functions on both execution paths (FR-069) and the race node's
   experience that cancel-only still blocked the caller (FR-706).

## Ideal Result

A committed witness suite states, per sub-node class, exactly what
happens to a timed-out branch and for how long; a later healthy branch
is proven to complete before a pinned absolute deadline after more
permanent hangs than any proposed bound; every timed-out branch is
attributed in-band to its authored map node and index with its elapsed
time; and a single compliant mechanism class or composition is chosen
with evidence and handed to an implementation FR — or, only if every
supported sub-node class is proven reclaimed with liveness preserved,
the investigation is ABSOLVED.

## Proposed Solution

### 1. Lifecycle witness suite (R-5, R-6) — `tests/unit/test_fr956_map_timeout_lifecycle.py`

FR-706's condemn-or-absolve contract applies
(`FR-706-race-timeout-loop-liveness.md:85-103,121-125`):

- **Bounded fakes.** Every hanging fake terminates in bounded time on
  its own (a `threading.Event` with a hard cap), never relying on the
  behaviour under test.
- **Witness-owned identity.** Each fake registers its thread identity
  and completion event; assertions use those, not only global thread
  population.
- **Pinned constants with order-of-magnitude separation:** map
  `timeout` ≪ healthy-branch absolute deadline ≪ fake hang duration.
  The deadline is an explicit absolute value suitable for CI (not
  `timeout × 2`) and expires well before the fakes naturally return.
  `k ≥ 8` hung branches. The FR records `k`, timeout, hang duration,
  deadline, baseline, peak, natural-return and reclamation timings.
- **Reclamation / termination.** After k hangs, assert witness-owned
  running work is terminated and its execution capacity released
  *before* the fakes' natural return. Expected today: **CONDEMNED**.
  A condemned termination assertion is committed as
  `xfail(strict=True)` naming the follow-up implementation FR, so the
  suite stays committable and the eventual fix produces XPASS until the
  marker is removed. The eventual-return witness (threads return to
  baseline once fakes finish) is an ordinary passing test.
- **Liveness.** After the same k hangs a healthy branch completes
  before the pinned absolute deadline. Expected today: ABSOLVED
  (one-shot pools). Committed as a permanent guard against any
  starvation-producing shared-capacity design (judgement C-4).
- **Late return.** A hung `python` branch writes a marker file after
  the reduce has run; assert the marker appears and the collected
  results are unchanged.
- **Attribution.** See §2. Expected today: CONDEMNED (`"map_subnode"`).
- **Definitions.** *Disposal* = executor `shutdown` invocation.
  *Reclamation* = termination of the witness-owned running work plus
  release of its execution capacity.

Per-sub-node evidence (R-6): the lifecycle table (§4) names, for each of
`llm`, `python`, `tool_call`, `agent`, `subgraph`, an executable witness
for each transition, or cites the shared-wrapper witness and justifies
why no class-specific boundary changes the conclusion.

### 2. The one authorized production change — in-band attribution (R-4)

Inside `yamlgraph/compile/map_compiler.py` only:

- pass the authored map node name into `wrap_for_reducer`;
- set `PipelineError.node` to `"<map_node>[<index>]"`;
- put numeric `map_index` and `elapsed_seconds` in
  `PipelineError.details` (`yamlgraph/models/schemas.py:31-47`);
- keep the reducer row's `_map_index`, add numeric `_elapsed_seconds`,
  keep `_error` human-readable including the elapsed duration;
- `ErrorType.TIMEOUT_ERROR` classification and `on_error: skip`
  survivor collection are unchanged.

No route-log event is added: the route decision log emits route and
fan-out records from routing decisions, not branch execution
(`yamlgraph/utils/route_log.py:213-223`; `yamlgraph/routing.py:14-113`);
a timeout event would be a separate observability contract (C-5).

### 3. LLM evidence, stated honestly (R-3)

Split into three claims that are never conflated:

1. **Constructor configuration** — cite or rerun the FR-708 witness
   that the relevant `create_llm` client receives a finite,
   wrapper-correct request timeout and bounded retries
   (`yamlgraph/utils/llm_providers.py`, REQ-YG-539 matrix).
2. **Deterministic model** — a fake callable that honours a supplied
   deadline measures *map-thread lifetime under a deadline-honouring
   callable*. It is labelled as such; it is not a measurement of
   provider SDK behaviour.
3. **Provider behaviour** — any real-provider probe is non-gating and is
   never represented by a mock.

No `3 × request_timeout` wall-clock bound is stated unless an executable
witness including retry/backoff proves that exact bound for the named
wrapper; configured per-attempt timeout and retry count are recorded
separately from observed wall time. `reference/graph-yaml.md` records
only bounds the accepted evidence establishes.

### 4. Lifecycle table and mechanism verdict (recorded in Implementation Status)

Per-class rows (`llm`, `python`, `tool_call`, `agent`, `subgraph`) ×
transitions (submission, timeout, return/termination, disposal,
reclamation), each cell naming its witness. Then the verdict over the
classes below.

| class | mechanism | precedent | fits sync node fns? | what the witness must show | disposition |
|---|---|---|---|---|---|
| A. Client-boundary bound + attribution | Rely on FR-708 request timeouts for `llm`; attribute leaks in-band | FR-708; judgement "real cure is client-level request timeouts" | yes | leak lifetime for `llm` under a deadline-honouring callable; **unbounded** for python/agent/tool | candidate **only as a component** — alone it leaves non-LLM classes unbounded and fails the gate (R-2) |
| B. Cooperative deadline in state | `_deadline` in the branch payload (FR-069 deferred it); python/agent tools check it | FR-069 alternatives | yes | tools that honour it stop; tools that do not still leak | candidate component — opt-in; alone fails the gate (R-2); must be an always-key under FR-955 |
| C. Terminable execution unit for non-LLM classes | Run `python`/`agent`/`tool_call` branches in a killable unit (subprocess or interpreter) | judgement R-5 "isolate it in a genuinely terminable execution unit"; FR-936 rejected isolation *for all branches* as heavyweight | yes | kill reclaims capacity; picklable state; spawn cost vs branch duration | candidate — the only class that terminates arbitrary work; cost must be measured |
| D. Cancellable async branch | Coroutine cancelled at an await point | FR-271-2 (race), FR-706, FR-707 | **no** — node fns are sync (FR-069) | n/a | REJECTED for this scope — belongs to an async-node FR if ever |
| E. Daemon threads + accounting | Mark daemon; count and report | #169 workaround (race) | yes | count only | REJECTED — process-exit only; C-4 forbids count-only |
| F. Bounded shared executor | One pool per map node | FR-936 §3 | yes | — | **REJECTED by the FR-936 judgement (R-5)**: leakage becomes starvation; the liveness witness is its permanent tombstone |

**Outcome contract (R-2).** ABSOLVED only if executable witnesses prove
that *every* currently supported map sub-node class reclaims timed-out
work and preserves later-branch liveness. Otherwise an implementation
FR is filed selecting an A–C composition that terminates work at a
client boundary or isolates it in a terminable unit for **every** class
shown to leak. The human chooses among compliant mechanisms after
reading the evidence; accepting a known unbounded leak is not an
available option (C-2).

**Dissent preserved (R-1).** The strongest evidence-backed case against
the direction the table leans toward (an A + C composition, with C for
non-LLM classes) is this: process isolation per branch is the mechanism
FR-936 itself rejected as heavyweight, and at census scale the spawn
and pickling cost per branch may exceed the branch's own work; the
race arc (FR-271-2 → FR-706 → FR-707) shows that adding cancellation
machinery produced a second class of incident before it produced a
cure. That dissent supports **B as the primary mechanism** — make the
deadline a mandatory part of the python-tool and agent-tool contract
(a tool that cannot honour a deadline is rejected at load), with A for
`llm` — and treats C as a last resort for tools that cannot be made
cooperative. The investigation can confirm or reject it with two
measurements it already produces: the per-branch spawn/teardown cost
of C against the median branch duration, and the fraction of in-repo
python/agent tools that can honour a deadline without rewrite. If
spawn cost is small relative to branch duration, the dissent loses; if
most tools can be made cooperative cheaply, the dissent wins.

`is_this_a_graph`: no. A watchdog node or a race-against-timer edge
runs in the same superstep machinery and cannot reclaim a thread the
executor abandoned; the boundary is the executor call at
`map_compiler.py:110`.

## Acceptance Criteria

Frozen by the judgement; the enforcer satisfies this list.

- [ ] AC-01: The in-body research record retains six genuine mechanism classes, explicit precedent dispositions, `is_this_a_graph: no`, and one concrete evidence-backed dissent; it does not attribute evidence to the unpersisted persona run.
- [ ] AC-02: Bounded lifecycle witnesses launch `k >= 8` timed-out branches, identify witness-owned running work, and record timeout, hang, deadline, baseline, peak, natural-return, and reclamation timings in the FR.
- [ ] AC-03: The termination assertion records CONDEMNED or ABSOLVED for `python` and deterministic LLM-model branches; any condemned committed assertion is `xfail(strict=True)` and names the follow-up implementation FR.
- [ ] AC-04: After the same excess hangs, a healthy branch completes before a pinned absolute deadline that is well below the fake hang duration; the witness is a permanent guard against starvation-producing shared capacity.
- [ ] AC-05: A late-returning Python branch completes its marker side effect after reduce while the already-collected results remain unchanged.
- [ ] AC-06: Timeout state output sets `PipelineError.node` to `"<map_node>[<index>]"`, puts numeric `map_index` and `elapsed_seconds` in `PipelineError.details`, and emits `_map_index`, numeric `_elapsed_seconds`, and a human-readable elapsed `_error` in the reducer row; timeout type and survivor collection remain unchanged.
- [ ] AC-07: LLM evidence distinguishes constructor configuration, deterministic fake behavior, and actual provider behavior; no mock is claimed to prove SDK timeout behavior or an untested `3 x request_timeout` wall-clock bound.
- [ ] AC-08: The FR records a lifecycle row for `llm`, `python`, `tool_call`, `agent`, and `subgraph`, with an executable witness or justified shared-wrapper witness for each submission, timeout, return/termination, disposal, and reclamation transition.
- [ ] AC-09: The mechanism verdict chooses and dispositions A-C with evidence, keeps D-F rejected/out of scope as applicable, and may declare ABSOLVED only if every supported sub-node class is proven reclaimed with liveness preserved.
- [ ] AC-10: If any supported class remains unbounded, a separately judged implementation FR is filed for a compliant termination/isolation composition; accepting a known unbounded leak is not an outcome.
- [ ] AC-11: One minimum necessary CAP-11 requirement states the lifecycle, attribution, and post-timeout liveness contract; every new test has a semantically matching `@pytest.mark.req`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-12: No executor, non-map timeout, route-log, provider, race, overflow, payload, retry, async-contract, durability, or scheduling implementation changes are made.
- [ ] AC-13: `reference/graph-yaml.md` cites only evidenced bounds; one fix-scoped attribution changelog fragment and one diary reflection are committed.

## Scope (frozen by the judgement)

| Deliverable | Surface |
|---|---|
| D-1 | This FR: revisions, observed verdict, lifecycle table, and mechanism disposition |
| D-2 | `tests/unit/test_fr956_map_timeout_lifecycle.py` bounded lifecycle, liveness, late-return, and attribution witnesses |
| D-3 | `yamlgraph/compile/map_compiler.py` only for map-name/index/elapsed timeout attribution; no executor or cancellation change |
| D-4 | One minimum necessary requirement update in `capabilities/CAP-11-subgraph-map.yaml` (lifecycle + attribution + post-timeout liveness) |
| D-5 | Focused `reference/graph-yaml.md:643` limitation update, attribution changelog fragment (`fix`), and one diary reflection |
| D-6 | A separately judged implementation FR if any supported sub-node class remains unbounded |

Not authorized: changing `_execute_node_fn`'s executor lifecycle;
changing `yamlgraph/node_timeout.py`; adding or changing route-log
events; changing provider constructors, request timeouts, retries, race
behaviour, map overflow (FR-939), branch payload projection (FR-955),
native retry (FR-957), async node contracts, graph scheduling,
durability, checkpointing, or process isolation. The selected
termination mechanism itself is not authorized by FR-956 (C-6).

## Alternatives Considered

The table in §4 is the dispositioned record, with the dissent
preserved. In addition: **doing nothing until D** (rejected — the leak
compounds in every long-lived process today, and D's chunked driver
would *increase* the number of timeouts per process); **removing the
per-branch timeout and relying solely on FR-708** (rejected —
`python`/`agent`/`tool_call` branches have no client boundary, and
FR-069's `on_error: skip` semantics are in use).

## Related

- [FR-956-map-branch-timeout-lifecycle-investigation.judgement.md](FR-956-map-branch-timeout-lifecycle-investigation.judgement.md)
- `yamlgraph/compile/map_compiler.py:93-113,139-160,329-331`
- `yamlgraph/node_timeout.py:15-60`, `yamlgraph/models/schemas.py:31-47`
- `tests/unit/test_map_node_timeout.py:90-156` (reporting-boundary witnesses, kept)
- `yamlgraph/utils/llm_providers.py` (FR-708 `_request_timeout`, `_bounded`)
- `yamlgraph/utils/route_log.py:213-223`, `yamlgraph/routing.py:14-113` (why no route-log event)
- `docs/plan-web-toolkit.md` audit item 3
- `docs/2026-09-02-brainstorm-business-use-cases.md` §5.2

## Judgement (2026-09-02)

**Verdict:** APPROVED WITH REVISIONS — see
[FR-956-map-branch-timeout-lifecycle-investigation.judgement.md](FR-956-map-branch-timeout-lifecycle-investigation.judgement.md)
for the full rubric, R-1–R-6, AC-01–AC-13 and C-1–C-7. R-1–R-6 are
folded above (§4 dissent; §4 outcome contract replacing the absolution
path; §3 honest LLM evidence; §2 attribution without a route-log event;
§1 suite-safe witnesses and definitions; §1/§4 per-class evidence and
the broadened CAP-11 requirement). Authority activates on human review.

### Questions for the human (as options, or 'none')

None at this stage. The choice among *compliant* mechanism compositions
(A–C) is made after the evidence in AC-08/AC-09 exists; "accept bounded
leak and close" is no longer an option (R-2).
