# Diary: FR-373 Gate Artifact Substance Validation

**Date:** 2026-05-13
**FR:** FR-373 — Substance validation for diary-gate and changelog-gate
**Reviewer:** validate_fix remediation pass

## What Happened

FR-373 hardens two CI merge gates (`changelog-gate` and `diary-gate`) from
presence-only checks to substance-validated checks. The gates now call shared
shell validation functions from `scripts/gate_artifact_semantics.sh` and reject
artifacts that are empty, lack required structural markers (front-matter `type:`
field, `##` headers, `Seed:` marker), or fall below a minimum byte threshold.

The implementation reuses the FR-325 `demo_log_semantics.sh` pattern:
extract validation logic into a sourced shell module, wire it into the CI
workflow, and cover both shapes (valid/invalid) with unit tests.

## Trap: gate_checks_shape_not_substance

The exact trap named in the Knowledge Graph was the driver for this FR:

> Gate validates presence (file exists, field non-empty, format matches) but
> not substance — compliance theatre; a 1-byte file satisfies the gate while
> conveying nothing.

Both gates fell into this pattern independently. The cure was to treat each
artifact as an external input entering the enforcement boundary — normalizing
there rather than trusting form alone.

## What Worked

- **Shared validator module** (`gate_artifact_semantics.sh`) eliminates
  duplicated inline logic and makes future gate extensions a one-line `source`.
- **TDD structure is explicit:** `test_fr373_gate_substance_validation_red.py`
  names every acceptance criterion; existing `test_ci_changelog_gate.py` and
  `test_ci_diary_gate.py` are extended to cover semantic cases.
- **Incremental scope:** only `changelog-gate` and `diary-gate` are touched;
  `demo-gate` and other gates are out of scope, keeping the blast radius small.

## Concerns

1. Minimum byte threshold (100 bytes for diary, checked via `wc -c`) is a
   proxy for substance. A sophisticated actor can satisfy the threshold with
   padding. The `##` header + `Seed:` structural requirement is the real
   semantic guard; size is a secondary sanity check.
2. The shared shell module is tested by inspecting its source file in Python
   unit tests. This is a structural test, not an execution test — a behavioral
   integration test (actually sourcing the script in bash) would be stronger.

## Seed

If structural marker checks (`##`, `Seed:`, `type:`) are the real substance
gates, should a future FR define a YAML schema for diary reflections and
changelog fragments and validate them with a proper parser (e.g., `pyyaml` +
Pydantic) rather than shell `grep`? Would that finally close the gap between
shape validation and semantic validation for compliance artifacts?
