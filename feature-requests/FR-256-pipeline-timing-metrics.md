# Feature Request: Pipeline Timing Metrics

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-19
**Origin:** GitHub Issue #132

## Summary

Add lightweight timing and outcome instrumentation to the three core pipeline scripts (`enforce_worktree.sh`, `bugfix_worktree.sh`, `watch.sh`) so that pipeline health — duration, phase breakdown, and success rate — is observable from local JSON files. Include a read-only aggregation script for daily summaries.

## Value Statement

Pipeline operators gain visibility into per-FR wall time, phase bottlenecks, and failure rates, enabling data-driven process improvement without adding external dependencies.

## Problem

The Chaplain pipeline is 95% closed-loop but has zero observability at the script level. With 36 commits and 8 PRs merged in a single day, none of these questions can be answered:

- How long does `enforce_worktree.sh` take per FR? (Observed: 10 min to 2+ hours)
- What is the PR CI failure rate?
- Which pipeline phase dominates wall time?
- How many worktree retries occur before a successful PR?

The only visibility today is terminal scroll output and optional LangSmith traces (CAP-89 covers LLM call timing only). Neither supports aggregate analysis across pipeline runs.

## Proposed Solution

Instrument the existing EXIT traps in `enforce_worktree.sh` and `bugfix_worktree.sh`, and add inline per-cycle timing in `watch.sh`, to write a JSON metrics file on every exit. No new dependencies — pure bash using `date +%s` for timestamps and heredoc/printf for JSON serialization.

### Phase timing pattern (bash)

```bash
# At script top
METRIC_DIR="tmp/pipeline-metrics"
mkdir -p "$METRIC_DIR"
T_START=$(date +%s)

# Before each phase
t_phase_start=$(date +%s)

# After each phase
t_phase_end=$(date +%s)
PHASE_WORKTREE_SETUP=$((t_phase_end - t_phase_start))
```

### `scripts/enforce_worktree.sh` — emit timing JSON

Record timestamps at each phase boundary. The script already has a `cleanup()` function (lines 77–111) registered as `trap cleanup EXIT` (line 111). Extend this cleanup to write the metrics file.

**Phase boundaries** (approximate line ranges):
1. **worktree_setup** (lines 21–135): branch derivation, `git worktree add`, `.venv` symlink, `cd` into worktree
2. **llm_enforce** (lines 136–142): `yamlgraph graph run .chaplain/graphs/enforce/graph.yaml`
3. **post_assertions** (lines 144–149): `bare=true` corruption check
4. **pr_creation**: success output and PR creation (lines 150–175)

**Output JSON:**

```json
{
  "pipeline": "enforce",
  "fr": "FR-253",
  "branch": "feat/fr-253-example",
  "outcome": "success",
  "started_at": "2026-04-19T14:00:00Z",
  "finished_at": "2026-04-19T14:45:00Z",
  "duration_seconds": 2700,
  "phases": {
    "worktree_setup": 12,
    "llm_enforce": 2400,
    "post_assertions": 180,
    "pr_creation": 15
  },
  "pr_number": 129,
  "retries": 0
}
```

**Output path:** `tmp/pipeline-metrics/enforce-FR-253-2026-04-19T140000.json`

### `scripts/bugfix_worktree.sh` — same schema

Identical instrumentation with `"pipeline": "bugfix"` discriminator. The script has the same `cleanup()` / `trap cleanup EXIT` structure (lines 77–111). The same phase boundaries apply, with the graph invocation targeting `examples/bugfix/graph.yaml` instead.

### `.chaplain/watch.sh` — inline cycle metrics

**Important:** Unlike the worktree scripts, `watch.sh` has **no EXIT trap and no cleanup function**. It runs an infinite polling loop (`while true; do` at line 20, `done` at line 113). Instrumentation must be **inline** — timing variables set before/after the `scripts/enforce_worktree.sh` and `scripts/bugfix_worktree.sh` calls (lines 82, 92) within the polling loop body.

Per polling cycle that processes an inbox item, record end-to-end timing and outcome:

```json
{
  "pipeline": "chaplain-cycle",
  "inbox_item": "gh-125.md",
  "fr_generated": "FR-253",
  "verdict": "approved",
  "enforce_outcome": "success",
  "total_seconds": 3200,
  "github_issue_closed": 125
}
```

**Output path:** `tmp/pipeline-metrics/chaplain-cycle-2026-04-19T140000.json`

### `scripts/pipeline_summary.py` — daily aggregation

A read-only aggregation script that reads `tmp/pipeline-metrics/*.json` and prints a daily summary. Uses Python stdlib only (`json`, `pathlib`, `datetime`).

```
Pipeline Summary (2026-04-19):
  FRs processed: 8
  Total wall time: 4h 23m
  Avg per FR: 32m
  Success rate: 100% (8/8)
  Longest: FR-250 (1h 12m)
  Shortest: FR-252 (18m)
```

## Acceptance Criteria

