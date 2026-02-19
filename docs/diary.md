# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-18.md](diary-2026-02-18.md) — 5 entries from 2026-02-18.

---

## 2026-02-19: Diary Rotation Automation

**Context:** Manual diary rotation (mv + create) done twice. Automated via `scripts/diary_rotate.py` + pre-commit hook.

**What it does:** On each commit, checks if the latest `## YYYY-MM-DD:` entry in `docs/diary.md` is before today. If so: moves diary to `docs/diary-{date}.md` (with `-N` suffix if collision), creates fresh diary with Previous link, stages both files.

**The design decisions:**
- Pre-commit hook, not cron — rotation happens at the natural boundary (first commit of a new day)
- Archives by latest entry date, not by rotation date — the file name reflects what's inside
- `-N` suffix for collisions — if `diary-2026-02-18.md` already exists (from manual rotation), it creates `diary-2026-02-18-1.md` instead of overwriting
- Idempotent — fresh diary with no dated entries → no-op. Same-day entries → no-op
- `git add` built in — the rotation is included in the commit that triggered it

**Heuristic:** Automate the thing you've done manually twice. Once is a task, twice is a pattern, three times is a process that should be scripted.
