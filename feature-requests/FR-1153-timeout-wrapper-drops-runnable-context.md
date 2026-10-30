# Feature Request: FR-1153 A node's timeout drops the LangGraph runnable context

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
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
  - "new tests run against the unfixed lines — must fail with the get_config RuntimeError, not another reason"
  - "grep for other pool.submit of a node function in yamlgraph/ — decides whether a third site is in scope"
branches:
  - "a third pool.submit of a node function without copy_context is found → fix it in this change with its own witness"
  - "copy_context breaks an existing timeout test → stop, record, back to judge"
delegations:
  - "judge.sh: 1 run"
waits:
  - "judge"
  - "CI"
  - "operator merge decision"
commands:
  - scripts/judge.sh feature-requests/FR-1153-timeout-wrapper-drops-runnable-context.md
  - pytest tests/unit/test_fr1153_timeout_runnable_context.py -q --no-cov
  - pytest tests/unit/test_map_node_timeout.py -q --no-cov
  - grep -rn "\.submit(" yamlgraph/
```

## Proposed Solution

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
F-1).

## Acceptance Criteria

- [ ] AC-01: a graph compiled from YAML with a `type: python` node and
  `timeout: 2`, whose tool returns `get_config()["configurable"]["sentinel"]`,
  returns `"a"` and `"b"` for two invocations with those sentinels. RED
  against the unfixed line with the `get_config` `RuntimeError` (verbatim
  output recorded in Implementation status).
- [ ] AC-02: the same graph without `timeout:` returns `"a"` and `"b"`
  (control).
- [ ] AC-03: a map node with `timeout: 2` over two items, sub-node a python
  tool returning the sentinel, collects two results equal to the sentinel for
  each of two invocations. RED against the unfixed line with the same
  `RuntimeError` in the `MapFailure` record.
- [ ] AC-04: AC-01 passes with OTel wrapping enabled and disabled (no exporter
  required).
- [ ] AC-05: existing timeout behaviour holds: `tests/unit/test_map_node_timeout.py`
  and every other test referencing `_maybe_wrap_timeout` pass unchanged.
- [ ] AC-06: new tests carry `@pytest.mark.req("REQ-YG-078")`;
  `python scripts/req_coverage.py --strict` passes.
- [ ] AC-07: `changelog/unreleased/fr-1153-timeout-runnable-context.md` with
  `type: fix`, `scope: compile`, `req: REQ-YG-078`;
  `python scripts/check_changelog_req.py` passes.
- [ ] AC-08: RED and GREEN commits are separate; no `--no-verify`.
- [ ] AC-09: a `docs/diary/` reflection with a **Seed:**.

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
