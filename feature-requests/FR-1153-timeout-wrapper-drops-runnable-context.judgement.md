# Judgement: FR-1153 A node's timeout drops the LangGraph runnable context

**Prior art:** [FR-1153-timeout-wrapper-drops-runnable-context.md](FR-1153-timeout-wrapper-drops-runnable-context.md) — the FR this judgement rules on, not precedent; dismissed. FR-925 (lane delivery agent context, SUPERSEDED) and FR-927 (retire lane guard hooks) match only on the nouns "timeout"/"context"; neither touches node timeout wrapping or runnable config — dismissed. The FR's own Prior art line dispositions FR-1058 and FR-069. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `scripts/judge.sh` (copilot, gpt-5.6-sol), 2026-10-30, round 1.)

**Verdict:** APPROVED WITH REVISIONS — the root cause and two-site repair are minimal and architecture-aligned, but authority activates only after the FR freezes those sites, adds concurrent isolation witnesses, makes the OTEL case exact, and updates REQ-YG-078 to state the preserved contract.

**Reviewed against:** `feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `feature-requests/FR-1058-subgraph-runnable-config-propagation.md`; `feature-requests/FR-1058-subgraph-runnable-config-propagation.judgement.md`; `feature-requests/069-map-node-timeout.md`; `yamlgraph/node_timeout.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/compile/node_otel.py`; `tests/unit/conftest.py`; `tests/unit/test_map_node_timeout.py`; `tests/unit/test_otel_observability.py`; `ARCHITECTURE.md`. GitHub issues #708, #474, and #438, PR #673, and the uncommitted `tmp/issue708/` scratch files were not consumed; their claims were assessed only as represented in the committed FR.

## What is sound

The defect is real in the committed implementation. Both timeout paths submit the node callable directly to a fresh executor (`yamlgraph/node_timeout.py:41-45`; `yamlgraph/compile/map_compiler.py:102-121`), while the FR correctly identifies that the runnable config is read through thread-local context rather than a function argument (`feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md:24-30,38-58`). The proposed `copy_context().run` boundary fix is the smallest change that preserves the caller's context without changing node signatures or reopening FR-1058's rejected explicit-config-forwarding path (`feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md:98-113`; `feature-requests/FR-1058-subgraph-runnable-config-propagation.md:149-184`).

The two affected surfaces are complete and independently testable. Repository search finds only the non-map submission in `_maybe_wrap_timeout()` and the map submission in `_execute_node_fn()`, matching the FR's inventory (`feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md:40-45`). The wrapper order also makes the OTEL composition case legitimate rather than adjacent scope: compiled Python nodes apply timeout first and OTEL second (`yamlgraph/compile/node_compiler.py:133-142`), and the outer OTEL wrapper preserves LangGraph's injected `RunnableConfig` before calling the inner timeout wrapper (`yamlgraph/compile/node_otel.py:37-50`).

The research record is substantive enough for this bug fix. It names the first consumer, records observed results for both execution paths, distinguishes the selected thread-boundary repair from explicit config forwarding, signals, and documentation-only treatment, dispositions FR-1058 and FR-069, and answers `is_this_a_graph` (`feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md:7-22,47-66,140-149`). The strategic classification is **Framework primitive**: the correction applies to the shared per-node timeout primitive across map branches and multiple compiled node types, not to a contrib example or documentation pattern.

Scope, feasibility, and single responsibility are otherwise sound. The change repairs context preservation at the exact platform boundary while retaining timeout classification, error shapes, shutdown policy, and the state-only callable contract (`feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md:109-113`). Existing REQ-YG-078 already governs both executor paths and their timeout behavior (`ARCHITECTURE.md:1521-1529`).

## Required revisions

### R-1: Freeze the implementation to the two proven submission sites

Replace the open-ended planned branch that authorizes any newly found third `pool.submit` site (`feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md:81-84`) with the completed inventory result: the governed production changes are exactly `yamlgraph/node_timeout.py:44` and `yamlgraph/compile/map_compiler.py:119`. State that another context-losing execution boundary, if later discovered, requires a separate FR unless it prevents these two repairs from functioning.

### R-2: Add overlapping concurrent-invocation witnesses for both paths

The Ideal Result promises that concurrent invocations never observe each other's context (`feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md:68-72`), but AC-01 and AC-03 invoke sentinels sequentially (`:117-127`). Add a mechanically specified concurrency test for each governed path: invoke the same compiled graph concurrently with sentinels `a` and `b`, use a barrier inside the Python tool so both timed workers overlap, and assert that each result contains only its own sentinel. The test must fail if the context is copied at compile time, shared between invocations, or copied inside the worker after the caller context has already been lost.

### R-3: Define the OTEL witness using the repository's actual fixture

Replace “OTel wrapping enabled and disabled (no exporter required)” (`feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md:128-129`) with two exact states: OTEL disabled with `YAMLGRAPH_OTEL_EXPORT` unset, and OTEL enabled through the shared `in_memory_exporter` fixture in `tests/unit/conftest.py`. In the enabled case, assert both the correct sentinel result and one completed `yamlgraph.node.execute` span for the timed Python node. Mark this composition witness with both `REQ-YG-078` and `REQ-YG-570`. No production change to `yamlgraph/compile/node_otel.py` is authorized.

### R-4: Make the architecture contract name context preservation

Amend CAP-96 / REQ-YG-078 in `ARCHITECTURE.md` so the requirement states that applying a timeout preserves the caller's runnable context for the node execution. Add `yamlgraph/node_timeout.py` and the new FR-1153 test module to the requirement's key modules. This makes the new tests trace the behavior they assert rather than only the existence and error classification of timeout wrapping.

### R-5: Pin the RED and regression commands

State that the RED commit must contain all four behavioral failures: non-map context loss, map context loss, non-map concurrent isolation, and map concurrent isolation. The first two must fail with the represented `get_config()` runtime error or map failure, while the concurrency witnesses must fail because the implementation does not preserve an invocation-local context, not because of fixture, import, or synchronization errors.

Replace “every other test referencing `_maybe_wrap_timeout`” with an exact regression command covering the new test module, `tests/unit/test_map_node_timeout.py`, `tests/unit/test_router_race.py`, and `tests/unit/test_race_node.py`. Retain `python scripts/req_coverage.py --strict` and `python scripts/check_changelog_req.py` as separate exact gates.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/node_timeout.py`: copy the caller context per timed non-map invocation |
| D-2 | `yamlgraph/compile/map_compiler.py`: copy the caller context per timed map sub-node invocation |
| D-3 | `tests/unit/test_fr1153_timeout_runnable_context.py`: YAML-compiled controls, timed failures/cures, concurrent isolation, and OTEL composition witnesses |
| D-4 | `ARCHITECTURE.md`: CAP-96 / REQ-YG-078 context-preservation contract and key-module traceability |
| D-5 | `changelog/unreleased/fr-1153-timeout-runnable-context.md`: `type: fix`, `scope: compile`, `req: REQ-YG-078` |
| D-6 | FR-1153 implementation-status evidence and one `docs/diary/` reflection containing a **Seed:** |

