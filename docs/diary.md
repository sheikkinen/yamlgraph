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

**Seed:** Could the Seeds themselves be **harvested** — periodically scanning diary entries for unanswered Seeds and surfacing them as a "question backlog" to revisit?

---

## 2026-02-19: The Missing Input — When Metacognition Becomes Solipsism

**Context:** The diary now has Trap + Heuristic + Seed. Three elements, all internally generated. 18 entries across 3 days, zero external input. The diary is a mirror — it reflects what happened inside the project, but has no window to the outside world.

**The gap:** Seeds ask outward-facing questions ("What constraint replaces cost?", "Could protocol archaeology be formalized?", "What's agent↔environment?") but nothing brings answers back in. The process generates forward-looking questions but never checks if the world has already answered them.

**The existing infrastructure:** `examples/daily_digest/` is a working, deployed pipeline. 7 nodes: HN + RSS → filter → analyze (map) → rank → format → email. Runs daily via GitHub Action → Fly.io. Cost: ~$0.02/run. It fetches, analyzes, and delivers — but to an email inbox, about generic tech topics, disconnected from project context.

**The insight:** The daily_digest pipeline is 80% of what's needed. The missing 20% is **context-awareness** — connecting external developments to the project's active work, open Seeds, and in-progress FRs. A generic "AI news" digest is noise. A digest that says "LangGraph 1.1 released — relates to your FR-044a SkipReport work" is signal.

**What FR-046 proposes:** A `diary-digest` graph that reuses daily_digest's source fetching and content extraction, adds a `scan_context` node that reads open Seeds + active FRs from the workspace, and outputs a diary-formatted entry instead of HTML email. Schedulable via cron/launchd/GHA.

**The trap I watched for:** **Scope inflation from enthusiasm.** The first draft wanted real-time monitoring, semantic search over article archives, automated FR creation from news. Cut to: fetch → filter → analyze-in-context → write diary entry. The diary entry format constrains scope naturally — it's one entry per day, not a news dashboard.

**Heuristic:** A metacognitive tool that only looks inward eventually becomes a closed loop. Even a small, automated outside signal — "here's what changed in the world that relates to your open questions" — breaks the loop and connects reflection to reality.

**Seed:** If the diary-digest connects Seeds to external developments, could it also detect when a Seed has been *answered* — marking it as germinated when external evidence addresses the question it posed?

---

## 2026-02-19: Enforce — FR-046 Diary World Digest

TDD implementation of the diary-digest pipeline. The judgment cut 7 nodes to 4-5, replaced dynamic context scanning with a static `feeds.yaml`, and demanded no-op on zero-relevance days. Enforced by writing 15 tests first (RED) — all `@pytest.mark.req("REQ-YG-072")` — then implementing the minimal code to pass (GREEN).

**What was built:**
- `scripts/diary_digest_tools.py` — fetch_hn, fetch_rss, format_diary_entry, append_to_diary, should_write_entry
- `scripts/diary_digest.py` — CLI with `--dry-run` and `--commit`
- `feeds.yaml` — static feed config (5 RSS feeds, 10 topics)
- `examples/diary_digest/` — graph YAML + 2 prompts (analyze_relevance, synthesize_diary_entry)
- `scripts/com.yamlgraph.diary-digest.plist` — launchd scheduling at 06:00 daily
- 15 unit tests covering config, fetching, formatting, append, and no-op

**Trap:** The test assumed `format_diary_entry` output starts with the `##` header, but the separator (`\n---\n\n`) comes first. The separator test and header test contradicted each other. Fixed by changing the header assertion from `startswith` to `in`. The trap: testing format assumptions without first defining the canonical format — the separator is part of the entry, not a prefix.

**Heuristic:** When a formatting function serves dual purposes (standalone readability AND append-to-file behavior), test the structural invariants (`contains`) not positional invariants (`startswith`). The position depends on context; the content doesn't.

**Seed:** The CLI runner does LLM calls inline rather than through the graph YAML. Is this a pragmatic shortcut or a violation of the three-layer pattern — and when does a script graduate to a proper graph execution?

---

