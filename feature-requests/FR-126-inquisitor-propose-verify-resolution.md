# Feature Request: Inquisitor Propose Verifies Resolution Before Writing

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** ✅ Approved
**Effort:** 0.5 days
**Requested:** 2026-03-07

## Summary

The inquisitor `--propose` mode detects persistent `✗ VIOLATION` entries across consecutive diary audits but never verifies whether those violations still exist in the current project state. This produces stale proposals for issues already resolved.

## Value Statement

Operators stop receiving noise proposals for violations that were already fixed, making the chaplain inbox a reliable signal of genuine unresolved work.

## Problem

The propose logic (`.chaplain/inquisitor.sh` lines 54-78) follows a diary-only pipeline:

```
docs/diary.md (last 5 audits)
  → detect ✗ in ≥2 consecutive audits
  → write proposal to .chaplain/inbox/
```

It never consults the actual project state. Concrete failure mode:

1. Audit XVIII: `✗ FR-112 status is "Draft"`
2. Audit XIX: `✗ FR-112 status is "Draft"` — 2 consecutive, qualifies for proposal
3. Between audits: someone fixes FR-112 to Status: `Implemented`
4. Audit XX: violation absent (fixed)
5. `--propose` reads diary, sees persistence in XVIII+XIX, writes stale proposal

The only deduplication is filesystem-level (skip if same filename exists in inbox). There is no semantic check against the current codebase.

Evidence: `FR-123-fr112-status-fix.md` was created as a duplicate of the already-implemented `FR-120`, demonstrating this exact blind spot in practice.

## Proposed Solution

Add a **Step 2B — Verify resolution** to the propose prompt in `.chaplain/inquisitor.sh`, between "Detect persistence" (Step 2) and "Classify" (Step 3):

```
**Step 2B — Verify resolution:** For each persistent violation found in Step 2:
  - Check the current state of the artifact the violation references:
    - Feature request status fields: read the FR file, check if Status is now "Implemented" or "Rejected"
    - ARCHITECTURE.md counts/content: read the current file, verify the claimed discrepancy still exists
    - Missing entries (CHANGELOG, confessions, req tags): check if the entry now exists
    - Commit convention issues: check if a fixup commit corrected the message
  - If the violation is resolved in the current project state, discard it from the proposal list
  - Only violations confirmed as still-unresolved proceed to Step 3
```

The change is prompt-only — no new scripts, no structural changes. The copilot agent already has `--allow-all-paths --allow-all-tools`, so it can read any project file to verify.

### Design Consideration

FR-118 deliberately separated concerns: "Audit reads project → writes diary; Propose reads diary → writes inbox." This change relaxes the propose boundary by allowing it to also read project files for verification. This is justified because:

- The propose step already has full file access (`--allow-all-paths`)
- Verification is read-only — no writes outside `.chaplain/inbox/`
- The alternative (stale proposals) undermines the entire propose mechanism's value

## Acceptance Criteria

- [ ] Propose prompt includes a verification step that checks current project state before writing proposals
- [ ] Violations whose referenced artifact is now in a resolved state (Status: Implemented/Rejected, count corrected, entry added) are silently discarded
- [ ] Violations confirmed as still-unresolved continue to generate proposals as before
- [ ] The propose summary (Step 5) distinguishes between "X violations found, Y already resolved, Z proposals written"
- [ ] `tests/unit/test_inquisitor_auto_propose.py` extended with a test that asserts the propose prompt text includes Step 2B verification language (prompt content test, not copilot behavior test — ACs 2-3 are verified manually via the FR-123 scenario)
- [ ] No changes to the audit step (Step 1-4 of the audit prompt remain untouched)

## Judgement

**Verdict: APPROVE** — 2026-03-07

**Scope is clear and minimal.** Prompt-only change to `.chaplain/inquisitor.sh` lines 56-77 — insert Step 2B between existing Steps 2 and 3. No new scripts, no structural changes.

**Motivation is concrete.** FR-123 (rejected duplicate of FR-120) is direct evidence of the blind spot: propose reads diary history but never checks current project state, producing stale proposals for already-resolved violations.

**Architecture alignment is sound.** The FR correctly identifies and justifies the boundary relaxation from FR-118's "propose reads diary only" principle. Verification is read-only, the agent already has `--allow-all-paths`, and the alternative (stale proposals) undermines the inbox signal.

**Refinement applied (AC #5):** Original AC claimed unit tests for "resolved-violation filtering" — but filtering happens inside the copilot prompt, not in shell logic. The existing test pattern (shell snippet extraction) cannot exercise copilot prompt compliance. Rephrased to test prompt text content, with ACs 2-3 verified manually via the FR-123 reproduction scenario.

**Accepted risk:** False negatives (copilot misreads a file and discards a valid violation) are tolerable — the violation will reappear in the next audit cycle and re-qualify for proposal. The current failure mode (stale proposals) is strictly worse.

**Scope frozen. Authority granted.**

## Alternatives Considered

**Post-filter in watch.sh:** Validate proposals in the watch loop before processing. Rejected — inbox still gets polluted with stale files, and the watch loop would need domain logic about what "resolved" means for each violation type. Better to prevent stale proposals at the source.

**Document as known limitation:** Add a note to FR-118. Rejected — the blind spot already produced a concrete duplicate (FR-123). Documentation doesn't prevent operator toil.

**Separate verification script:** A new `.chaplain/verify-proposals.sh` that runs after propose. Rejected — adds another moving part. The copilot agent in propose mode already has the context and access to do this inline.

## Related

- `.chaplain/inquisitor.sh` — Script to modify (propose prompt, lines 56-77)
- `feature-requests/FR-076-chaplain-inquisitor.md` — Original inquisitor spec
- `feature-requests/FR-118-inquisitor-auto-propose.md` — Propose flag spec (design decision context)
- `feature-requests/FR-123-fr112-status-fix.md` — Concrete example of a stale proposal
- `tests/unit/test_inquisitor_auto_propose.py` — Tests to extend
- `docs/diary.md` — Data source for propose logic
