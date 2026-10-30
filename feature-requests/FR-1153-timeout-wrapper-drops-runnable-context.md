# Feature Request: FR-1153 A node's timeout drops the LangGraph runnable context

**Priority:** HIGH
**Type:** Bug
**Status:** Approved with revisions (R-1..R-5 folded), ready for enforcement
**Judgement:** [FR-1153-timeout-wrapper-drops-runnable-context.judgement.md](FR-1153-timeout-wrapper-drops-runnable-context.judgement.md)
**Requested:** 2026-10-30
**First consumer / first event:** the reporter of GitHub issue
[#708](https://github.com/sheikkinen/yamlgraph/issues/708) (@sergesha), whose
Python tool reads `get_config()` and fails the moment `timeout:` is added to
its node; reproduced on `main` 2026-10-30.
**Research:** in-body Alternatives Considered table (FR-889 style); no
`research.sh` run. The defect has an executed reproduction at both sites and
an executed cure at the first.
**Prior art:**
[FR-1058-subgraph-runnable-config-propagation.md](FR-1058-subgraph-runnable-config-propagation.md)
fixed config propagation for subgraphs (issue #474) and explicitly cut the
timeout wrapper (its F-1: "no reachable caller" for *explicit config
forwarding*). This FR is distinct: the reachable path is a state-only tool
calling `get_config()`, which reads a contextvar, not an argument. FR-1058's
F-1 still holds for argument forwarding, so this FR does not add it.
FR-069 introduced the timeout wrapper (CAP-96, REQ-YG-078). Issue #438
(timeout cancellation) is out of scope. No rejected FR covers this territory.

## Summary

A node with `timeout:` runs on a fresh `ThreadPoolExecutor` thread. Python
contextvars are not inherited by pool threads, and LangGraph keeps the
runnable config in a contextvar. Inside a timed node, `get_config()` raises
`RuntimeError: Called get_config outside of a runnable context`. Removing
`timeout:` makes the same code work.

## Value Statement

For graph authors who bound a step with `timeout:` and need per-run settings
(`configurable`) inside it, who today must choose between the time limit and
the settings.

## Problem

Two sites submit the node function to a pool without the caller's context:

- `yamlgraph/node_timeout.py` `_maybe_wrap_timeout` → `pool.submit(node_fn, state)`
  (tool, python, agent, tool_call, and llm/router nodes without `candidates`).
- `yamlgraph/compile/map_compiler.py` `_execute_node_fn` →
  `pool.submit(node_fn, state)` (map sub-nodes with `timeout:`).

Reproduction on `main` (2026-10-30, scratch files in the main checkout's
`tmp/issue708/`): a python tool `observe` returning
`get_config()["configurable"]["sentinel"]`, invoked twice with sentinels `a`
and `b`:

| Case | Result |
|---|---|
| python node, no `timeout` | `a`, `b` |
| python node, `timeout: 2` | `RuntimeError: Called get_config outside of a runnable context` (both) |
| python node, `timeout: 2`, `submit` patched in-process to `copy_context().run` | `a`, `b` |
| map node over `[1, 2]`, no `timeout` | `[{'_map_index': 0, 'value': 'a'}, {'_map_index': 1, 'value': 'a'}]`; then `b`, `b` |
| map node, `timeout: 2` | `MapCompletenessError … succeeded=0 … failed=2`; failure record: `MapFailure(error_type='RuntimeError', message='Called get_config outside of a runnable context', node='_map_fan_sub')` |

Knowledge Graph boundary: `state` / `platform` — the runnable context enters
the node through a contextvar, and the thread boundary drops it.

Inferred, not probed: LangChain callbacks (LangSmith parent run) travel in the
same contextvar, so LLM calls inside a timed node likely appear as
disconnected root traces. Not an acceptance criterion here; recorded so the
enforcer can note what the fix changes.

## Ideal Result

Adding `timeout:` to any node changes only how long the node may run. Code
inside the node sees the same runnable context with or without it, and
concurrent invocations never see each other's context.

## Planned Operations

```yaml
probes:
  - "main-checkout tmp/issue708 python-node and map-node reproductions (done, table above)"
  - "in-process copy_context().run patch of ThreadPoolExecutor.submit, python node (done: a, b)"
  - "new tests run against the unfixed lines — the four RED witnesses (R-5) must fail for the stated reason, not a fixture/import/barrier error"
branches:
  - "another context-losing execution boundary is discovered → separate FR, unless it prevents these two repairs from functioning (R-1)"
  - "copy_context breaks an existing timeout test → stop, record, back to judge"
delegations:
  - "judge.sh: 1 run"
waits:
  - "judge"
  - "CI"
  - "operator merge decision"
commands:
  - scripts/judge.sh feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md
  - pytest tests/unit/test_fr1153_timeout_runnable_context.py tests/unit/test_map_node_timeout.py tests/unit/test_router_race.py tests/unit/test_race_node.py -q --no-cov
  - python scripts/req_coverage.py --strict
  - python scripts/check_changelog_req.py
```

## Proposed Solution

Scope is frozen to exactly two production lines (R-1):
`yamlgraph/node_timeout.py:44` and `yamlgraph/compile/map_compiler.py:119`.
At both sites, copy the caller's context per invocation and run the node
function inside it:

```python
from contextvars import copy_context

return pool.submit(copy_context().run, node_fn, state).result(timeout=timeout)
```

Constraints: the context is copied inside the wrapper call, never at compile
time; the `except concurrent.futures.TimeoutError` branches, the returned
error shapes, and `shutdown(wait=False, cancel_futures=True)` are unchanged;
no change to `timed_fn`'s signature; no explicit config forwarding (FR-1058
F-1); no change to `yamlgraph/compile/node_otel.py`; no claim about LangSmith
callback parenting.

Architecture (R-4): CAP-96 / REQ-YG-078 in `ARCHITECTURE.md` gains the clause
"timeout wrapping preserves the caller's runnable context for the node
execution" and lists `yamlgraph/node_timeout.py` and
`tests/unit/test_fr1153_timeout_runnable_context.py` as key modules.

## Acceptance Criteria

Revised by judgement ([FR-1153-timeout-wrapper-drops-runnable-context.judgement.md](FR-1153-timeout-wrapper-drops-runnable-context.judgement.md)):

- [x] AC-01: R-1 through R-5 are folded into FR-1153 before enforcement begins.
- [ ] AC-02: A graph compiled from YAML with a `type: python` node and `timeout: 2`, whose tool returns `get_config()["configurable"]["sentinel"]`, returns `a` and `b` for invocations configured with those sentinels; the same graph without `timeout` is the passing control.
- [ ] AC-03: A YAML-compiled map node with `timeout: 2`, two items, and a Python sub-node that returns the runnable-config sentinel collects two results carrying `a` for an `a` invocation and two carrying `b` for a `b` invocation; the RED failure records `RuntimeError: Called get_config outside of a runnable context`.
- [ ] AC-04: For both the non-map and map paths, two barrier-overlapped invocations of the same compiled graph with sentinels `a` and `b` each return only their own sentinel, proving per-invocation context copying and isolation (R-2).
- [ ] AC-05: The timed non-map YAML witness passes with `YAMLGRAPH_OTEL_EXPORT` unset and with the shared `in_memory_exporter` fixture (`tests/unit/conftest.py`); the enabled case returns the correct sentinel and records one completed `yamlgraph.node.execute` span for that node. The witness carries both `REQ-YG-078` and `REQ-YG-570` (R-3).
- [ ] AC-06: The production diff changes only the two frozen execution boundaries to submit `copy_context().run` with the original `node_fn` and `state`; callable signatures, timeout exception branches, error shapes, and executor shutdown calls remain unchanged.
- [ ] AC-07: CAP-96 / REQ-YG-078 states that timeout wrapping preserves the caller's runnable context and lists `yamlgraph/node_timeout.py`, `yamlgraph/compile/map_compiler.py`, `tests/unit/test_map_node_timeout.py`, and `tests/unit/test_fr1153_timeout_runnable_context.py` as key modules (R-4).
- [ ] AC-08: `pytest tests/unit/test_fr1153_timeout_runnable_context.py tests/unit/test_map_node_timeout.py tests/unit/test_router_race.py tests/unit/test_race_node.py -q --no-cov` passes (R-5).
- [ ] AC-09: Every new test carries `@pytest.mark.req("REQ-YG-078")`, the OTEL composition witness additionally carries `@pytest.mark.req("REQ-YG-570")`, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: `changelog/unreleased/fr-1153-timeout-runnable-context.md` has `type: fix`, `scope: compile`, and `req: REQ-YG-078`; `python scripts/check_changelog_req.py` passes.
- [ ] AC-11: A RED commit containing the four failures (non-map context loss, map context loss, non-map concurrent isolation, map concurrent isolation — R-5) precedes the GREEN implementation commit; Implementation Status records the RED outputs and final commands; no verification bypass is used.
- [ ] AC-12: A `docs/diary/` reflection records the thread-boundary/context-boundary lesson and contains a **Seed:**.

## Alternatives Considered

**is_this_a_graph:** no — a one-line threading fix at two call sites.

| # | Alternative | Disposition |
|---|---|---|
| A | **`copy_context().run` at each `submit`** (chosen) | Executed in-process: python node returns `a`, `b` with `timeout: 2`. Smallest change at the thread boundary. |
| B | Forward `config` explicitly through `timed_fn(state, config)` (issue #474's earlier patch) | Rejected — the #708 reporter records it does not fix the YAML reproduction (a state-only tool reads the contextvar); FR-1058 F-1 found no reachable config-aware caller. |
| C | Enforce timeout without a thread (`signal.alarm`) | Rejected — main-thread only, POSIX only; LangGraph runs nodes on its own pool threads. |
| D | Document "do not combine `timeout` with `get_config`" | Rejected — a documented trap is still a trap; the fix is one line. |

## Related

- GitHub issue #708; #474 / PR #673 (FR-1058); #438 (timeout cancellation).
- `yamlgraph/node_timeout.py`, `yamlgraph/compile/map_compiler.py`,
  `yamlgraph/compile/node_otel.py`.
