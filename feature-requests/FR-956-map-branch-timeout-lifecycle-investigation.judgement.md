# Judgement: FR-956 Map Branch Timeout Lifecycle — condemn-or-absolve witness and mechanism verdict

**Verdict:** APPROVED WITH REVISIONS — the investigation and narrow attribution fix are sound, but authority activates only after the FR folds R-1 through R-6 below and this draft is human-reviewed.

**Reviewed against:** `feature-requests/FR-956-map-branch-timeout-lifecycle-investigation.md`; `feature-requests/research-briefs/fr956-map-timeout-lifecycle-brief.md`; `feature-requests/TEMPLATE.md`; `feature-requests/069-map-node-timeout.md`; `feature-requests/FR-936-map-node-hardening.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `feature-requests/FR-706-race-timeout-loop-liveness.md`; `feature-requests/FR-708-llm-client-request-timeout.md`; `feature-requests/FR-271-async-race-node-cancellable-2.md`; `feature-requests/FR-720-close-trace-spans-on-loser-cancel.md`; `feature-requests/FR-154-architecture-capability-count-guard.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/node_timeout.py`; `yamlgraph/models/schemas.py`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/route_log.py`; `yamlgraph/routing.py`; `examples/demos/research-route/nodes/research_tools.py`; `tests/unit/test_map_node_timeout.py`; `capabilities/CAP-11-subgraph-map.yaml`; `reference/graph-yaml.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect is real and already admitted by both implementation and precedent. `_execute_node_fn` returns after `Future.result(timeout)` while `shutdown(wait=False, cancel_futures=True)` cannot terminate its running callable (`yamlgraph/compile/map_compiler.py:93-113`); FR-069 records the same limitation (`feature-requests/069-map-node-timeout.md`, Known Limitations). Existing tests assert only the timeout-shaped result, not resource lifecycle (`tests/unit/test_map_node_timeout.py:90-156`). Investigation before mechanism is therefore the correct order.

The FR is substantially scoped as the D-3 child required by FR-936. It excludes executor, non-map timeout, race, provider, overflow, payload, and retry changes (`feature-requests/FR-956-map-branch-timeout-lifecycle-investigation.md:184-186`), while retaining the inherited termination/reclamation and post-timeout liveness fence (`feature-requests/FR-936-map-node-hardening.judgement.md:88-93,165-166,185`). The single authorized production behavior—real map/index attribution—is separable from the later resource-control mechanism (`feature-requests/FR-956-map-branch-timeout-lifecycle-investigation.md:134-139`).

The prospective research gate is not defeated merely because the route exposed its legacy-filename checker defect: the repository template expressly permits an equivalent committed in-body alternatives record (`feature-requests/TEMPLATE.md:17-20`), and this FR provides six mechanism classes, precedent dispositions, and an explicit `is_this_a_graph` answer (`feature-requests/FR-956-map-branch-timeout-lifecycle-investigation.md:141-154`). R-1 below is still required because the failed route persisted no persona output and the table does not yet preserve a concrete dissent as required by the local research-substance rule.

Against the eight criteria:

| Criterion | Finding |
|---|---|
| Scope | Minimal after R-4 removes the unrelated route-log schema expansion; lifecycle investigation, attribution, and the evidence handoff remain one timeout-ownership concern. |
| Consistency | The inherited termination fence is correctly cited at FR lines 27-30, but AC-08 and the human options contradict it by permitting closure with known unbounded non-LLM leaks (`feature-requests/FR-956-map-branch-timeout-lifecycle-investigation.md:145-147,179-180,212-217`). R-2 resolves this. |
| Measurability | Reclamation, liveness, late return, attribution, and a lifecycle table can be asserted or inspected. The mocked-provider lifetime claim and unpinned timing thresholds are not honest mechanical gates as written; R-3 and R-5 resolve them. |
| Feasibility | The one-shot executor and typed `PipelineError` already expose the required seams. `PipelineError.details` can carry branch metadata (`yamlgraph/models/schemas.py:31-47`), and the map name can be passed to `wrap_for_reducer` at its existing construction site (`yamlgraph/compile/map_compiler.py:329-331`). |
| Architecture alignment | The investigation extends CAP-11's existing map/reducer surface (`capabilities/CAP-11-subgraph-map.yaml:1-16`) and keeps true termination in a separately judged implementation FR. |
| Single responsibility | Lifecycle evidence, truthful attribution, and mechanism selection are one causal chain. Implementing the selected termination mechanism remains separately fenced. |
| Strategic classification | Framework-primitive correction: the existing map abstraction serves multiple long-lived/scheduled consumers, and no current abstraction owns timed-out synchronous branch work (`feature-requests/FR-956-map-branch-timeout-lifecycle-investigation.md:8-12,46-51`). |
| Testability | Direct tests are derivable once condemned outcomes are suite-safe, timing constants are fixed, and each sub-node row names its witness. R-5 and R-6 pin those contracts. |

## Required revisions

### R-1: Preserve substantive research disagreement

Add a committed subsection to the in-body research record that states the strongest evidence-backed dissent against the recommended mechanism class, identifies which class or composition that dissent supports, and records why the investigation can confirm or reject it. Preserve the disagreement rather than replacing it with the final verdict. Keep the six-class table and `is_this_a_graph` answer. Do not claim that the failed five-persona run supplied evidence, because no persona output was persisted.

### R-2: Remove the noncompliant absolution path

Delete AC-08's permission to mark this FR ABSOLVED merely because class A bounds LLM requests, and delete the human option to "accept bounded leak + attribution and close." Class A explicitly leaves Python and agent work unbounded, while class B explicitly leaves non-cooperating work running (`feature-requests/FR-956-map-branch-timeout-lifecycle-investigation.md:145-146`); neither alone satisfies FR-936's termination-or-isolation and reclamation gate.

Replace AC-07/AC-08 with this outcome contract: the investigation may be ABSOLVED only if executable witnesses prove every currently supported map sub-node class reclaims timed-out work and preserves later-branch liveness. Otherwise it must file an implementation FR selecting a class A-C composition that terminates work at a client boundary or isolates it in a terminable unit for every class shown to leak. The human may choose among compliant mechanisms after reading the evidence; accepting a known unbounded leak is not an available option.

### R-3: Make the LLM evidence claim honest

Replace the current AC-05 claim that a mocked client measures the FR-708 provider bound. FR-708 explicitly rules that a mocked hang cannot validate SDK timeout behavior (`feature-requests/FR-708-llm-client-request-timeout.md:86-88,102-104`). Split the evidence:

1. Cite or rerun the existing constructor-level witness that the relevant client receives a finite wrapper-correct request timeout and bounded retries.
2. If a deterministic fake is used, label its result a model of map-thread lifetime under a callable that honors a supplied deadline, not a measurement of provider SDK behavior.
3. Do not state a `3 x request_timeout` wall-clock bound unless an executable witness includes retry/backoff behavior and proves that exact bound for the named wrapper. Record configured per-attempt timeout and retry count separately from observed wall time.

Update AC-11 so `reference/graph-yaml.md` records only bounds the accepted evidence actually establishes. Any real-provider probe remains non-gating and must not be represented by a mock.

### R-4: Keep attribution in-band and inside the authorized seam

Remove the route-decision-log requirement from Proposed Solution and AC-04. The map timeout path currently has no route-log emission seam; `emit_route` emits an `"event": "route"` record and is called from routing decisions, not branch execution (`yamlgraph/utils/route_log.py:213-223`; `yamlgraph/routing.py:14-113`). Adding a new timeout event/schema is a separate observability contract and exceeds the claimed one production change.

Pin the authorized state output instead:

- pass the authored map node name into `wrap_for_reducer`;
- set `PipelineError.node` to `"<map_node>[<index>]"`;
- put numeric `map_index` and `elapsed_seconds` in `PipelineError.details`;
- retain the reducer error row's `_map_index`, add numeric `_elapsed_seconds`, and keep `_error` human-readable with the elapsed duration;
- assert the `ErrorType.TIMEOUT_ERROR` and `on_error: skip` survivor behavior remain unchanged.

### R-5: Make condemned witnesses suite-safe and timing-safe

Adopt FR-706's proven condemn-or-absolve contract (`feature-requests/FR-706-race-timeout-loop-liveness.md:85-103,121-125`):

- every hanging fake must terminate in bounded time without relying on the behavior under test;
- record the observed verdict in the FR;
- if the termination assertion is CONDEMNED, commit it as `xfail(strict=True)` naming the follow-up implementation FR, so the suite remains committable and the eventual fix produces XPASS until the marker is removed;
- keep eventual-return and later-healthy-branch witnesses as ordinary passing regression tests;
- use witness-owned thread identities/events rather than only global thread population;
- pin constants with order-of-magnitude separation between map timeout, healthy-branch deadline, and fake hang duration. Replace `timeout x 2` with an explicit absolute deadline suitable for CI while retaining the invariant that it expires well before the hanging fake naturally returns;
- retain `k >= 8` and record `k`, timeout, hang duration, deadline, baseline, peak, and reclamation time in the FR.

### R-6: Pin per-sub-node evidence and traceability

For each supported map sub-node class—`llm`, `python`, `tool_call`, `agent`, and `subgraph`—the lifecycle table must name an executable witness or cite a shared-wrapper witness and justify why no class-specific boundary changes the conclusion. Do not infer an agent's total lifetime from a single LLM request timeout; agents and tools may perform multiple calls or non-LLM work. Define disposal as executor shutdown invocation and reclamation as termination of the witness-owned running work plus release of its execution capacity.

Broaden the new CAP-11 requirement from "branch timeout attribution" to the exact contract tested: timed-out map branches are attributed by authored node/index, their lifecycle is observable, and later healthy branches retain fixed-deadline liveness. Tag each new test with that requirement or an existing CAP-11 requirement whose text actually matches the assertion; do not attach an attribution-only requirement to unrelated reclamation tests.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-956-map-branch-timeout-lifecycle-investigation.md` revisions, observed verdict, lifecycle table, and mechanism disposition |
| D-2 | `tests/unit/test_fr956_map_timeout_lifecycle.py` bounded lifecycle, liveness, late-return, and attribution witnesses |
| D-3 | `yamlgraph/compile/map_compiler.py` only for map-name/index/elapsed timeout attribution; no executor or cancellation change |
| D-4 | One minimum necessary requirement update in `capabilities/CAP-11-subgraph-map.yaml` |
| D-5 | Focused `reference/graph-yaml.md` limitation update, attribution fix changelog fragment, and one diary reflection |
| D-6 | A separately judged implementation FR if any supported sub-node class remains unbounded |

