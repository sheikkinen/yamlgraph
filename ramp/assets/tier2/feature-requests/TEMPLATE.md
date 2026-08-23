# Feature Request: [Title]

**Priority:** LOW | MEDIUM | HIGH
**Type:** Feature | Bug | Enhancement
**Status:** Proposed
**Effort:** X days
**Requested:** YYYY-MM-DD
**First consumer / first event:** who uses this first, and at what
concrete moment? An FR that cannot complete this sentence is
`growth_as_default` (FR-746 F1; the consumer test).

## Summary

Brief description of the feature or bug.

## Value Statement

<!-- One sentence: Who benefits and how. -->
<!-- Example: "Graph authors get immediate feedback on broken edges, reducing debug time from minutes to seconds." -->

## Problem

What problem does this solve? Why is it needed?

## Raw Output Read (measurement / metric-tooling FRs only)

<!-- REQUIRED for any FR that adds or changes a scorer, an *_measure graph, an
     evaluate.py metric, or a score_*/combine_* tool. Delete this section for FRs
     that touch no measurement code. -->
<!-- read_raw_output_first (Scripture): READ the rawest artifact a stage emits
     BEFORE you build a ruler for it. cat, not a new metric, is the first
     diagnostic. The gate checks presence; this section must show substance. -->

- **Samples read:** link/path to >= K raw output samples dumped to disk.
- **What I saw:** one concrete, specific, surprising detail per sample
  (e.g. "The Swarm is not a person, yet the prose authored it a four-kind arc").
  A generated dump cannot produce this line; only a real read can.

## Ideal Result

State the ideal end state in one paragraph (`ideal_result_backwards`,
FR-746). The Proposed Solution below must read as the minimal path
back from it — a solution that outgrows its ideal is scope creep.

## Proposed Solution

How should it work? Include code examples if relevant.

```yaml
# Example usage
```

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests added
- [ ] Documentation updated

## Alternatives Considered

What other approaches were considered?

## Related

- Link to related issues, PRs, or files
- LangSmith trace as a separate file

## Judgement (date)

**Verdict:** APPROVED / APPROVED with corrections / REJECTED

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | … | … |

**Purge list:** …

**Scope frozen:** …

### Questions for the human (as options, or 'none')

<!-- FR-740: the interrupt is a judgement OUTPUT, not an agent
initiative. Each question: options + evidence + recommended default.
'None' is a statement; absence is an omission. -->
