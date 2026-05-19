## 2026-05-19: Inquisitor Audit — FR-418/FR-416 compliance and gate bypass

**Context:** Audited the 5 most recent commits on `main` (71c89093..5e7d61b2, 2026-05-19) against the Scripture's Commandments, Sermon, and enforcement gates. Focus areas: Conventional Commits, changelog traceability, diary-gate, req tags, and branch protection.

**Findings:**

1. ✓ **COMPLIANT — FR-418 (feat, 71c89093):** Full doctrine compliance. Conventional Commits format with PR number. Changelog fragment has `req: REQ-YG-408`. REQ-YG-408 added to ARCHITECTURE.md and CAP-16. Tests tagged `@pytest.mark.req("REQ-YG-408")`. Diary entry with `Seed:` marker present. Exemplary.

2. ✗ **VIOLATION — FR-416 missing diary entry (fix, 8a731d71):** Commit is `fix(fsm): FR-416 ...` — a `fix` type with FR-XXX reference. The diary-gate requires a diary reflection in the diff for such PRs. No diary file for FR-416 exists. Gate was either bypassed or commit did not pass through a PR.

3. ✗ **VIOLATION — FR-416 no PR trace (8a731d71):** Commit message lacks the `(#NNN)` suffix that squash-merge adds. `gh pr list --search "FR-416" --state merged` returns empty. This commit appears to have been pushed directly to `main`, bypassing branch protection. No break-glass documentation found for this bypass.

4. ⚠ **DRIFT — FR-416 changelog missing `req:` front-matter:** The fragment body references `(REQ-YG-319)` but the YAML front-matter omits `req: REQ-YG-319`. The `changelog-req-gate` validates `req:` references when present but may not enforce their presence on `fix` types. Still, the asymmetry between body and front-matter is sloppy.

5. ✓ **COMPLIANT — chore/docs commits (77a14333, 4980a81f, 5e7d61b2):** All three follow Conventional Commits. `docs` and `chore` types correctly exempt from changelog, diary, and test gates. No scope creep.

**Heuristic:** Gate bypass without documentation is invisible drift. Each unrecorded bypass normalizes the next. The `fix` commit that skipped PR review and diary reflection produced correct code — but correctness is not compliance. The gates exist to prevent the *next* commit from being wrong, not this one.

**Seed:** Should the break-glass audit log be queryable by CI, so that any commit on `main` without a corresponding merged PR automatically triggers an Inquisitor alert — making invisible bypasses structurally impossible?