Not authorized: changing `_execute_node_fn` executor lifecycle; changing `yamlgraph/node_timeout.py`; adding or changing route-log events; changing provider constructors, request timeouts, retries, race behavior, map overflow, branch payload projection, native retry, async node contracts, graph scheduling, durability, checkpointing, or process isolation. The selected termination mechanism itself is not authorized by FR-956.

## Revised acceptance criteria

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

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into the FR before enforcement begins. | GATE |
| C-2 | Do not close or absolve the investigation while any supported map sub-node class is known to leave unbounded running work. | GATE |
| C-3 | Do not claim that a deterministic fake proves provider SDK timeout or retry wall-clock behavior. | GATE |
| C-4 | Do not accept a thread-count ceiling without witness-owned reclamation and fixed-deadline later-branch liveness. | GATE |
| C-5 | Do not add a route-log event or change executor/cancellation behavior under FR-956. | GATE |
| C-6 | Do not implement the selected termination mechanism until its follow-up FR is independently researched, judged, and approved. | GATE |
| C-7 | Treat this draft as advisory until human-reviewed. | GATE |

Authority granted: after R-1 through R-6 are folded and this judgement is human-reviewed, enforcement may add the bounded witness suite, the narrow in-band attribution fix, the matching CAP-11 requirement, and the focused records listed in D-1 through D-5; no termination mechanism is yet authorized.