Not authorized: changes to timeout values, cancellation semantics, executor lifetime, `shutdown(wait=False, cancel_futures=True)`, timeout exception handling or returned error shapes; changes to callable signatures; explicit `RunnableConfig` forwarding; changes to `yamlgraph/compile/node_otel.py`; guarantees or production changes for LangSmith callback parenting; graph or prompt artifact changes; dependency changes; or repairs to any execution boundary other than the two frozen submission sites.

## Revised acceptance criteria

- [ ] AC-01: R-1 through R-5 are folded into FR-1153 before enforcement begins.
- [ ] AC-02: A graph compiled from YAML with a `type: python` node and `timeout: 2`, whose tool returns `get_config()["configurable"]["sentinel"]`, returns `a` and `b` for invocations configured with those sentinels; the same graph without `timeout` is the passing control.
- [ ] AC-03: A YAML-compiled map node with `timeout: 2`, two items, and a Python sub-node that returns the runnable-config sentinel collects two results carrying `a` for an `a` invocation and two carrying `b` for a `b` invocation; the RED failure records `RuntimeError: Called get_config outside of a runnable context`.
- [ ] AC-04: For both the non-map and map paths, two barrier-overlapped invocations of the same compiled graph with sentinels `a` and `b` each return only their own sentinel, proving per-invocation context copying and isolation.
- [ ] AC-05: The timed non-map YAML witness passes with `YAMLGRAPH_OTEL_EXPORT` unset and with the shared `in_memory_exporter` fixture; the enabled case returns the correct sentinel and records one completed `yamlgraph.node.execute` span for that node. The witness carries both `REQ-YG-078` and `REQ-YG-570`.
- [ ] AC-06: The production diff changes only the two frozen execution boundaries to submit `copy_context().run` with the original `node_fn` and `state`; callable signatures, timeout exception branches, error shapes, and executor shutdown calls remain unchanged.
- [ ] AC-07: CAP-96 / REQ-YG-078 states that timeout wrapping preserves the caller's runnable context and lists `yamlgraph/node_timeout.py`, `yamlgraph/compile/map_compiler.py`, `tests/unit/test_map_node_timeout.py`, and `tests/unit/test_fr1153_timeout_runnable_context.py` as key modules.
- [ ] AC-08: `pytest tests/unit/test_fr1153_timeout_runnable_context.py tests/unit/test_map_node_timeout.py tests/unit/test_router_race.py tests/unit/test_race_node.py -q --no-cov` passes.
- [ ] AC-09: Every new test carries `@pytest.mark.req("REQ-YG-078")`, the OTEL composition witness additionally carries `@pytest.mark.req("REQ-YG-570")`, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: `changelog/unreleased/fr-1153-timeout-runnable-context.md` has `type: fix`, `scope: compile`, and `req: REQ-YG-078`; `python scripts/check_changelog_req.py` passes.
- [ ] AC-11: A RED commit containing the four failures in R-5 precedes the GREEN implementation commit; FR-1153's Implementation Status records the RED outputs and final commands; no verification bypass is used.
- [ ] AC-12: A `docs/diary/` reflection records the thread-boundary/context-boundary lesson and contains a **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the committed FR before implementation authority activates. | GATE |
| C-2 | Copy context independently inside every invocation at each frozen caller boundary; do not capture one `Context` at compile/wrapper construction time or reuse a `Context` across invocations. | GATE |
| C-3 | Preserve timeout exception classification, result/error shapes, executor shutdown policy, and state-only callable signatures exactly. | GATE |
| C-4 | Do not replace context propagation with explicit config forwarding; FR-1058's distinction remains binding. | GATE |
| C-5 | Do not modify OTEL production code or claim LangSmith callback-parent correctness; OTEL is only a wrapper-composition witness under this authority. | GATE |
| C-6 | Do not modify graph/prompt artifacts, dependencies, or any third execution boundary. | GATE |

Authority granted: after the required revisions are folded into FR-1153, the enforcer may preserve the caller's runnable context across the two existing timeout executor boundaries and add only the frozen tests, architecture wording, changelog, implementation record, and diary evidence above.
