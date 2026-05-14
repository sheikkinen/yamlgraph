# Reflection: FR-380 Watcher2 Sanity-Check State

**Date:** 2026-05-14
**FR:** FR-380 Pre-commit diary Seed marker parity
**Reviewer:** watcher2 (post-validate sanity check)

## Trap

`gate_checks_shape_not_substance` — the pre-commit hook was only enforcing
placeholder-stub absence (shape) while CI additionally required a `Seed:`
marker (substance). A contributor could pass local hooks and still fail CI,
making CI the first and only discovery point for a locally-correctable error.

## What Happened

FR-380 closed the parity gap by extending `diary-reflection-check` in
`.pre-commit-config.yaml` to also run `grep -L "Seed:"` over staged diary
reflection files, mirroring the semantics of CI's `validate_diary_reflection_file()`.
The scope was surgical: 7 files, 213 insertions, covering the hook entry,
three new behavioral tests, and requirement/capability documentation updates
in `ARCHITECTURE.md` and `CAP-45-diary-reflection-enforcement.yaml`.

## Root Cause

The original FR-144 implementation was written before `Seed:` enforcement was
added to CI (`gate_artifact_semantics.sh`). The two gates accrued independent
evolution without a parity check, leaving a window where local enforcement
was weaker than remote enforcement.

## What Worked

- **Scope constraint enforced**: only `Seed:` parity was addressed; no other
  CI substance rules were pulled into the local hook.
- **Behavioral tests**: `test_missing_seed_marker_rejected` and
  `test_filled_reflection_accepted` run real temp files through the actual
  shell hook entry, providing genuine substance coverage.
- **Silent-scope change documented in tests**: the switch from `git ls-files`
  (all tracked files) to `git diff --cached` (staged files only) is a better
  semantic fit for a pre-commit hook; the CI gate retains full-PR coverage.
- All 11 diary-related tests pass green.

Seed: Could an automated parity auditor periodically diff the check conditions
in `gate_artifact_semantics.sh` against their local hook counterparts in
`.pre-commit-config.yaml` and raise a warning issue when they diverge?
