# Feature Request: FR-418 fallback-token confession gate for production Python

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-19

## Summary

Extend `scripts/hedging_check.py` to detect lexical `fallback` usage in production Python code and require confession-backed allowlisting for any retained usage.

## Value Statement

Maintainers get an auditable hygiene gate that prevents ambiguous `fallback` language from normalizing silent-failure behavior.

## Problem

Issue #418 asks for stricter handling of `fallback` usage in production code. Current guardrails are incomplete:

1. `scripts/hedging_check.py` detects only one AST hedging pattern (`if not X: X = ...`), while its docstring claims a second pattern that is not implemented.
2. There is no lexical detector for `fallback` in identifiers, comments, or docstrings.
3. There is no confession contract equivalent to `scripts/noqa_coverage.py` for this token.
4. Current pre-commit wiring runs `hedging_check.py` only on `yamlgraph/`, while production helper scripts also contain `fallback` usage.

Repository evidence (2026-05-19):

- `rg -i '\bfallback\b' yamlgraph scripts -g '*.py'` returns 45 matches across production Python code.
- `.pre-commit-config.yaml` runs `scripts/hedging_check.py yamlgraph --strict`.
- `docs/confessions.md` already defines the project confession structure (`CONF-XXX`, file+line, code, sin, penance).

## Research Findings

1. Requested topic source `.chaplain/processing/gh-418.md` is absent in this worktree; canonical source used: GitHub issue #418.
2. Prior art exists for confession-enforced lint exceptions:
   - `scripts/noqa_coverage.py` parses `docs/confessions.md` and fails strict mode for undocumented suppressions.
3. Existing doctrine surface already treats silent-failure language as a quality concern:
   - `ARCHITECTURE.md` Capability 16 includes REQ-YG-114 (W017 warning for `on_error: skip` silent fallback).
4. Existing `hedging_check.py` is the right enforcement entrypoint:
   - already wired into pre-commit strict mode and focused on fallback-related hygiene.

## Objectives

1. Add lexical `fallback` detection in production Python (`yamlgraph/`, `scripts/`).
2. Require confession-backed allowlisting for retained occurrences.
3. Preserve existing `hedging_check` AST behavior while adding the new gate.

## Constraints

1. Single responsibility: only fallback-token hygiene enforcement (no runtime behavior changes).
2. Do not rename public YAML contract terms in this FR (`on_error: fallback`, `fallback:` schema field).
3. Keep scanning scope to production Python (`yamlgraph/`, `scripts/`), excluding tests/examples/docs.
4. Reuse `docs/confessions.md` instead of adding a second confession registry.

## Proposed Solution

1. Extend `scripts/hedging_check.py` with an `FB001` finding class for lexical `fallback` detection:
   - **Identifiers**: AST names (`ast.Name`, function/class names, args).
   - **Docstrings**: AST docstring extraction.
   - **Comments**: token stream via `tokenize`.
2. Introduce confession-aware allowlisting for `FB001`:
   - allowlist maps `file:line` → `CONF-XXX`;
   - strict mode fails when `FB001` is unconfessed or mapped to missing/mismatched confession metadata.
3. Keep existing pattern-1 hedging detection intact and add missing pattern-2 (`X = expr or fallback`) detection as part of the same script scope.
4. Update pre-commit hook invocation to cover `yamlgraph` and `scripts` for this check.
5. Add focused RED acceptance tests for FR-418 behavior.

## Acceptance Criteria

- [x] **AC-01:** `hedging_check.py` emits `FB001` for `fallback` in identifiers.
- [x] **AC-02:** `hedging_check.py` emits `FB001` for `fallback` in comments/docstrings.
- [x] **AC-03:** `hedging_check.py --strict` exits non-zero when `FB001` findings are unconfessed.
- [x] **AC-04:** `hedging_check.py --strict` exits non-zero when allowlist entries do not resolve to valid `CONF-XXX` entries for `FB001`.
- [x] **AC-05:** `hedging_check.py` detects documented Pattern 2 (`X = expr or fallback`) in addition to existing Pattern 1.
- [x] **AC-06:** Existing Pattern 1 detection (`if not X: X = ...`) remains intact (no regression).
- [x] **AC-07:** Pre-commit `hedging-check` scope includes both `yamlgraph/` and `scripts/`.
- [x] **AC-08:** Requirement traceability is updated during implementation (new requirement entry + capability registry update + req-tagged tests).

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr418_fallback_confession_gate.py`

Planned RED tests:

1. `test_ac01_flags_fallback_in_identifier_name`
2. `test_ac02_flags_fallback_in_comment`
3. `test_ac02_flags_fallback_in_docstring`
4. `test_ac03_strict_mode_fails_on_unconfessed_fb001`
5. `test_ac04_strict_mode_fails_on_invalid_confession_mapping`
6. `test_ac05_detects_pattern2_or_fallback_assignment`
7. `test_ac06_existing_pattern1_detection_still_works`

RED command:

```bash
pytest tests/unit/test_fr418_fallback_confession_gate.py -q --no-cov
```

## Alternatives Considered

1. **Grep-only policy gate**
   Rejected: too noisy; cannot distinguish code surfaces or confession status.

2. **New standalone script just for fallback confessions**
   Rejected: duplicates enforcement pipeline and splits ownership from existing `hedging_check`.

3. **Runtime warning-only approach**
   Rejected: cannot cover comments/docstrings/identifier hygiene at commit time.

4. **Global rename campaign first, no gate**
   Rejected: no prevention of future drift; lacks ongoing enforcement.

## Judgement Notes

- `ALLOWLIST` type must change from `set[str]` to `dict[str, str]` (file:line → CONF-XXX). Implied by proposed solution; made explicit here.
- Confessions path must resolve relative to script location (`Path(__file__).parent.parent / "docs/confessions.md"`), not relative to the scanned directory.
- AC-08 (new REQ-YG-XXX + capability registry entry + req tag update from placeholder REQ-YG-063) is mandatory before commit.
- Tests are in correct RED state: 6 missing-implementation failures, 1 pass confirming infra (Pattern 1) works.

## Related

- Issue #418: <https://github.com/sheikkinen/yamlgraph/issues/418>
- `scripts/hedging_check.py`
- `tests/unit/test_hedging_check.py`
- `scripts/noqa_coverage.py`
- `docs/confessions.md`
- `.pre-commit-config.yaml`
- `ARCHITECTURE.md` (Capability 16 / REQ-YG-114 context)
- Requested source path: `.chaplain/processing/gh-418.md` (missing in this worktree snapshot)
