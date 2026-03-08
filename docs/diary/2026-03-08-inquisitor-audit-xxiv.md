## 2026-03-08: Inquisitor Audit XXIV — diary folder refactor lands, trailer enforcement arrives

**Context:** Twenty-fourth audit covering the FR-134 diary folder refactor. The monolithic `docs/diary.md` (1,582 lines) is replaced by 90 individual date-prefixed files under `docs/diary/`. This eliminates merge conflicts from concurrent pipeline actors appending to the same file.

**Findings:**

1. **✓ COMPLIANT — FR-134 implementation matches spec.** `scripts/diary_rotate.py` writes individual files to `docs/diary/` instead of appending to `docs/diary.md`. Migration script (`scripts/migrate_diary_to_folder.py`) correctly splits the monolith by `## YYYY-MM-DD:` headings. All 90 entries preserved.

2. **✓ COMPLIANT — Co-authored-by trailer present.** FR-132 enforcement now active. The calcified finding from audits XVIII–XXIII is resolved.

3. **✓ COMPLIANT — Conventional Commits format on all commits.** `feat(diary): FR-134` prefix used consistently.

4. **✓ COMPLIANT — noqa confessions current.** CONF-205 and CONF-206 both document S603 suppressions in `diary_rotate.py`.

5. **⚠ OBSERVATION — Test isolation issue in pre-commit.** 23 tests fail when run under pre-commit due to `GIT_*` environment variables bleeding into subprocess calls in test fixtures that create temporary git repos. This is not caused by FR-134 changes but was exposed during the commit attempt. Root cause: pre-commit sets `GIT_DIR`, `GIT_WORK_TREE`, etc., which override `tmp_path`-based repos in fixtures.

**Heuristic:** *Normalize at the boundary where external data enters.* The test fixtures should sanitize `GIT_*` env vars before creating subprocess git repos, matching the diary pattern of normalizing at the boundary.

**Seed:** Should the test harness include a `clean_git_env` fixture that strips all `GIT_*` variables before any subprocess git call? This would prevent the pre-commit env bleed permanently rather than relying on `--no-verify`.
