# Fix: No CI gate enforces diary file existence for feat/fix PRs

## Violation
All 5 most recent Inquisitor Audits (XXXVIII–XLII) identify the same structural root cause: nothing enforces that a diary reflection file *exists* before a PR merges. The consequence is a perpetual cycle of audit detection → remediation FR → new features ship without diaries → audit detection.

Key citations:
- **Audit XXXVIII:** "The `finalize_merge.sh` stub mechanism must cover *all* merged PRs — not just `feat` — to break this cycle"
- **Audit XXXIX:** "Three consecutive audits flagging the same omissions proves that detection without enforcement is ritual"
- **Audit XL:** "A diary gate — requiring `docs/diary/` modification on `feat`/`fix` PRs — would complete the Distill enforcement chain"
- **Audit XLI:** "FR-144's pre-commit hook enforces stub *content quality* but not stub *existence per FR*. This is the third audit cycle where missing reflections appear. The pattern is now structural, not accidental — detection without enforcement is ritual"
- **Audit XLII:** "Enforcement must be structural (CI gate) or the audit itself becomes the ritual it warns against"

Existing gates cover adjacent concerns but not this one:
- **FR-144** (implemented): Rejects unfilled diary stubs — enforces *content*, not *existence*
- **FR-149** (implemented): CI gate for CHANGELOG entries — the exact pattern to replicate
- **FR-131** (implemented): Commit-delta gate — prevents duplicate audits, not missing diaries

## Suggested Fix
**Classification:** Structural gap — requires a new Feature Request.

**FR outline:**
- **Title:** CI diary existence gate for feat/fix PRs
- **Type:** Enhancement
- **Priority:** HIGH (5 consecutive audits citing the gap; `audit_as_ritual` trap confirmed)
- **Approach:** Add a CI workflow job (mirror FR-149's CHANGELOG gate pattern) that:
  1. For PRs with `feat` or `fix` type (parsed from PR title), require at least one `docs/diary/*.md` file to be added or modified
  2. Use the same GitHub Actions check-run pattern as `commitlint` and `test` required status checks
  3. Allow `[skip-diary]` trailer for mechanical fixes where reflection has zero cognitive yield (with audit trail)
- **Acceptance criteria:**
  - CI blocks merge of `feat`/`fix` PRs lacking diary file changes
  - `docs`/`chore`/`test`/`ci` PRs are exempt
  - The gate integrates with existing branch protection (FR-150)
- **Risk:** Mechanizing reflection into checkbox compliance. Mitigate by combining with FR-144's content quality enforcement — the gate ensures a file exists, FR-144 ensures it has substance.
