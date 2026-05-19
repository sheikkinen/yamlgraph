# Reflection: FR-421 Watcher2 Sanity Check

**Date:** 2026-05-19
**FR:** FR-421 Built-in Questionnaire Gap Utilities
**Reviewer:** watcher2 post-validate

## Trap

`framework_costume` / `working_system_inertia` — logic that works fine as project-local code can resist promotion to a framework primitive because "it already works." The existing `examples/questionnaire/tools/handlers.py::detect_gaps` was functional, but per-project copies silently diverge over time (e.g., `probe_count` management creeping into gap detection). The pull toward status quo nearly prevented this extraction.

## What Happened

FR-421 extracted `detect_gaps` and `normalize_extracted` into `yamlgraph/tools/questionnaire.py` as framework primitives callable via existing `type: python` tool wiring. All 10 acceptance criteria were implemented in a single commit:

- Implementation: 40 lines (`yamlgraph/tools/questionnaire.py`)
- 14 unit tests covering all ACs including a full end-to-end YAML wiring integration test (AC-08)
- CAP-153 registered, REQ-YG-409/410 defined and traced, ARCHITECTURE.md updated
- Changelog fragment, reference documentation snippet, FR-415 supersession notice — all present
- `probe_count` divergence from the example handler explicitly documented via inline comment

Tests are behavioral (assert on return values, not internal state). The parametrized AC-07 test covers 7 non-dict types (`None`, `str`, `int`, `float`, `list`, `tuple`, `bool`), providing strong boundary coverage without implementation coupling.

## Root Cause

The original gap detection lived in project space because `yamlgraph/tools/` had no questionnaire module. No framework contract existed, so teams copied rather than imported. FR-421 established that contract at the correct boundary: the `type: python` tool interface.

## What Worked

- Scope freeze was precise: no new node types, no orchestration changes, no linter rules
- The `probe_count` divergence note in the implementation prevents migrators from re-adding it by mistake
- The AC-08 wiring test uses `load_and_compile` + `compiled.invoke` — a true integration check, not a mock
- REQ coverage script confirms CAP-153 at 2/2 reqs, 9 tests after accounting for class-level marker inheritance

## Seed

**Seed:** If `detect_gaps` is now a framework primitive, should there be a `strict_gaps` variant that raises instead of returning `has_gaps: True`? When would graph authors prefer a hard failure at detection time versus routing on the boolean — and could a `mode: strict|soft` parameter on the same utility serve both, or does that violate single-responsibility?
