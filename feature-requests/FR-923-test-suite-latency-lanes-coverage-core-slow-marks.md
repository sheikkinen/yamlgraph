# Feature Request: Test-Suite Latency — Coverage Core, Lane Split, Slow-Mark Hygiene

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-30
**First consumer / first event:** the CI `test` job on the next PR, and any developer running `pytest tests/` locally — first event is the next full-suite run after merge.
**Research:** in-body measurement record and dispositioned alternatives table (four clocked configurations, main @ ca44832b, 2026-08-30)
**Prior art:** FR-275/CAP-126 (test speed optimization) established the slow-mark tier and fast-loop convention — this FR extends that arc with lane split and coverage core, and re-tiers FR-275's own meta-tests; FR-714 raised the coverage gate this FR preserves. Hook hits dispositioned: FR-902 (session worktree lifecycle — lexical overlap on "lanes", different domain: git lanes, not CI lanes); FR-569 and FR-519 (dm-v2/v3 prose pipeline — lexical overlap only, no test-infra scope).

## Summary

The default full suite (`pytest tests/`, sequential, coverage-on per `addopts`)
takes **13:46** wall for only ~5 min CPU — it is wait-bound, and its coverage
instrumentation doubles the cost of the parallel loop. Three mechanical
reductions, each independently measurable: enable coverage's `sys.monitoring`
core, split unit and integration into parallel-friendly lanes, and mark the
pytest-in-pytest meta-tests `slow` so the documented fast loop excludes them.

Depends on FR-921 (fr784 xdist safety) for the `-n auto` full-suite goal and
benefits from FR-922 (283s recap test skip); this FR owns everything else.

## Value Statement

Full suite with coverage drops from ~14 min toward ~4–5 min; the documented
fast loop drops below 90s — directly reducing the execution drag the operator
flagged.

## Problem

Measured on main @ ca44832b (2026-08-30):

| Configuration | Wall | CPU (user+sys) | Result |
|---|---|---|---|
| `pytest tests/` (default: sequential + coverage) | 13:46 | 4:52 | 6474 passed, cov 94.02% |
| `pytest tests/ -n auto` (+ coverage) | 7:19 | 19:18 | 6 extra failures (FR-921) |
| `pytest tests/unit -m "not slow" --no-cov -n auto` (fast loop) | 2:17 | 10:42 | clean* |
| fast loop + coverage | 4:44 | 15:28 | clean* |

\* modulo 2 failures owned by in-flight FR-909/FR-918 arcs.

Three specific defects:

1. **Coverage overhead is +107%** on the parallel loop (2:17 → 4:44), with sys
   time ballooning 3:25 → 7:12 — the default C-tracer under xdist. coverage
   7.15 on Python 3.13/3.14 supports the `sys.monitoring` core
   (`COVERAGE_CORE=sysmon`), which avoids per-line trace overhead.
2. **One sequential lane does all the work**: integration tests are API-wait
   dominated (380s of the top-30 durations) while unit tests are CPU-bound —
   serializing them in one coverage-instrumented lane is the worst arrangement
   of the same work.
3. **Fast loop is polluted by meta-tests**: pytest-in-pytest and repo-scan
   tests run inside the "not slow" tier —
   `test_fr275_test_speed_optimization` (18.0s combined),
   `test_example_taxonomy_scan` (21.2s), `test_fr278_remove_baseline_dead_code`
   (11.3s). ~50s of the 137s fast loop is tests about the test suite.

## Proposed Solution

1. **Coverage core**: set `COVERAGE_CORE=sysmon` in the CI test workflow env
   and document it in `CLAUDE.md` dev commands. Clock before/after on the
   fast-loop-with-coverage configuration; record both numbers in this FR.
   If sysmon is incompatible with any plugin in use, record that and stop —
   detection_without_enforcement in reverse: no silent claim either way.
2. **Lane split** in `.github/workflows/workflow.yml`: job A runs
   `tests/unit -n auto` with coverage (gate stays ≥85, measured against the
   unit lane); job B runs `tests/integration` without coverage. Branch
   protection required-contexts updated to the new job names — enforcement at
   the merge boundary moves with the jobs, or the gate silently vanishes.
3. **Slow-mark hygiene**: add `@pytest.mark.slow` to the three meta-test
   modules above. REQ coverage unaffected (marks, not skips).

## Acceptance Criteria

- [ ] `COVERAGE_CORE=sysmon` active in CI; before/after wall times recorded in this FR
- [ ] Unit and integration run as separate CI jobs; integration lane runs without coverage
- [ ] Required status checks on `main` updated to match renamed/split jobs (verified via `gh api`)
- [ ] Coverage gate still enforced ≥85% on the unit lane
- [ ] Fast loop (`tests/unit -m "not slow" --no-cov -n auto`) ≤ 90s on the reference machine (2026-08-30 baseline: 2:17, with ~60s owed to FR-921 and ~50s to slow-marks)
- [ ] `CLAUDE.md` testing section updated with measured timings
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Make `-n auto` the pytest default in `addopts` | Rejected until FR-921 lands and 3 clean consecutive full parallel runs are recorded — 6 tests fail under xdist today |
| Drop coverage locally, keep sequential CI | Rejected — CI is where the 13:46 hurts automation (watcher2/chaplain PR latency); local convention already uses `--no-cov` |
| Move meta-tests to `tests/` top level or `scripts/tests/` | Deferred — re-tiering by mark is sufficient and cheaper; relocation is churn without added exclusion power |
| Coverage on integration lane too | Rejected — integration exercises live-API paths whose coverage delta is marginal; the wait-bound lane should carry zero instrumentation |

## Related

- FR-921 (fr784 xdist safety — prerequisite for full-suite `-n auto`)
- FR-922 (recap 283s test skip + investigation)
- FR-275 / CAP-126 (test speed optimization precedent)
- FR-714 (coverage gate raised to 85)
- `.github/workflows/workflow.yml`, `pyproject.toml` `[tool.pytest.ini_options]`
- Clock logs: `logs/clock-full.log`, `logs/clock-full-xdist.log`, `logs/clock-fast.log`, `logs/clock-fast-cov.log`