## 2026-02-19: The Seed That Answered Itself

**Context:** The previous entry's Seed asked: "Is the CLI runner a violation of the three-layer pattern?" Within minutes of writing it, the answer was obvious: yes. `scripts/diary_digest.py` called `execute_prompt()` inline — presentation layer doing logic layer's job. The Seed didn't need to germinate; it was already ripe.

**What changed:**
- Deleted `scripts/diary_digest.py` (CLI with inline LLM calls)
- Deleted `scripts/diary_digest_tools.py` (redundant re-export; user called it "entropy")
- Moved `feeds.yaml` → `examples/diary_digest/feeds.yaml`
- Split tools into `examples/diary_digest/nodes/sources.py` and `nodes/writing.py`
- Rewrote `graph.yaml` with 6 nodes: load_config → fetch_sources → analyze_all (map) → filter_relevant → synthesize_entry → write_diary
- Added conditional edge: `relevant_count == 0` routes to END (the no-op the Judgement demanded)
- Plist now runs `yamlgraph graph run examples/diary_digest/graph.yaml --var commit=true`

**Module resolution lesson:** Relative imports (`nodes.sources`) fail when CWD is project root because `python_tool.py` adds CWD to `sys.path`. Other example graphs use fully-qualified paths (`examples.diary_digest.nodes.sources`). The pattern was already established — I just hadn't looked.

**Trap:** **Tautological Seeds.** A Seed that asks whether existing code violates a known principle isn't generative — it's a deferred lint finding. The question already contained the answer. A better Seed would have asked something genuinely unknown: "What types of graph orchestration *can't* be expressed in YAML-only?" That requires discovery, not just inspection.

**Heuristic:** If a Seed can be answered by applying an existing rule to existing code, it's not a Seed — it's a TODO. Seeds should point to unexplored territory, not unchecked boxes.

**Seed:** The linter doesn't check `prompts_relative` inside `defaults:` — only at top level. If the linter and runtime disagree on config resolution, what other graph.yaml fields have silent linter blind spots?

---

## 2026-02-19: Phase 2 — Seed Curation and Single-Purpose Purge

Removed `dry_run` and `commit` from the diary-digest pipeline. `dry_run` was a string-truthy hack (`--var dry_run=true` passes "true", a truthy string — it worked by accident). `commit` was subprocess.run for git in a logic-layer function — a presentation concern baked into the pipeline. Both violated three-layer separation. Moved git ops to the plist shell command. Seeds field dropped from feeds.yaml (was `seeds: []`, dead code).

Then Phase 2: close the Seeds loop. 24 Seeds exist across diary files, planted by the development process but never read back. Added `extract_raw_seeds()` to regex-scan diary files for `**Seed:**` lines, `load_seeds/save_seeds` for seeds.yaml persistence, and wired a `curate_seeds` LLM node into the graph. Both paths (articles-found and no-op) converge on curation — Seeds change when diary changes, not when articles are relevant.

The judgement corrections were key: two state fields not four (avoid overlapping `current_seeds`/`curated_seeds`/`seeds` confusion), merge extraction into `load_config` (one tool, one node), plain list format for seeds.yaml (no `planted`/`source` metadata — the LLM judges staleness by content, not dates), cap at 10.

**Trap:** **Pre-commit hooks as hidden co-authors.** The vulture hook auto-modified 3 unrelated files during our commit — deleting Pydantic v1 `.dict()` shims and a dead `replicate_tool.py`. The commit message became misleading (our Phase 2 changes bundled with "remove Pydantic v1 shims"). The hook did the right thing (kill dead code), but the commit lost its story. Hooks that auto-modify files should be separated from hooks that validate — one commits truth, the other enforces it.

**Heuristic:** If a pre-commit hook modifies files, it changes the commit's narrative. Auto-fix hooks (formatting, dead code removal) should run in a dedicated pass, not mixed with feature commits.

**Seed:** The curate_seeds node receives all 24 raw Seeds every run and must decide which 10 to keep. But it has no memory of previous curation decisions — each run starts fresh. Could a diff-based approach (showing what changed since last curation) produce more stable, intentional evolution of the seed list?
