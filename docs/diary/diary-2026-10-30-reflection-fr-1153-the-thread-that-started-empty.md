# Reflection: FR-1153 — the thread that started empty

**Date:** 2026-10-30
**FR:** FR-1153 (GitHub issue #708)

## What happened

An outside reporter showed that adding `timeout:` to a python node broke
`get_config()` inside it. The timeout runs the node on a fresh pool thread,
and pool threads do not inherit contextvars. The fix is one line at each
submit: `pool.submit(copy_context().run, node_fn, state)`.

The report named one site. Before I wrote the FR, a grep for `ThreadPoolExecutor`
found a second one with the same line, in `map_compiler._execute_node_fn`,
and a real map-node run with `timeout: 2` failed 0/2 with the same
`RuntimeError`. If the fix had followed the report, map nodes would still be
broken.

## The trap

`partial_remediation`, arriving through a well-written external report: the
better the reproduction, the more it reads like the full scope. The reporter
had read the code and described the defect correctly, but only for the path
they had hit.

A second, smaller trap in the RED step: the map tests failed first with
`MapCompletenessError: accepted 0/2`. That is a correct failure, but it does
not say why. Setting `min_success: 0.0` in the test graph surfaced the
`MapFailure(error_type='RuntimeError', message='Called get_config outside of a
runnable context')` record, so the RED now states its reason.

## Heuristic

When a report names a broken line, grep for the line's shape, not its
location. Any defect at a thread, process or event-loop boundary has a sibling
wherever the same boundary is crossed again.

Also, a third time on this repo: running the full suite through
`.venv/bin/python` without activating the venv lets `python3` subprocesses
fall through to homebrew Python and fail on `import yaml`. Activate the venv
before reading any full-suite red.

## Seed:

Every pool, `asyncio.to_thread` or `run_in_executor` in `yamlgraph/` is a place
where contextvars, and with them LangChain callbacks and LangSmith parent runs,
can silently drop. Could one test compile a graph that uses every node type
with `timeout:` and assert that each LLM call's trace has a parent? That would
turn the "inferred, not probed" tracing claim in FR-1153 into a measured one.
