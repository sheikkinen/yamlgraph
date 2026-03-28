## 2026-03-28: Inquisitor Audit — Chaplain FR Pipeline & EXIF Extension

**Context:** Audited the 5 most recent commits on `main` (ec55e4a..551a837). Four are Chaplain-generated `docs(FR):` commits adding feature requests to the enforce pipeline (FR-203 through FR-205). One is a `chore(examples):` commit extending EXIF metadata in the image pipeline. The audit checks doctrine compliance against the Scripture's Commandments, ADR-001, and the Sermon.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits**: All 5 commits use valid `docs(FR):` or `chore(examples):` prefixes. No `feat`/`fix` type means no changelog or diary obligations triggered. Test modifications in 551a837 retain existing `@pytest.mark.req("REQ-YG-198")` tags.

2. ⚠ **DRIFT — FR Numbering Collisions**: FR-203 was double-assigned (already `FR-203-linter-e302-accept-state-key`, then `FR-203-five-whys-demo`). FR-204 similarly collided (`FR-204-fi-domain-crawl` then `FR-204-five-whys-demo`). Both were corrected in subsequent commits (five-whys→FR-204, fi-domain-crawl→FR-205), but git history retains the stale numbering commits. The Chaplain's auto-numbering lacks a collision check against existing FR files on disk.

3. ⚠ **DRIFT — No Co-authored-by Trailers**: None of the 5 commits carry a `Co-authored-by` trailer. Chaplain-generated commits are arguably machine-authored and may warrant a machine trailer for auditability. The `chore(examples)` commit (551a837) should have one if AI-assisted.

4. ✓ **COMPLIANT — No noqa Additions**: No new `# noqa` suppressions introduced in the diff.

5. ✓ **COMPLIANT — Diary Exists**: `2026-03-28-chaplain.md` covers FR-205's planning and judgment phases with a forward-looking Seed.

**Heuristic:** _Automate FR number assignment with a collision check_ — the Chaplain should scan existing `feature-requests/FR-NNN-*.md` files and pick `max(NNN) + 1` atomically, preventing the double-assignment pattern that required two corrective commits.

**Seed:** Should the Chaplain's `plan` graph include a pre-flight node that validates FR numbering, detects collisions, and aborts before committing — turning the current "commit then correct" pattern into "validate then commit"?
