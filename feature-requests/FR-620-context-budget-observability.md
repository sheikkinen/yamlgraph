# Feature Request: Context-Budget Observability

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-06-28

## Summary

Treat *context-window pressure* as a first-class, observable operational signal:
surface per-node input-context size (and its fraction of the model's window) in
the existing timing/token reporting, and warn when a node approaches the limit —
so context rot is caught as a measured defect, not discovered as degraded output.

## Value Statement

Operators and graph authors can *see* when a graph is about to outgrow its
attention budget, turning silent quality decay into an explicit, actionable signal
they can fix (with compaction, memory, or lazy variables) before it bites.

## Value Proposal

- **Closes a Commandment-9 gap**: We instrument latency (`--timing`) and tokens
  (`--token-usage`), but not *context pressure* — the very failure mode the 2025
  context-engineering guidance identifies as primary. Performance degradation and
  evaluation drift are production defects; this makes one of them visible.
- **Makes the other four FRs measurable**: Compaction (FR-616), memory (FR-617),
  and lazy variables (FR-618) all claim to *reduce context*. This FR provides the
  ruler that proves they work — without it, their value is asserted, not shown.
- **Cheap, additive, non-invasive**: It extends existing reporting hooks; no graph
  semantics change. Lowest-risk way to operationalize the context budget.
- **Read-the-artifact discipline**: Per `read_raw_output_first`, the cheapest
  diagnostic for "why did quality drop at step 7?" is seeing that step 7's input
  was 95% of the window. This surfaces that fact at the boundary.

## Problem

YAMLGraph has no view of how full the context window is at each node. Authors
discover context rot only as degraded output, with no signal pointing at the
cause. There is no threshold, no warning, and no per-node context-size line in any
report — so the dominant long-horizon failure mode is invisible.

## Proposed Solution

Extend the existing timing/token callback to also record, per node, the estimated
input-context token count and its fraction of the configured model window; add a
CLI flag and an optional warn threshold.

```bash
# New summary column alongside --timing / --token-usage
yamlgraph graph run graph.yaml --var x=1 --context-usage

# Example output
# node            in_tokens   window%   status
# load_history       38,210      30%     ok
# expand_world      102,640      80%     WARN  (approaching window)
# synthesize        128,900     101%     OVER  (will truncate/error)
```

```yaml
# Optional per-graph or per-node policy
metadata:
  context_warn_fraction: 0.8     # warn when a node's input exceeds 80% of window
```

- Reuses the **execution-timing callback** plumbing (already per-node).
- Window size resolved from provider/model metadata (heuristic fallback).
- `WARN`/`OVER` are *signals*, not hard failures (v1) — non-breaking.

## Acceptance Criteria

- [ ] Per-node input-token estimate + window-fraction captured via existing callback
- [ ] `--context-usage` CLI summary table
- [ ] Optional `context_warn_fraction` policy emits a WARN at/over threshold
- [ ] Window size resolved per provider/model with a documented fallback
- [ ] No change to graph execution semantics (purely observational)
- [ ] Tests tagged with a new `REQ-YG-XXX`; capability file added
- [ ] `reference/getting-started.md` documents the flag alongside `--token-usage`

## Alternatives Considered

- **LangSmith-only inspection**: traces show tokens but not window-fraction or a
  proactive threshold, and require leaving the CLI; this surfaces the signal at
  the point of execution.
- **Hard-fail on overflow**: rejected for v1 — providers already error on true
  overflow; a *warning* gives authors room to act before the cliff.
- **Do nothing (rely on output quality)**: the status quo; makes context rot a
  post-hoc discovery rather than a measured signal.

## Related

- `docs/2026-06-28-research.md` (gap #5)
- `execution-timing-callback`, `--token-usage` (reporting plumbing to extend)
- FR-616, FR-617, FR-618 (this is the ruler that validates their context savings)
