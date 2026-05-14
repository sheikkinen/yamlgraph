# Reflection: FR-380 Pre-commit diary Seed marker parity

## Cognitive Traps and Insights

**Trap: gate_checks_shape_not_substance at the boundary between CI and pre-commit.**
The pre-commit `diary-reflection-check` only validated unfilled placeholder stubs
(shape check: "does the stub text appear?") while CI's `diary-gate` additionally
required a `Seed:` marker (substance check). This created a parity gap: a reflection
could pass locally and still fail CI.

**Insight: detection_without_enforcement.**
The CI gate enforced `Seed:` but the local hook did not — making CI the first
discovery point for an error that can only be corrected locally. Fast feedback
loops require parity between local and remote enforcement at the same boundaries.

**Insight: normalize at the entry boundary.**
The fix was minimal: extend the pre-commit grep pattern to also assert `Seed:` is
present. No new tools, no shared framework — a single additional condition in the
YAML hook entry closes the gap. The CI definition remains the canonical source of
truth; pre-commit mirrors the same rule.

## What Worked Well

- Identifying the exact divergence by diffing the hook entry against the CI
  `validate_diary_reflection_file()` function made the scope unambiguous.
- Single-responsibility constraint kept the change surgical: only `Seed:` parity,
  no other CI substance rules imported into pre-commit.

## Heuristic Graduated

`gate_checks_shape_not_substance`: every enforcement gate should check substance
(content meaningful, required structural markers present), not only shape
(file exists, pattern absent). When CI enforces substance and a local hook
enforces only shape, contributors discover substance failures too late.

Seed: Could a lightweight pre-commit meta-check automatically flag divergences
between CI gate conditions and their local hook counterparts — e.g., by parsing
`gate_artifact_semantics.sh` and comparing checks against `.pre-commit-config.yaml`?
