# Feature Request: FR-697 direct-to-main break-glass audit trail gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-07-07

## Summary

Add a deterministic break-glass ledger check for direct-to-main commits, plus a bounded retroactive ledger entry for the currently known undocumented bypass batch.

## Value Statement

Maintainers get machine-checkable evidence that each direct-to-main bypass was documented with rationale and corrective action.

## Problem

`reference/break-glass.md` requires post-facto bypass documentation, but no gate verifies compliance. The resulting gap is visible in current evidence:

1. `docs/diary/2026-05-30-inquisitor-audit-255.md` flags direct-to-main bypass drift.
2. `docs/diary/diary-2026-07-07-the-scribe-bypasses-the-scripture.md` confirms the bypass path is active and under-documented (474/568 direct commits since 2026-05-01, with explicit break-glass traceability concern).

Without a deterministic ledger check, bypass documentation remains advisory.

## Research Findings

1. **Required policy exists, enforcement does not.** `reference/break-glass.md` defines bypass procedure and audit expectations, but has no structured incident ledger and no parser-backed check.
2. **Reusable CI gate pattern exists.** `.github/workflows/commitlint.yml` jobs (`copilot-trailer-gate`, `author-identity-gate`, `wip-gate`) already run deterministic shell checks over git ranges.
3. **Reusable RED test pattern exists.** `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py` and `tests/unit/test_fr410_ci_author_identity_gate_red.py` execute workflow run scripts in temporary git repos and assert pass/fail semantics.
4. **Direct-push evidence topic file is absent in this worktree.** `.chaplain/processing/inquisitor-main-bypass.md` does not exist; this FR uses the two existing diary artifacts above plus current git history as canonical evidence.
5. **Traceability IDs are available.** `CAP-190` is unclaimed in `capabilities/`, and `REQ-YG-525` is unclaimed in `ARCHITECTURE.md` (nearest existing IDs include `REQ-YG-523`).
6. **Scope boundary:** this FR covers traceability for direct-to-main bypasses only. It does not modify branch protection settings or Inquisitor internals.

## Objectives

1. Make direct-to-main bypass documentation parseable and testable.
2. Close the known undocumented July 7 bypass batch with explicit SHA-level entries.
3. Add an advisory CI signal (`breakglass-gate`) that reports missing ledger entries.

## Constraints

1. Deterministic implementation only (git metadata + markdown parsing), no LLM logic.
2. Single responsibility: direct-push break-glass traceability.
3. Advisory/non-blocking CI status in this FR; blocking escalation is explicitly deferred.
4. No commit history rewrite.

## Proposed Solution

### 1. Retroactive remediation with explicit bounded baseline

Add a new `## Direct-to-main incident ledger` section to `reference/break-glass.md` and include one incident row for each commit in the bounded undocumented batch:

- `56230029` — `docs(process): add development process self-reflection overview`
- `caf14330` — `docs(diary): the scribe bypasses the scripture - process overview reflection`
- `2b265793` — `docs(process): reality check - manual plan-judge-enforce loop dominates (83% direct commits)`
- `b17a8b5e` — `docs(process): why manual ops dominate - latency, task-shape mismatch, transaction cost`

These four SHAs are the retroactive catch-up scope for this FR.

### 2. Pinned ledger format contract

The new ledger section must use this exact markdown table header:

```markdown
## Direct-to-main incident ledger

| sha | date | rationale | corrective_action | evidence |
| --- | --- | --- | --- | --- |
| 56230029 | 2026-07-07 | <why bypass was necessary> | <what prevents recurrence> | <diary/FR link> |
```

Contract rules:

1. Header names are exact and lowercase as shown.
2. `sha` is a short or full commit SHA present in `main` history.
3. `rationale`, `corrective_action`, and `evidence` must be non-empty.
4. `evidence` must include at least one path or `FR-` token.

### 3. Detection script

Add `scripts/check_direct_push_breakglass.py` that:

1. Enumerates commits in a supplied range (`--since-sha`, `--until-sha`, defaulting `--until-sha` to `HEAD`).
2. Parses the ledger table in `reference/break-glass.md`.
3. Fails when any commit in the supplied SHA range is missing from the ledger.
4. Fails when required ledger fields are blank.
5. Prints missing/invalid entries in a machine-readable summary.

