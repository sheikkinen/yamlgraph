# Diary 2026-09-26 — The mock that had a width

**Context:** FR-1085 enforcement: every managed run boundary now resolves
one `max_concurrency` (caller → graph → `YAMLGRAPH_MAX_CONCURRENCY` → 8).

The resolver took about forty lines. The first full-suite run after it
failed twenty-five tests. Seventeen of them passed a bare `MagicMock` as
the graph config. Before FR-1085, `_build_run_config` read
`graph_config.max_concurrency` from that mock, got a `MagicMock`, and put
it into the run config as the width. No test noticed, because
`app.invoke` was also a mock and accepted any config. The resolver
validates the graph level and raised on the mock. The mocks had been
feeding a non-integer width into LangGraph all along; the new check made
it visible.

This is the same pattern the FR-1084 diary recorded a few hours earlier,
in a different subsystem: a boundary check breaks mocked tests because
the mocks carried the defect. Two recurrences in one day, on two
unrelated FRs, meet the Scripture's graduation bar ("heuristic appears
twice → create FR").

Two smaller choices from this enforcement:

- The new resolver first went into a new module. The FR-335 module-map
  line budget then failed by one line. Its history shows the budget is
  raised by one or two lines per new module. I moved the resolver into
  `validators.py` beside FR-984's `validate_max_concurrency` instead,
  leaving the gate alone. That was cheaper than editing an enforcement
  test in the same session that tripped it, and the code fits there
  anyway.
- The 2-CPU async peaks were 6, not 8. The resolver was not the cause. The
  fixture's worker is a sync function, which LangGraph runs on asyncio's
  default executor, sized `min(32, cpus + 4)`. The FR promised a cap, and
  the peak table records the executor ceiling rather than calling 6 a
  resolver result.

## Heuristic and seed

**Heuristic:** a bare `MagicMock` standing in for a typed config answers
every attribute read with a truthy object. Any new code that reads a new
field from that config inherits a fake value that passes type-blind code
and fails the first validator. When a validator breaks many mocked tests
at once, grep the failures for `MagicMock name='...<field>'`: that is a
list of every test that was already running with a garbage value.

**Seed:** should tests build graph-config doubles with
`MagicMock(spec=GraphConfig)`, or from one conftest factory with real
defaults, so that reading an undeclared field fails at test time instead
of silently returning a mock? Filing that as an FR would also be the
graduation vehicle for "mocks encoded the defect" (two recurrences:
FR-1084, FR-1085).
