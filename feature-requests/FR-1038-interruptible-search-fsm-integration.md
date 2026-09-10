# Feature Request: Interruptible search as an ownership-safe async FSM integration

**Priority:** HIGH
**Type:** Enhancement — shared-bridge correctness and executable integration example
**Status:** Proposed — not judged; no implementation authority
**Publication scope:** Docs-only filing. Merging this proposal records work for
future judgement; it does not approve the proposed API or authorize implementation.
**Effort:** Estimate after the deterministic RED witness; no measured estimate yet
**Requested:** 2026-09-10
**First consumer / first event:** a developer using the FSM Router pattern for
interactive search, when a second query arrives before the first graph finishes.
**Research:** [Research record and alternatives](#research-record-and-alternatives)
— in-body source-grounded record under the equivalent-record provision of the
feature-request workflow; no research-adapter run is claimed. This record must
be committed with the proposal before judgement grants authority.
**Prior art:**
- [FR-346](FR-346-extract-shared-fsm-bridge-phase1.md): shared bridge extraction;
  reuse it rather than create another runner.
- [FR-369](FR-369-fsm-snapshot-hooks-phase2-subclassing.md): implemented snapshots
  and hooks; this proposal adds invocation ownership, not replacement hooks for
  their existing observation purpose.
- [FR-391](FR-391-fsm-phase-aware-event-resolution.md): phase-aware completion;
  retain the event cascade, do not reopen its implementation.
- [FR-392](FR-392-fsm-on-launch-hook.md): launch hook; use its existing extension
  role, not a second example-local dispatch implementation.
- [FR-755](FR-755-utils-fsm-ownership-ruling.md): enforced contrib-tier ownership;
  this is supported peripheral integration, not a new dependency of graph core.
- [FR-756](FR-756-core-test-isolation.md): test-boundary classification; retain
  normal collection/traceability and classify example-dependent tests as process.
- [FR-757](FR-757-fsm-contrib-relocation.md): proposed package relocation; this
  FR changes behaviour at the existing path and does not implement that move.

## Summary

Add a small, offline interruptible-search example and a deterministic integration
suite that runs the real statemachine-engine, shared `YamlgraphAsyncAction`,
compiled YAMLGraph and control-socket event path. Use it to establish and enforce
the shared bridge's explicit supersession contract: after a newer invocation owns
a search, an older invocation cannot commit current state, dispatch an ordinary
completion/failure, or release the newer invocation's running guard.

The example is a companion to the existing FSM Router, not a replacement. Its
search catalogue is synthetic and local. No browser, external search provider,
LLM credentials or production service is required.

## Value Statement

FSM integrators get one executable example and regression contract for accepting
new input while graph work remains active, instead of inferring concurrency safety
from a sequential router demonstration and mocked runner tests.

## Problem

At inspected YAMLGraph revision `0dba283b789e7a11680ca1f27c29eb6d185ea4bb`:

1. The router's action is already a thin subclass of the shared async action.
   Its happy path processes classification and response sequentially; it does
   not demonstrate superseding unfinished work.
2. `TestFSMIntegration` in the router example parses YAML and checks action types.
   It does not instantiate or run an engine. The name and test README overstate
   that coverage.
3. Shared tests inject mocked graph loading/execution. Ordinary guard cleanup is
   covered; late cleanup after a new owner begins is not established by that test.
4. The shared runner invokes success/error hooks before its dispatch gate and
   removes the state guard unconditionally in `finally`. A dispatch veto does
   not protect earlier hook mutations or ownership-blind guard removal.
5. A same-state transition must not be assumed to repeat entry actions: the
   inspected engine 1.0.90 resets completed action indices on different-state
   transitions. The example must establish re-entry through actual lifecycle
   events, not by modifying engine internals or test-writing guard dictionaries.

These are source observations, not a claimed executed concurrency reproducer.
The first implementation task is a deterministic RED witness. If the intended
failure cannot be reproduced, record why and revise the proposal before adding
production mechanisms.

## Ideal Result

A developer starts the offline example, submits “cafes in Helsinki”, then
“cafes in Tampere” before the first result completes, and sees only the current
result published. The automatic test deliberately releases old work late and
proves the same outcome through real engine transitions and graph execution.
Ownership is handled once in the shared integration; search-specific publication
policy stays in the example. The result does not depend on a lucky sleep interval.

## Proposed Solution

### 1. One bounded application: interruptible local search

Create `examples/fsm_interruptible_search/` with a small FSM config, one graph,
thin action wrappers, typed request/result models, a synthetic catalogue, a CLI
driver and documentation. Keep new Python-importable paths in snake_case.
Actual graph artifacts must be authored through the repository's graph-authoring
route during enforcement; this FR does not create those artifacts.

Inputs are submit-query, clear and stop. Results are console publications, not
external writes. A submit accepted by the FSM receives a monotonically increasing
request revision scoped to that application session. Repeating the same text
creates a new revision: query text is content, **not invocation identity**.

Use an explicit preparation/re-entry state before the processing state so a new
query really invokes the action again. Do not rely on a processing self-loop
re-running one-shot actions. Request revision assignment and supersession happen
in that preparation action, synchronously, before new graph work is launched.
The FSM event-processing order defines acceptance order, not wall-clock keystrokes.

The graph consumes an immutable request snapshot and produces a typed local-search
result carrying the request revision. Search data is fixed and non-sensitive.
There is no shared conversation checkpoint in this example: each query is an
independent invocation. Existing checkpoint/resume regression tests must remain
green, but concurrent checkpoint writers are not a problem this example solves.

### 2. Explicit shared ownership, not an example-local fork

The implementation must expose a documented synchronous supersession operation
for a named invocation scope in one FSM context. The search example uses one
scope, `search`; unrelated scopes must not invalidate each other.

Proposed contract, with exact public names finalized by judgement:

- Explicitly superseding a scope revokes the prior invocation's commit authority
  immediately, even if its work continues. Clearing or closing the application
  revokes authority without launching a replacement.
- Each launch captures its own immutable ownership identity. Current-state name,
  query equality and presence of a boolean guard are not identity checks.
- A running guard belongs to a specific invocation. Cleanup uses compare-and-
  release: an old invocation cannot remove a replacement's guard.
- Add an owner-only success/error commit extension point, distinct from the
  existing run-observation hooks. Validate ownership immediately before calling
  a synchronous commit hook; no `await` may separate the check from the commit.
- Preserve existing success/error hooks as run observations, including stale
  runs. Document that they must not perform current-owner business mutations;
  the library cannot make arbitrary subclass side effects safe automatically.
- Owner-only hooks and ordinary dispatch are suppressed for stale work. Existing
  `pre_dispatch` remains an additional veto, not a grant that restores revoked
  authority. Error-path and success-path rules are symmetrical.
- Observation failures must not grant dispatch authority or skip ownership-safe
  release. Tests must specify propagation without silently swallowing errors.
- The ownership scope is explicit opt-in configuration for this new policy.
  Existing non-superseding integrations retain hook ordering/event selection;
  forcing all integrations to invalidate work on every state transition would
  change their lifetimes without a declared need. No old/new runner duplication.

Use existing typed snapshot/config conventions. The example may invoke the public
supersession operation and override documented hooks; it must not implement its
own graph runner, poke private guard keys, or patch engine transition internals.
Inspect direct `run_and_dispatch` callers before changing its signature.

### 3. Publication is a second authorization boundary

The bridge checks authority immediately before socket send, but a datagram sent
while A was current can still be processed after a queued new-query event.
Therefore every example completion carries its immutable request revision and
the example verifies it against the accepted revision **before publication**.
Incoming result fields must not be projected directly onto authoritative display
or request fields before this check. Keep pending result data separate.

Test both orderings: supersession before send, and an already-sent completion
consumed after supersession. The first belongs to shared dispatch gating; the
second belongs to the example's result-acceptance policy. Do not claim a send-time
predicate solves both, and do not add a new engine transport protocol in this FR.

### 4. Deterministic real-component harness

Automated tests must run:

- Actual `StateMachineEngine` config loading, action discovery and event loop.
- The shared `YamlgraphAsyncAction` and runner, without replacing their execution.
- Actual YAMLGraph loading, compilation and node execution.
- Actual AF_UNIX datagram input and completion delivery, including context-map
  projection. Use a unique short machine name and socket for each test.

A test-controlled asynchronous barrier inside search work signals “started” and
waits for explicit release. It controls completion order, not event interpretation.
Use bounded waits for milestones; do not use elapsed sleeps to manufacture races.
Do not mock `run_and_dispatch`, `run_graph_async`, engine transitions or socket
delivery in integration tests. Smaller unit witnesses may inject dependencies.

An interactive scripted mode offers the same hold/release controls so a human can
see A finish after B without relying on network timing. The CLI and tests use the
same FSM/actions/graph; only their input driver differs. This is asynchronous
correctness coverage, not a latency, throughput or real-provider benchmark.

The example host stops accepting input, revokes authority, cancels/drains its
owned tasks with a bound, and closes the engine/socket while the event loop is
alive. Retain specific task handles via a narrow shared lifecycle surface if
needed; do not enumerate and cancel unrelated loop tasks. Tests must await old
work's terminal path to assert absence of effects, not merely inspect state before
that work has had a chance to finish.

## Acceptance Criteria

- [ ] **AC-01 — RED evidence:** a focused shared-bridge test fails on the inspected
  ownership-blind implementation; record the exact failing assertion and revision.
  Distinguish failure to launch B from stale completion corrupting B; neither may
  be hidden by direct test mutation of guard internals.
- [ ] **AC-02 — real path:** the offline integration harness executes engine,
  shared action, compiled graph and socket delivery. Assert A-start, supersession,
  B-start, A-terminal and B-terminal milestones and actual transition sequence.
- [ ] **AC-03 — old success:** release A successfully while B is pending. A is
  observed once but causes no owner-only commit or ordinary completion dispatch;
  B retains its guard and repeated engine action opportunities create no duplicate B.
- [ ] **AC-04 — old failure:** repeat AC-03 with A raising an exception. The failure
  is observable but cannot replace B's result/error state, release its guard, or
  send a stale ordinary failure. B then completes normally exactly once.
- [ ] **AC-05 — late after completion:** complete B first, then A, for both A
  success and failure. B's published result and terminal ownership remain unchanged.
- [ ] **AC-06 — identity:** repeat identical query text as distinct requests, and
  run three rapid revisions. Only the latest accepted revision may publish;
  ownership in a separate scope/context is unaffected.
- [ ] **AC-07 — queued completion:** send A's completion after the new-query
  datagram is queued but before it is processed. Drain in controlled order and
  prove the consumer rejects A after accepting the new revision, without first
  overwriting authoritative fields. Exercise the real socket receive path.
- [ ] **AC-08 — clear/stop:** clear or stop during pending search; release or drain
  old work and prove no result reappears. After shutdown no host-owned graph task,
  engine timer or test socket remains. Failure during an observation hook cannot
  bypass revocation or ownership-safe release.
- [ ] **AC-09 — existing contract:** existing shared bridge and router tests pass,
  covering no-scope use, launch/snapshot hooks, event precedence, payload forwarding,
  metadata stripping, ordinary error dispatch and interrupt/resume paths.
- [ ] **AC-10 — executable example:** documented offline CLI/scripted demonstration
  shows overlapping invocations and discarded old results using the same real path
  as the test, with no credentials and a nonzero exit on invariant failure.
- [ ] **AC-11 — honest collection:** relabel the router's YAML-only integration
  claims as config tests. Put new automatically run tests under the normal test
  tree, not only under an example directory; preserve requirement-marker checks.
- [ ] **AC-12 — continuous validation:** a Linux CI invocation installs the FSM
  extra and explicitly runs this offline suite without credentials. Missing engine
  dependency is a failure in that invocation, not a passing skip. Document AF_UNIX
  platform limits; do not hide the suite behind an external-service-only marker.
- [ ] **AC-13 — traceability and documentation:** allocate a collision-checked new
  requirement under the appropriate existing contrib capability, update generated
  architecture documentation, tag tests, and add a changelog fragment and diary.
  Document new hook semantics, supersession, shutdown, and publication boundaries.

## Scope and implementation sequence

1. Establish RED at the smallest bridge boundary; inventory existing hook and
   runner callers. Freeze concrete API names/types in judgement before enforcement.
2. Implement only the ownership primitives needed by the example, with unit
   witnesses for comparison, stale success/error, hook failures and scope isolation.
3. Author the minimal graph/example and real-component harness through the
   prescribed graph-authoring route. Validate the ordered scenarios above.
4. Run regression, demonstrate offline operation, wire CI and document the contract.

Keep independent requests throughout. Out of scope: shared-checkpoint concurrency,
graph interrupt redesign, real search or LLM integrations, a browser UI, voice,
provider racing, durable jobs, performance targets, engine embedding/replacement,
package relocation, arbitrary automatic cancellation on state exit, and migration
of external applications. If RED requires substantial new engine machinery or the
generic API cannot be bounded, split investigation from correction rather than
silently expanding this FR.

## Research record and alternatives

Source inspection on 2026-09-10; YAMLGraph revision above, engine 1.0.90 source.
No live demo, test execution or claimed performance result accompanies this filing.

| Evidence / option | Observed detail | Disposition |
|---|---|---|
| Existing router wrapper | Subclasses shared action; only overrides graph base directory | Reuse wiring conventions, not a new action implementation |
| Existing router integration class | Three methods parse YAML/check action types; none starts an engine | Correct its claim; add actual execution coverage |
| Shared runner unit coverage | `test_guard_is_cleared_after_completion` asserts deletion of a single boolean guard after a mocked run | Retain normal completion; add replacement-owner witness |
| Existing hook gate | Success/error hooks precede dispatch predicate; guard removal is unconditional in `finally` | Add explicit authorized-commit semantics and compare-and-release |
| Sequential router alone | Classification finishes before responder launch | Cannot witness overlapping superseded work |
| Controlled async graph work | Required ordering can be established by started/release barriers | Selected: deterministic test of actual async execution, no provider needed |
| Live-provider-only example | Adds credentials and nondeterministic completion; no recorded provider run for this proposal | Optional future demonstration, not correctness gate |
| Support drafting or address correction | Requires conversation-revision or checkpoint policy in addition to independent task ownership | Defer; local search is the smaller first consumer |
| Cancel old task only | Cancellation does not undo already-produced effects or already-sent events | Cancellation assists cleanup; ownership remains the correctness boundary |
| Query text as identity | Two identical submissions have different acceptance order | Reject; use session-scoped request revisions and invocation identities |
| Example-local guards | Would allow the example to pass while shared cleanup remains unchanged | Reject; shared ownership must be the exercised mechanism |

Existing source references:
- [Router action](../examples/fsm-router/actions/yamlgraph_async_action.py)
- [Router configuration](../examples/fsm-router/config/router.yaml)
- [Router tests](../examples/fsm-router/tests/test_yamlgraph_async_action.py)
- [Shared action](../yamlgraph/utils/fsm/action.py)
- [Shared runner](../yamlgraph/utils/fsm/graph_runner.py)
- [Event sender](../yamlgraph/utils/fsm/event_sender.py)
- [Shared bridge tests](../tests/unit/test_fsm_bridge_shared.py)
- [Dependency and test configuration](../pyproject.toml)

At this revision Python is declared `>=3.11,<3.14` and the optional FSM extra
requires `statemachine-engine>=1.0.89`. Use a supported interpreter and record the
exact versions actually tested; do not infer supported execution from an import
in a different environment. Recheck paths if FR-757 lands before enforcement.

## Risks and decisions for judgement

- Resolve the exact scope/identity and host teardown API without creating a
  general task scheduler. The semantics above are required; method names are not
  yet an approved API.
- Review the strongest objection: this is more machinery than a sequential
  router needs. The justification is specifically supersedable interactive work;
  applications without it must not acquire a new lifetime policy accidentally.
- Review all current hook consumers before granting authority to migration rules.
  Merely renaming a mutating hook to “observation” does not make it safe.
- No latency promise follows from deterministic ordering tests. No concurrent
  checkpoint safety follows from independent query invocations.

## Implementation status

Proposal only. Research is the explicit source-grounded record above. No judgement,
code, test result, release, pipeline submission or external adoption is claimed.
FR identifier checked against local files and remote main; no open upstream PRs
were returned at filing. Recheck collision status before committing.
