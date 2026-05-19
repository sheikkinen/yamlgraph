## 2026-05-19: Inquisitor Audit — FR-419/FR-416 direct-push pattern and req frontmatter drift

**Context:** Audited the 5 most recent commits on `main` (77a14333..b925bff9, 2026-05-19) against the Scripture. This audit follows audit-235, which flagged FR-416 commit 8a731d71 for bypassing branch protection. Two new commits have landed since: b925bff9 (FR-419) and 17da4033 (FR-416 follow-up).

**Findings:**

1. ✗ **VIOLATION — FR-419 direct push (b925bff9):** `fix(fsm): FR-419 kill _translate_legacy_config` lacks the `(#NNN)` squash-merge suffix. No matching PR found via `gh pr list`. The commit modifies production code (`yamlgraph/utils/fsm/action.py`), tests, and changelog — a substantive change that bypassed PR review, diary-gate, and changelog-req-gate enforcement. No break-glass entry documents this bypass. The diary *does* exist but was never validated by CI.

2. ✗ **VIOLATION — FR-416 repeat direct push (17da4033):** Second FR-416 commit pushed directly to `main` after audit-235 already flagged the first (8a731d71). No PR, no diary entry. The `diary-gate` requires a reflection for `fix` PRs with `FR-XXX` reference — this gate was structurally bypassed by not creating a PR at all.

3. ✓ **COMPLIANT — FR-418 full doctrine (71c89093):** Conventional Commits with PR `(#419)`. Changelog fragment with `req: REQ-YG-408`. Tests tagged `@pytest.mark.req("REQ-YG-408")`. Diary with `Seed:` marker. REQ added to ARCHITECTURE.md. Exemplary.

4. ⚠ **DRIFT — req frontmatter omitted on fix changelogs:** FR-419 and both FR-416 changelog fragments omit `req:` in YAML frontmatter despite tests referencing REQ-YG-319. The `changelog-req-gate` only validates `req:` when present — it does not enforce presence. This is the same drift pattern noted in audit-235 finding #4, now across three fragments. Pattern is calcifying.

5. ✓ **COMPLIANT — docs/research commit (77a14333):** `docs(research): context helpers survey` — `docs` type correctly exempt from changelog, diary, and test gates.

**Heuristic:** Direct push is the universal gate bypass. Every CI gate — diary-gate, changelog-req-gate, commitlint, conflict-check — assumes code arrives via PR. When commits reach `main` without a PR, *all* gates are simultaneously defeated. The gates are not independently weak; they share a single point of failure: the assumption that branch protection is inviolate. Audit-235 flagged this for FR-416; FR-419 repeated it. The pattern is no longer a one-off — it is a habit.

**Seed:** Can a post-push hook on `main` enumerate commits without a merged PR reference and automatically open an Inquisitor issue — converting invisible bypasses into visible audit debt that blocks the next release?
