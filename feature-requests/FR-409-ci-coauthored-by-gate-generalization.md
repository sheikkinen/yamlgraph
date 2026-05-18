# Feature Request: FR-409 Generalize CI trailer gate to reject any Co-authored-by identity trailer

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.25 day
**Requested:** 2026-05-18

## Summary

Widen `copilot-trailer-gate` so CI rejects any `Co-authored-by:` trailer in PR commit messages or PR body text, not only Copilot-specific literal strings.

## Value Statement

Maintainers get substance-level enforcement of the "no identity trailers" policy, closing a bypass where non-Copilot `Co-authored-by` values currently pass.

## Problem

GitHub issue #408 reports an enforcement gap: the CI job `copilot-trailer-gate` matches only two literal Copilot strings and can be bypassed with another trailer identity (for example `Co-authored-by: Test`).

Evidence in this worktree:

1. `.github/workflows/commitlint.yml` defines only:
   - `TRAILER_SHORT='Co-authored-by: Copilot'`
   - `TRAILER_FULL='Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'`
   - grep checks against those two values only.
2. `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py` validates Copilot short/full forms but not arbitrary `Co-authored-by:` identities.
3. `CAP-148` and `REQ-YG-358` are currently worded as Copilot-specific, reinforcing shape-level matching instead of policy-level intent.

## Research: Existing Patterns and Prior Art

1. **Existing CI gate pattern:** deterministic shell checks in `.github/workflows/commitlint.yml` (`conflict-check`, `changelog-gate`, `demo-gate`, `diary-gate`) with explicit pass/fail exit codes.
2. **Current trailer governance split:**
   - CI (`copilot-trailer-gate`) is currently Copilot-literal only.
   - local commit-msg hook `scripts/block_ai_coauthor.py` blocks known AI identities but allows human `Co-authored-by:` trailers.
3. **Architecture traceability exists already:** CAP-148 / REQ-YG-358 cover this gate, so this FR should refine those definitions rather than introduce a new capability.
4. **Topic source file requested by prompt is absent in this worktree:**
   - Requested: `.chaplain/processing/gh-408.md`
   - Canonical source used: GitHub issue #408.

## Objectives

1. Reject all `Co-authored-by:` trailer identities in PR commit messages.
2. Reject all `Co-authored-by:` trailer identities in PR body text.
3. Keep enforcement deterministic and minimal in existing `copilot-trailer-gate` job.

## Constraints

1. Single responsibility: adjust CI trailer gate matching semantics only.
2. Preserve current workflow triggers/job topology; no unrelated CI refactor.
3. Keep detection deterministic (`git log` + grep), no LLM dependency.
4. Keep local `block-ai-coauthor` hook behavior out of scope for this FR.
5. Update existing CAP-148 / REQ-YG-358 wording to policy-level semantics ("any Co-authored-by identity trailer").

## Proposed Solution

### In scope

1. Update `.github/workflows/commitlint.yml` `copilot-trailer-gate` verification step to fail on any `Co-authored-by:` trailer line in:
   - `git log --format=%B "$BASE_SHA..$HEAD_SHA"`
   - `github.event.pull_request.body`
2. Remove dependence on Copilot-only literals in this job.
3. Extend unit coverage to include non-Copilot identity trailers and preserve clean-pass behavior.
4. Update CAP-148 and REQ-YG-358 text to match generalized trailer policy.
5. Update `CLAUDE.md` required-check description to reflect generalized CI behavior.

### Out of scope

1. Refactoring or replacing `scripts/block_ai_coauthor.py`.
2. Expanding policy beyond `Co-authored-by:` trailers to other trailer types.
3. Any watcher runtime/FSM changes.

## Acceptance Criteria

- [x] **AC-01:** CI fails when any commit in `BASE_SHA..HEAD_SHA` contains a non-Copilot trailer such as `Co-authored-by: Test <test@example.com>`.
- [x] **AC-02:** CI fails when PR body contains a non-Copilot trailer such as `Co-authored-by: Test <test@example.com>`.
- [x] **AC-03:** CI still fails for existing Copilot trailer forms (short and full email).
- [x] **AC-04:** PRs with no `Co-authored-by:` trailers in commits/body pass this gate unchanged.
- [x] **AC-05:** Unit tests cover AC-01..AC-04 with explicit red/green scenarios.
- [x] **AC-06:** CAP-148, REQ-YG-358, and `CLAUDE.md` wording align with generalized `Co-authored-by:` policy.

## Failing Acceptance Tests (RED plan)

RED test artifact to add in implementation:

- `tests/unit/test_fr409_ci_coauthored_by_gate_generalization_red.py`

Planned RED tests:

1. `test_ac01_commit_scan_rejects_non_copilot_coauthored_by_trailer`
2. `test_ac02_pr_body_scan_rejects_non_copilot_coauthored_by_trailer`
3. `test_ac03_commit_scan_still_rejects_copilot_short_and_full_forms`
4. `test_ac04_clean_commits_and_pr_body_pass_without_trailers`
5. `test_ac05_workflow_script_no_longer_depends_on_copilot_literal_constants`
6. `test_ac06_traceability_docs_use_generalized_coauthored_by_language`

RED command:

```bash
pytest tests/unit/test_fr409_ci_coauthored_by_gate_generalization_red.py -q --no-cov
```

Additional RED evidence command (expected to expose Copilot-literal matching before implementation):

```bash
rg -n "TRAILER_SHORT|TRAILER_FULL|Co-authored-by: Copilot" .github/workflows/commitlint.yml tests/unit/test_fr385_ci_copilot_trailer_gate_red.py capabilities/CAP-148-ci-copilot-trailer-gate.yaml ARCHITECTURE.md
```

## Alternatives Considered

1. **Keep Copilot-only literals**
   Rejected: continues bypass for non-Copilot identities and repeats issue #408.

2. **Use `scripts/block_ai_coauthor.py` directly in CI**
   Rejected: policy target here is any `Co-authored-by:` identity trailer, while that hook is AI-pattern based and intentionally allows human co-authors.

3. **Rename gate job from `copilot-trailer-gate` now**
   Rejected for minimality: semantic widening can ship without workflow job renaming; naming cleanup can be a separate docs/maintenance FR.

## Implementation Notes (Judge)

- **FR-385 test conflict:** `test_ac06_workflow_step_uses_deterministic_grep_without_llm` in `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py` asserts that `TRAILER_SHORT` and `TRAILER_FULL` constants exist in the CI script. When AC-05 removes those Copilot-literal constants, this test will fail. The implementer must update or supersede that test as part of this FR's scope.
- **Policy basis is sound:** `CLAUDE.md` states "CI rejects them" for all `Co-authored-by:` trailers; the local `block_ai_coauthor.py` hook intentionally allows human trailers as a softer gate. The CI is the hard gate; generalization is correct and consistent with documented intent.
- Scope is frozen as written. No further amendments required.

## Related

- GitHub issue #408: <https://github.com/sheikkinen/yamlgraph/issues/408>
- `.github/workflows/commitlint.yml` (`copilot-trailer-gate`)
- `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`
- `capabilities/CAP-148-ci-copilot-trailer-gate.yaml`
- `ARCHITECTURE.md` (REQ-YG-358)
- `CLAUDE.md` required checks section
- `scripts/block_ai_coauthor.py` (contrast: AI-pattern local hook, not CI policy source)
- Topic source requested: `.chaplain/processing/gh-408.md` (not present in this worktree)