### Detection algorithm

This FR adopts **Option C (Range = direct by maintainer assertion)** from Judge feedback.

Algorithm contract:

1. The commit set under validation is exactly the linear history in `--since-sha..--until-sha`.
2. For this FR baseline (`--since-sha 56230029`), maintainers assert this bounded range is the direct-to-main bypass batch requiring ledger coverage.
3. The script does **not** infer PR association from git topology and does **not** call GitHub APIs.
4. Because this FR keeps `breakglass-gate` advisory (`continue-on-error: true`), the asserted-range model is acceptable for initial rollout and can be tightened in a later FR.

### 4. CI advisory gate

Add `breakglass-gate` to `.github/workflows/commitlint.yml` (pull_request trigger) running:

```bash
python scripts/check_direct_push_breakglass.py --since-sha 56230029
```

Clarification: this gate runs on PR events and reports accumulated undocumented direct-to-main commits in the configured baseline window; it does not intercept a bypass at push time.

Set `continue-on-error: true` for this job in this FR so the signal is visible without blocking merge.

## Requirement Traceability Plan

1. Add capability file: `capabilities/CAP-190-breakglass-direct-push-gate.yaml` (proposed).
2. Add requirement: `REQ-YG-525` (proposed) to `ARCHITECTURE.md`.
3. Tag FR-specific tests with `@pytest.mark.req("REQ-YG-525")`.

## Acceptance Criteria

- [x] **AC-01:** `reference/break-glass.md` contains `## Direct-to-main incident ledger` with at least these SHAs: `56230029`, `caf14330`, `2b265793`, `b17a8b5e`.
- [x] **AC-02:** The ledger table header is exactly `| sha | date | rationale | corrective_action | evidence |`.
- [x] **AC-03:** `scripts/check_direct_push_breakglass.py` exits non-zero when any commit in the supplied SHA range is missing from the ledger.
- [x] **AC-04:** The script exits non-zero when a ledger row for an in-range commit has blank required fields (`rationale`, `corrective_action`, or `evidence`).
- [x] **AC-05:** The script exits zero when all commits in the supplied SHA range are present and required fields are populated.
- [x] **AC-06:** `.github/workflows/commitlint.yml` defines `breakglass-gate` that runs the script on pull_request and uses `--since-sha 56230029`.
- [x] **AC-07:** `breakglass-gate` is advisory/non-blocking (`continue-on-error: true`) in this FR.
- [x] **AC-08:** Traceability artifacts are updated for `CAP-190` and `REQ-YG-525`, and FR tests carry `@pytest.mark.req("REQ-YG-525")`.

## Failing Acceptance Tests (RED plan)

Create:

- `tests/unit/test_fr697_breakglass_direct_push_gate_red.py`

Planned RED tests:

1. `test_ac01_breakglass_ledger_contains_bounded_retroactive_sha_set`
2. `test_ac02_breakglass_ledger_header_matches_contract`
3. `test_ac03_script_fails_when_direct_commit_missing_from_ledger`
4. `test_ac04_script_fails_when_required_ledger_fields_are_blank`
5. `test_ac05_script_passes_when_ledger_covers_all_in_scope_direct_commits`
6. `test_ac06_commitlint_workflow_defines_breakglass_gate_with_since_sha_56230029`
7. `test_ac07_breakglass_gate_is_advisory_continue_on_error_true`
8. `test_ac08_traceability_artifacts_reference_req_yg_525`

RED command:

```bash
pytest tests/unit/test_fr697_breakglass_direct_push_gate_red.py -q --no-cov
```

## Alternatives Considered

1. **Diary-only documentation** — rejected; not a structured, parseable enforcement artifact.
2. **Inquisitor-only detection** — rejected; post-hoc audits do not provide CI signal.
3. **Immediate blocking gate** — rejected for this FR; advisory-first avoids merge disruption while baseline confidence is established.
4. **GitHub branch-protection redesign** — rejected; orthogonal to this FR's single responsibility.

## Out of Scope

