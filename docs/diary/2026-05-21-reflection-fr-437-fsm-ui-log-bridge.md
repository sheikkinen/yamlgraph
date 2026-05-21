# FSM UI Log Bridge Reflection — FR-437

**Date:** 2026-05-21
**FR:** FR-437 — FSM UI Activity Log Bridge
**Author:** copilot enforcement pass

## Trap

`workspace_is_not_boundary` + `gate_checks_shape_not_substance` — The new module
was implemented correctly but silently excluded by a broad `.gitignore` rule
(`fsm/`) that matched nested framework paths. Functionality existed locally but
would not survive commit.

## What Happened

FR-437 required a new shared utility module under `yamlgraph/utils/fsm/`.
Implementation and tests passed, but `git status` did not list the file.
Root cause was ignore pattern overlap: top-level private project ignore leaked
into framework package namespace.

## Root Cause

Boundary mismatch in ignore policy. The rule intended to hide private top-level
repos was path-ambiguous and matched any `fsm/` directory, including tracked
framework code neighborhoods.

## What Worked

1. Post-implementation verification included `git status` + `git check-ignore -v`.
2. Minimal remediation: keep top-level private repo ignored, add explicit unignore
   for `yamlgraph/utils/fsm/*.py`.
3. FR scope remained intact: utility added, exported, tested, and documented.

**Seed:** Should we add a guard test that asserts critical framework package paths
are never matched by broad ignore patterns (for example, `git check-ignore` smoke
checks in CI for `yamlgraph/utils/fsm/` and similar directories)?
