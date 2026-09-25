# Feature Request: Repair `innovation_matrix` — declared input, derived grid size

**Priority:** MEDIUM
**Type:** Bug
**Status:** Rejected — [judgement](FR-1070-innovation-matrix-repair.judgement.md); no implementation authority. Re-file with research and a supported grid bound.
**Refiled (2026-09-25):** as [FR-1088](FR-1088-innovation-matrix-repair.md).
**Effort:** 0.5 days
**Requested:** 2026-09-25
**First consumer / first event:** the next
`yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml --var domain=@brief.md`;
on 2026-09-24 the brief never reached state, every cell was domain-free, and
the synthesis prompt claimed 25 cells while receiving 21 plus four error
strings.
**Research:** in-body dispositioned alternatives table below, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1 (witnessed run)
and §2 D9. The FR-890 research route was not run.
**Prior art:** the demo's own `PORTING_PLAN.md`. No FR covers it.

## Summary

Declare `domain` in the graph's `state:` block, derive the grid size from the
generated dimensions instead of hard-coding 5 × 5, and make the synthesis
prompt render the actual number of expansions.

## Value Statement

The demo produces cells about the domain it was given and reports the count it
actually has.

## Problem

- `pipeline.yaml` has no `state:` entry for `domain`, so `--var domain=…` is
  dropped (D5; [FR-1067](FR-1067-reject-undeclared-cli-vars.md) makes that
  loud).
- `nodes/cartesian.py` builds cell IDs assuming five constraints; `max_items`
  is 25; `prompts/synthesize.yaml` says "25" literally.

## Ideal Result

For any `n_capabilities × n_constraints` dimensions, the product, the map's
`max_items`, the IDs and the synthesis count agree, and the synthesis sees
only successful expansions (from [FR-1064](FR-1064-map-branch-contract.md)).

## Proposed Solution

All graph and prompt edits via `scripts/author.sh` (FR-767); the Python node is
edited in the same run.

- `state:` declares `domain`.
- `cartesian.py`: IDs `C{i // n_constraints + 1}S{i % n_constraints + 1}`
  with `n_constraints` from the input.
- `max_items` equals the product size (state expression, or the node returns
  it).
- `synthesize.yaml`: `{{ expansions | length }}` replaces the literal "25"
  (four occurrences: description, L18, L27, L43). The dimensions prompt still
  asks for five of each; the code no longer depends on it.
- Lands after FR-1064 and FR-939 (overflow raises instead of slicing).

## Acceptance Criteria

- [ ] RED: a unit test of `cartesian.py` with 4 × 3 dimensions yields 12 unique IDs `C1S1…C4S3`.
- [ ] `graph lint` clean; E007 no longer reports `domain`.
- [ ] Smoke run with a short `--var domain=…` brief: the dimensions mention the brief's domain (read the raw output; record one quoted line).
- [ ] `demo-output.log` regenerated from `pipeline.yaml` itself.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Force the dimensions prompt to always return 5 × 5 | Rejected: hides the coupling; the next prompt edit breaks it again. |
| Edit the YAML directly | Forbidden: FR-767 route. |

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 H
- Depends on: [FR-1064](FR-1064-map-branch-contract.md), [FR-939](FR-939-map-overflow-policy.md)