1. Changing GitHub branch protection settings.
2. Replacing Inquisitor audit flow.
3. Rewriting historical commit topology.
4. Promoting `breakglass-gate` from advisory to blocking.

## Judge Notes

**2026-07-07 — AMEND**

**Issue 1 (Critical): Detection algorithm unspecified.**

The FR describes a script that "enumerates direct-to-main commits in a supplied range" but does not define the algorithm for distinguishing a direct push from a squash-merged PR. In this repository, squash merges produce single, non-merge commits that are visually identical to direct pushes in `git log --no-merges`. The script cannot infer bypass status from git topology alone.

This gap invalidates AC-03/AC-04/AC-05 as written: "in-scope direct commit" is undefined without a detection algorithm.

**Required resolution (choose one and document in the FR):**

- **Option A (Explicit list):** The script accepts an `--direct-shas` argument (or reads from a pinned file, e.g., `reference/break-glass-shas.txt`) listing known direct-push SHAs. The `--since-sha` range is used only as a bounding guard. This is deterministic and requires no GitHub API access.
- **Option B (GitHub API):** The script calls `gh api repos/.../commits/{sha}/pulls` to determine whether each commit in the range is associated with a merged PR. Commits with no associated PR are treated as direct pushes. Requires `GH_TOKEN` in CI.
- **Option C (Range = direct):** Document explicitly that `--since-sha 56230029` means "all commits in this range were direct pushes by author assertion." Acceptable for the advisory gate since the gate is non-blocking and the baseline is manually curated.

Option C has the lowest implementation cost and is consistent with the advisory-only constraint in this FR. If adopted, AC-03 must be rewritten as: "fails when any commit in the supplied SHA range is missing from the ledger" (removing the word "direct").

**Issue 2 (Minor): REQ-YG-525 and CAP-190 are proposed IDs — verify non-collision.**

The FR proposes `REQ-YG-525` and `CAP-190`. These must be confirmed available in `ARCHITECTURE.md` and `capabilities/` before tests are tagged.

**Directive:**

1. Resolve Issue 1 by adding a `### Detection algorithm` subsection to `### 3. Detection script` specifying the chosen option.
2. Update AC-03 to reflect the resolved algorithm.
3. Verify REQ-YG-525 and CAP-190 are unclaimed.
4. Then re-submit for Judge review.

**2026-07-07 — APPROVE**

Scope is clear and minimal. Single responsibility confirmed (direct-push break-glass traceability only). Detection algorithm is resolved (Option C: range = direct by maintainer assertion, documented in `### Detection algorithm`). All 8 ACs are measurable and map 1:1 to the 8 planned RED tests. Implementation follows established CI gate patterns (`copilot-trailer-gate`, `author-identity-gate`, `wip-gate`) — no novel abstractions introduced.

**One minor note (non-blocking):** `REQ-YG-525` skips over `REQ-YG-524`. Planner asserts both IDs are verified unclaimed. If `REQ-YG-524` is genuinely unclaimed, prefer using `REQ-YG-524` to preserve sequential order; if 524 is reserved by another in-flight FR, document that in the traceability section. Either is acceptable — the gate check will enforce whichever ID is registered.

**Authority granted.** Proceed with RED test file, then implementation.

**2026-07-07 — Planner response (AMEND applied)**

1. Added a `### Detection algorithm` subsection under `### 3. Detection script`.
2. Chosen approach: **Option C (Range = direct by maintainer assertion)** for advisory rollout.
3. Updated AC-03/AC-04/AC-05 wording to reference the supplied SHA range instead of inferred direct-commit detection.
4. Verified non-collision: `CAP-190` and `REQ-YG-525` are unclaimed in current `capabilities/` and `ARCHITECTURE.md`.

## Related

- `docs/diary/2026-05-30-inquisitor-audit-255.md`
- `docs/diary/diary-2026-07-07-the-scribe-bypasses-the-scripture.md`
- `reference/break-glass.md`
- `.github/workflows/commitlint.yml`
- `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`
- `tests/unit/test_fr410_ci_author_identity_gate_red.py`
- `feature-requests/FR-150-branch-protection-main.md`
- `feature-requests/FR-424-inquisitor-wip-main-gate.md`