- [ ] `enforce_worktree.sh` writes timing JSON to `tmp/pipeline-metrics/` on every exit (success and failure) via extended `cleanup()` function
- [ ] `bugfix_worktree.sh` writes timing JSON with same schema (discriminated by `"pipeline": "bugfix"`) via its `cleanup()` function
- [ ] `watch.sh` writes cycle metrics JSON for every inbox item processed, using inline timing around enforce/bugfix calls (not trap-based)
- [ ] JSON write is best-effort: metric write failure must not affect pipeline outcome (guard with `|| true`)
- [ ] `tmp/pipeline-metrics/` directory is created on demand (`mkdir -p`)
- [ ] `tmp/` is already gitignored — verify only, no `.gitignore` changes
- [ ] `scripts/pipeline_summary.py` aggregates daily metrics from JSON files (stdlib only)
- [ ] Unit test for `pipeline_summary.py` with fixture JSON files
- [ ] No new dependencies introduced (bash `date +%s`, printf for JSON; Python stdlib for summary)

## Constraints

- **No pipeline behavior change**: Metrics are write-only side effects. In the worktree scripts, writes happen in the EXIT trap cleanup. In `watch.sh`, writes happen inline. A failed JSON write must never cause a pipeline failure.
- **No new dependencies**: Pure bash for instrumentation; Python stdlib only for the summary script.
- **No git tracking of metrics**: Output lives in `tmp/` which is already gitignored (line 21 of `.gitignore`).
- **Phase boundaries are approximate**: `date +%s` gives second-level granularity, which is sufficient for pipelines measured in minutes.

## Alternatives Considered

1. **LangSmith-only**: Already available for LLM call tracing (CAP-89), but does not cover bash pipeline phases (worktree setup, pre-commit, PR creation). Complementary, not a replacement.
2. **Structured logging to stdout**: Would require parsing terminal output with ANSI codes. JSON files are simpler to aggregate.
3. **SQLite metrics database**: More queryable but adds complexity. JSON files are append-only, human-readable, and trivially debuggable. Can migrate to SQLite later if volume warrants it.
4. **External observability (Prometheus/Grafana)**: Overkill for a local development pipeline. JSON files serve as the data source if external tooling is desired later.

## Implementation Notes

- `enforce_worktree.sh` and `bugfix_worktree.sh` already have EXIT traps with `cleanup` functions (lines 77–111, trap registered at line 111) — extend these to write the metrics file after existing cleanup logic.
- `watch.sh` has **no EXIT trap**. Its instrumentation is **inline per-cycle**: capture `t_cycle_start` before the enforce/bugfix call (lines 82, 92 respectively) and `t_cycle_end` after, then write the JSON. This is not trap-based.
- Filename timestamps use ISO 8601 with colons removed for filesystem safety (e.g., `2026-04-19T140000`).
- The `pipeline_summary.py` script uses `json`, `pathlib`, and `datetime` from stdlib only.

## Architecture

- **Requirement:** REQ-YG-259 (Pipeline timing metrics)
- **Capability:** CAP-112 (Pipeline Timing Metrics)
- **Layer:** Presentation (scripts are Layer 1 — CLI/process orchestration)
- **Boundary:** Platform boundary — timestamps are OS-level; JSON write is filesystem side effect
- **Relation to CAP-89:** CAP-89 (Execution Timing Callback) tracks per-LLM-call timing inside graph execution. This FR tracks per-phase timing of the outer bash pipeline. They are complementary.

## Judgement

**Verdict:** APPROVE — Scope frozen. Authority granted.

**Reviewed:** 2026-04-19

**Findings:**

1. **Scope:** Clear and minimal. Four deliverables (three script instrumentations + one summary script) serve a single concern: pipeline observability. No scope creep.
2. **Structural claims verified against code:**
   - `enforce_worktree.sh`: `cleanup()` at line 78, `trap cleanup EXIT` at line 111 — confirmed.
   - `bugfix_worktree.sh`: identical structure at identical lines — confirmed.
   - `watch.sh`: no EXIT trap, infinite loop at line 20, enforce/bugfix calls at lines 82/92 — confirmed.
   - `tmp/` gitignored at line 21 of `.gitignore` — confirmed.
3. **Acceptance criteria:** All nine criteria are binary and testable.
4. **Feasibility:** Pure bash `date +%s` + printf is zero-dependency and proven. Python stdlib summary is trivial.
5. **Architecture alignment:** Layer 1 placement correct. Commandment 9 ("operational truth") directly satisfied. Complementary to CAP-89 (LLM-level timing) — no overlap.

**Minor notes for implementer:**
- Phase "pr_creation" (lines 150–175) is actually success output / next-steps echo — no PR creation happens there (graph handles it at line 139). Rename to `success_output` or similar.
- REQ-YG-259 and CAP-112 must be created in `ARCHITECTURE.md` and `scripts/req_coverage.py` during implementation.

## Related

- FR-106: Enforce worktree script (original)
- FR-128: Enforcement pipeline
- FR-173: Bugfix worktree script
- FR-243: Watch daemon enhancements
- FR-251: Watch daemon sequential enforcement
- CAP-89: Execution Timing Callback (LLM-level timing — complementary)
- ADR-001: Requirement traceability
- Commandment 9: "Thou shalt define and observe operational truth"
