## 2026-03-08: Implementation Reflection — FR-134 Diary Folder Refactor

Replaced the monolithic `docs/diary.md` (1582 lines, 89 entries) with a `docs/diary/` folder
of date-prefixed individual files. Five concurrent actors — `finalize_merge.sh`, `diary_rotate.py`,
`inquisitor.sh`, `examples/shared/diary.py`, and `diary_digest.sh` — now write separate files
instead of appending to a single shared file, eliminating the merge conflict that motivated this FR.

**Trap encountered:** `set -euo pipefail` + `ls glob* 2>/dev/null | sort` — when the glob matches
nothing, `ls` exits non-zero and `set -e` kills the pipeline despite `2>/dev/null`. The fix:
`$(ls glob* 2>/dev/null || true)` followed by a separate `sort -r | head -1` pipe. This pattern
appeared in both production shell scripts and test harnesses. The trap: stderr suppression is not
exit-code suppression.

**Insight:** Migration scripts should be idempotent and reversible. The `split_diary()` function
uses `---` separators and `## YYYY-MM-DD:` headers as entry boundaries — the same format all actors
produce. This means re-running migration is safe (duplicate detection via `used_names` dict).

**Seed:** Now that diary entries are individual files, could we add YAML frontmatter (type, fr, sha)
to enable structured queries without parsing markdown headers? A `diary index` CLI command could
build a queryable index from frontmatter.
