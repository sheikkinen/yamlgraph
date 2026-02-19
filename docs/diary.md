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

**Seed:** What other manual rituals in the development process (e.g., changelog updates, FR status tracking, audit re-runs) have crossed the twice-done threshold and are ripe for pre-commit automation?

---

## 2026-02-19: Diary as Generative Tool — Adding the Seed

**Context:** The diary had two metacognitive elements per entry: **Trap** (backward-looking pattern recognition) and **Heuristic** (extracted rule to prevent recurrence). Both are reflective — they look at what happened and distill a lesson. Missing: a forward-looking generative element.

**The gap:** Reflection without generation is a closed loop. You learn from mistakes but don't create openings for new thinking. The diary captured *what went wrong* and *what to do differently*, but not *what to explore next*. Each entry ended with a period, not a question mark.

**The addition:** **Seed:** — a forward-looking question planted at the end of each entry. Named to evoke growth: a seed is small, specific, and may or may not germinate. Not every seed produces fruit, and that's fine. The point is to keep planting.

**Four touchpoints updated:**
1. Absolution hook (`.pre-commit-config.yaml`) — the Distill prompt agents see after every commit
2. Copilot instructions — conventions, Sermon of the Chaplain (Distill), Path of Implementation (Reflect)
3. Existing diary entry — retroactive Seed added to the rotation automation entry

**The trap I watched for:** **Over-formalization.** A question field could become performative — asking questions for the sake of the format rather than genuine curiosity. The guard: Seeds should be specific enough to act on. "How can we improve?" is not a Seed. "What other manual rituals have crossed the twice-done threshold?" is — it points to a concrete investigation.

**Heuristic:** A metacognitive tool needs both reflection (what happened) and generation (what could happen). Trap + Heuristic + Seed: backward pattern → forward rule → open question. The question is cheaper than the answer but more valuable than silence.

**Seed:** Could the Seeds themselves be harvested — periodically scanning diary entries for unanswered Seeds and surfacing them as a "question backlog" to revisit?
