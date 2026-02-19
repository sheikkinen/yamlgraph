# Feature Request: Diary World Digest — Outside Input for the Metacognitive Loop

**FR-046**
**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented (Phase 1 + Phase 2)
**Effort:** 2-3 days
**Requested:** 2026-02-19

## Summary

The development diary captures internal metacognition (traps, heuristics, seeds) but is blind to the outside world. A scheduled "world digest" pipeline would fetch relevant developments (AI frameworks, LangGraph, Python ecosystem, protocol standards) and append a diary entry summarizing what changed externally, connecting it to active work and open Seeds.

## Problem

The diary is a closed loop:
1. Work happens → trap/heuristic/seed captured → next work informed by past entries
2. But the **input** is always internal: what we did, what we learned, what we should try
3. Missing: **"what happened out there that matters to this project"**

Current blind spots:
- LangGraph releases (we're on 1.0.6 — are there breaking changes? new features that obsolete our workarounds?)
- Competitor frameworks (LlamaIndex Workflows, CrewAI, DSPy — are they solving problems we're solving?)
- LLM provider changes (new models, pricing shifts, capability jumps)
- Protocol developments (MCP spec updates, A2A spec changes — we researched these 2 days ago)
- Python ecosystem (Pydantic v3? new async patterns?)

The Seeds often point outward ("What's the third composition — agent↔environment?", "What constraint replaces cost?") but nothing brings outside answers back in.

## Proposed Solution

### Architecture: Reuse daily_digest, output to diary

```
┌──────────────────────┐     ┌───────────────────────────────────┐
│  Scheduler           │     │  diary-digest graph               │
│  (cron/launchd/GHA)  │────▶│                                   │
│  daily at 06:00      │     │  fetch_sources ─▶ filter_recent   │
└──────────────────────┘     │       ─▶ analyze_all (map)        │
                             │       ─▶ connect_to_project       │
                             │       ─▶ write_diary_entry        │
                             └───────────────────────────────────┘
```

### Key differences from daily_digest

| Aspect | daily_digest | diary-digest |
|--------|-------------|--------------|
| **Sources** | HN top stories | HN + targeted RSS (LangGraph blog, Python insider, Anthropic changelog, etc.) |
| **Topics** | User-configured | Auto-derived: YAMLGraph concepts + open Seeds |
| **Analysis** | Per-article relevance | Per-article relevance **+ connection to active work/seeds** |
| **Output** | HTML email | Markdown diary entry appended to `docs/diary.md` |
| **Delivery** | Resend API | `git add + commit` or file write for human review |
| **Scheduling** | GitHub Action → Fly.io | Local launchd/cron or GitHub Action |

### Graph definition (sketch)

```yaml
version: "1.0"
name: diary_digest
description: "Fetch world developments relevant to YAMLGraph, output as diary entry"

nodes:
  scan_context:
    type: python
    tool: scan_diary_context
    state_key: context
    # Reads: open Seeds, recent diary entries, active FRs, CHANGELOG.md
    # Produces: topics list + seed questions + active work summary

  fetch_sources:
    type: python
    tool: fetch_sources
    state_key: raw_articles
    # Reuse daily_digest sources.py, add targeted RSS feeds

  filter_recent:
    type: python
    tool: filter_recent
    state_key: filtered_articles

  fetch_content:
    type: python
    tool: fetch_content
    state_key: articles_with_content

  analyze_all:
    type: map
    over: "{state.articles_with_content}"
    as: article
    node:
      type: llm
      prompt: analyze_for_diary
      # "How does this article relate to YAMLGraph's active work and open Seeds?"
    collect: analyzed
    on_error: skip

  synthesize_entry:
    type: llm
    prompt: synthesize_diary_entry
    state_key: diary_entry
    # Produces markdown in diary format:
    # ## YYYY-MM-DD: World Digest — [Theme]
    # **External developments:**
    # - [Article] — relevance to [active work/seed]
    # **Seed connections:** which open Seeds have new evidence
    # **Seed:** forward-looking question from today's developments

  write_diary:
    type: python
    tool: append_to_diary
    state_key: written
    # Appends entry to docs/diary.md
    # Optionally: git add + commit
```

### Context-aware topics (the key differentiator)

The `scan_context` node reads:
1. **Open Seeds** — extracted from diary entries (regex: `**Seed:**`)
2. **Active FRs** — status != closed/rejected
3. **Recent diary entries** — last 3-5 entries for current focus
4. **CHANGELOG.md** — current version, recent changes

This produces a focused topic list like:
```
["LangGraph releases", "A2A protocol spec", "MCP updates",
 "LLM cost trends", "Python async patterns",
 "evaluation frameworks for LLM pipelines",
 "silent fallback detection patterns"]
```

Rather than the static `"AI,Python,LangGraph"` that daily_digest uses.

### Output format

```markdown
## 2026-02-19: World Digest — LangGraph 1.1 and A2A RC2

**What happened outside:**
- **LangGraph 1.1 released** — adds native `on_error` reporting (relates to FR-044a SkipReport)
- **A2A spec RC2** — JSON-RPC binding stabilized (connects to Seed #3, FR-045)
- **Anthropic Claude 4 announced** — 2x context, 50% cost reduction (validates Constraint Shift thesis)

**Seed connections:**
- Seed #16 (what constraint replaces cost?) — Claude 4 pricing suggests latency is next
- Seed #4 (semantic triage node?) — new structured output mode could enable this

**No action required** / **Consider:** [specific suggestion if warranted]

**Seed:** With LangGraph 1.1's native error reporting, does FR-044a become unnecessary — or does SkipReport still add value as a user-facing summary layer?
```

## Acceptance Criteria

- [ ] `scan_context` tool extracts open Seeds and active FR topics from workspace
- [ ] Sources include YAMLGraph-relevant RSS feeds (not just HN)
- [ ] Analysis prompt connects articles to active work, not just generic relevance
- [ ] Output is valid diary format (## YYYY-MM-DD: header, Seed at end)
- [ ] `--dry-run` mode prints entry without writing to diary
- [ ] Entry is appended to `docs/diary.md`, not replacing content
- [ ] Can run as: `python scripts/diary_digest.py` (local) or via scheduler
- [ ] Reuses daily_digest infrastructure (sources, filters) where possible
- [ ] Tests for context scanning and entry formatting

## Alternatives Considered

### A: Pure daily_digest with diary template
Just change the output format of daily_digest from HTML email to markdown. Simpler but loses the context-awareness (open Seeds, active FRs). The connection between external developments and internal work is the whole point.

### B: Manual "check the news" habit
No automation. Developer reads HN/RSS manually and writes diary entries. This is what's happening now (nothing) — the manual overhead means it doesn't happen. Automation makes it happen daily even when the developer is focused on implementation.

### C: GitHub Action only (no local)
Run only in CI, commit diary entry via GHA. Cleaner but adds CI dependency for a development tool. Local-first with optional GHA scheduling is more flexible.

### D: Separate file, not diary
Write to `docs/world-digest-YYYY-MM-DD.md` instead of the diary. Avoids diary pollution but loses the integration — the whole point is that external context lives alongside internal reflection. A separate file becomes another thing to check.

## Implementation Approach

### Phase 1: Core pipeline (1 day)
- `scripts/diary_digest.py` — CLI runner
- `scan_diary_context` tool — parse Seeds and FRs
- Reuse `daily_digest/nodes/sources.py` + `filters.py` + `content.py`
- New prompts: `analyze_for_diary.yaml`, `synthesize_diary_entry.yaml`
- `append_to_diary` tool — write to docs/diary.md
- Graph YAML

### Phase 2: Scheduling (0.5 day)
- **macOS local:** `launchd` plist for daily run
  - Plist at `~/Library/LaunchAgents/com.yamlgraph.diary-digest.plist`
  - Runs `python scripts/diary_digest.py` at 06:00 daily
  - Uses `StandardOutPath`/`StandardErrorPath` for logging
  - `launchctl load/unload` for install/remove
  - See: [reference/scheduling-agents.md](../reference/scheduling-agents.md)
- **CI alternative:** GitHub Action cron → commit diary entry
- `--dry-run` and `--commit` flags

### Phase 3: Seed tracking (0.5 day)
- Seed extractor that scans all diary files
- "Seed connections" section in digest entry
- Track which Seeds have received external evidence

## Related

- `examples/daily_digest/` — source pipeline to reuse
- `scripts/diary_rotate.py` — diary lifecycle automation
- `docs/diary.md` — target output location
- FR-043 (evaluation framework) — the digest could surface evaluation research
- FR-045 (A2A protocol) — digest would track spec evolution
- Seed #16: "What constraint replaces cost as it approaches zero?"
- Seed #2: "Could protocol archaeology be formalized as a graph?"

## Risk Assessment

**Low risk:**
- Reuses proven infrastructure (daily_digest is deployed and working)
- Output is append-only to diary (no destructive operations)
- `--dry-run` prevents accidental writes

**Medium risk:**
- Noise: HN stories may be irrelevant most days → empty digest
  - Mitigation: relevance threshold; skip entry if no articles score above 0.7
- Staleness: RSS feeds change URLs, APIs change
  - Mitigation: graceful degradation per source (same as daily_digest)

**Not a risk:**
- Cost: ~$0.02/run (Claude Haiku for analysis + synthesis)
- Complexity: 6-node graph, 2 new prompts, 1 new Python tool, rest is reuse

---

## Judgment

**Date:** 2026-02-19
**Verdict:** APPROVED with scope reduction — Phase 1 only, defer Phases 2-3

### What's right

1. **The problem is real.** 20 diary entries, zero external input. The Seeds point outward but nothing comes back in. This is a genuine gap in the metacognitive loop.
2. **Reuse is genuine.** `daily_digest/nodes/sources.py` (HN + RSS), `filters.py` (SQLite dedup), `content.py` (article extraction) are tested, deployed code. Not reinventing.
3. **Output to diary, not email.** Correct decision. The diary is the single pane of glass — a separate file would be ignored (Alternative D is correctly rejected).
4. **Relevance threshold.** "Skip entry if no articles score above 0.7" is essential. Most days HN has nothing project-relevant. Silent no-op is correct.

### What needs correction

**1. "Auto-derived topics from Seeds" is over-engineered.**

The FR claims `scan_context` should parse Seeds, FRs, CHANGELOG, and recent diary entries to produce dynamic topics. But:
- There are 18 Seeds. They change weekly, not daily.
- Active FRs change even less frequently.
- The LLM analysis already receives the context — it doesn't need pre-computed topic keywords.

**Correction:** Replace `scan_context` with a simpler approach: a static `topics.yaml` file listing project-relevant topics and RSS feeds, manually updated when focus shifts. The LLM synthesis prompt can receive the last 3 Seeds directly as context. Dynamic topic extraction is Phase 3 at earliest — not Phase 1.

**2. The graph has too many nodes.**

7 nodes is the full daily_digest pipeline replicated. But the diary-digest doesn't need:
- `filter_recent` with SQLite dedup — the digest runs once/day, not repeatedly. A simple "last 24h" filter suffices without persistent dedup.
- `fetch_content` for all articles — most HN articles are behind paywalls or irrelevant. Fetch content only for articles that pass a title-based relevance pre-filter.

**Correction:** Simplify to 4-5 nodes:
1. `fetch_sources` — HN + targeted RSS (reuse)
2. `analyze_all` (map) — title+URL only, score relevance (cheap, fast)
3. `fetch_relevant_content` — fetch full text only for articles scoring > 0.5
4. `synthesize_entry` — produce diary entry from relevant articles + Seeds context
5. `write_diary` — append to diary.md

This halves the API calls on irrelevant-content days.

**3. Phase 2 (scheduling) should be Phase 1.**

The whole point is that this runs automatically. A script that requires manual invocation will be forgotten — that's Alternative B (manual habit), which the FR correctly rejects. The launchd plist is trivial (template already exists in `reference/scheduling-agents.md`). Ship it with the pipeline, not as a separate phase.

**Correction:** Merge scheduling into Phase 1. The plist is 20 lines of XML, not a separate work item.

**4. Phase 3 (Seed tracking) is premature.**

Tracking which Seeds have "received external evidence" requires semantic matching between article content and open-ended questions. This is an evaluation problem (FR-043 territory). The diary entry can mention Seeds manually in the synthesis prompt without building a tracking system.

**Correction:** Defer Phase 3 entirely. The synthesis prompt should say "Here are the 3 most recent Seeds — if any article connects to them, mention it." No tracking infrastructure needed.

**5. "Reuse daily_digest infrastructure" means import coupling.**

`daily_digest/nodes/sources.py` hardcodes `RSS_FEEDS = ["https://lobste.rs/rss", "https://dev.to/feed"]`. These are generic tech news, not project-relevant. The diary-digest needs different feeds (LangGraph changelog, Anthropic blog, Python releases).

**Correction:** Don't import `sources.py` directly. Copy the `fetch_hn()` and `fetch_rss()` functions (they're 30 lines each) into the diary-digest's own tool module. Use a `feeds.yaml` config for RSS URLs. Coupling to daily_digest's feed list is wrong.

**6. Missing: what happens when there's nothing relevant?**

The FR mentions a relevance threshold but doesn't define the behavior. If 0 articles pass the threshold, what happens? An empty diary entry is worse than no entry.

**Correction:** Add explicit acceptance criterion: "If no articles score above relevance threshold, no diary entry is written and the run logs 'No relevant developments today.'"

### Revised scope — Phase 1 (approved)

| Component | Description |
|-----------|-------------|
| `scripts/diary_digest.py` | CLI runner with `--dry-run` and `--commit` flags |
| `scripts/diary_digest_tools.py` | `fetch_sources()`, `fetch_rss()`, `append_to_diary()` |
| `feeds.yaml` | RSS feed URLs + static topic list |
| Graph YAML | 4-5 nodes: fetch → analyze (map, title-only) → fetch relevant content → synthesize → write |
| 2 prompts | `analyze_relevance.yaml`, `synthesize_diary_entry.yaml` |
| launchd plist | `com.yamlgraph.diary-digest.plist` shipped in `scripts/` |
| Tests | Context scanning, entry formatting, no-relevant-articles no-op |

**Effort:** 1 day (down from 2-3 days)

### Deferred

| Item | Trigger to revisit |
|------|-------------------|
| Dynamic topic extraction from Seeds/FRs | After 2+ weeks of manual `feeds.yaml` updates |
| Seed tracking ("germinated" status) | When FR-043 evaluation framework exists |
| GitHub Action alternative | When/if local launchd proves insufficient |
| SQLite dedup | If duplicate entries actually appear (unlikely at 1x/day cadence) |

### Revised acceptance criteria

- [x] Fetches HN + configured RSS feeds
- [x] Scores articles by relevance to configured topics (title-based, map node)
- [ ] ~~Fetches full content only for articles above relevance threshold~~ (dropped — title-only scoring is sufficient and cheaper)
- [x] Produces diary-format entry with `## YYYY-MM-DD: World Digest` header and Seed
- [x] No entry written if no articles pass threshold (silent no-op)
- [x] ~~`--dry-run` prints entry to stdout without writing~~ (removed — single-purpose pipeline always writes)
- [x] ~~`--commit` stages and commits the diary entry~~ (moved to plist shell command — presentation layer concern)
- [x] launchd plist included for macOS scheduling
- [x] Tests for entry formatting and no-op behavior

### Phase 1 implementation notes

Implemented and committed (`31f8d3c` through `f9790bf`). Key deviations from judgment:
- No CLI script — `yamlgraph graph run` is the runner (three-layer compliance)
- No `dry_run` / `commit` flags — pipeline is single-purpose (write entry). Git commit moved to plist shell command.
- CONF-206/207 (subprocess noqa) eliminated by removing git operations from write_diary
- Seeds field removed from feeds.yaml — currently `seeds: []` was never populated. Phase 2 addresses this.

---

## Phase 2: Seed Curation via LLM

### Problem

The synthesis prompt receives `{state.seeds}` to connect articles to open questions, but `load_config` returns `seeds: []` because feeds.yaml no longer has a seeds key and nobody maintained it manually. There are 24 Seeds across 3 diary files — real questions planted by the development process — but they're trapped in prose, never read back.

The naive fix (regex extraction) gives you all 24 Seeds. But Seeds age: some are answered, some are superseded, some are too vague to act on. What's needed is **curation** — an LLM that reads the raw Seeds, the current curated list, and today's diary activity, then produces an updated, focused set.

### Proposed: `curate_seeds` node in the diary-digest graph

Add a terminal node after `write_diary`. The graph becomes:

```
load_config → fetch_sources → analyze_all (map) → filter_relevant
    → [relevant_count > 0] → synthesize_entry → write_diary → curate_seeds
    → [relevant_count == 0] → curate_seeds
```

The `curate_seeds` node runs on **every** execution, even no-op days (when no articles are relevant). Seed curation is independent of article relevance — a new diary entry from a manual session could have planted new Seeds.

#### Components

| Component | Type | Description |
|-----------|------|-------------|
| `load_seeds` | Python tool | Read `examples/diary_digest/seeds.yaml`, return list. Create file if missing. |
| `extract_raw_seeds` | Python tool | Regex scan `docs/diary*.md` for `**Seed:**` lines. Return all raw seeds. |
| `curate_seeds` | LLM node | Inputs: current seeds file, raw seeds from diary, today's date. Output: updated curated list. |
| `save_seeds` | Python tool | Write curated list back to `seeds.yaml`. |
| `prompts/curate_seeds.yaml` | Prompt | Instructions for curation: add new, retire answered, condense related. |

#### seeds.yaml format

```yaml
# Auto-curated by diary-digest pipeline. Do not edit manually.
# Last updated: 2026-02-19
seeds:
  - question: "What constraint replaces cost as it approaches zero?"
    planted: 2026-02-17
    source: diary-2026-02-17.md
  - question: "Could protocol archaeology be formalized as a graph?"
    planted: 2026-02-17
    source: diary-2026-02-17.md
  - question: "What other graph.yaml fields have silent linter blind spots?"
    planted: 2026-02-19
    source: diary.md
```

#### Curation prompt behavior

The LLM receives:
1. **Current curated seeds** (from seeds.yaml, may be empty on first run)
2. **All raw seeds** (regex-extracted from diary files)
3. **Today's date** (for aging context)

Instructions:
- **Add** any raw seed not already in the curated list
- **Retire** seeds that have been answered by subsequent diary entries or are > 30 days old without activity
- **Condense** seeds that ask the same underlying question into a single sharper formulation
- **Cap at 10** — forces prioritization, prevents unbounded growth
- Output the curated list as structured data (Pydantic schema)

#### State changes

New state fields: `current_seeds`, `raw_seeds`, `curated_seeds`
`load_config` continues to populate `seeds` from `seeds.yaml` (for the synthesis prompt).
After curation, `save_seeds` writes the updated list back.

### Acceptance criteria

- [x] `seeds.yaml` created automatically on first run (load_seeds returns [] if missing)
- [x] Raw seeds extracted from all `docs/diary*.md` files via regex (`extract_raw_seeds`)
- [x] LLM curates: adds new, retires old, condenses duplicates (`curate_seeds` node + prompt)
- [x] Curated list capped at 10 seeds (prompt instruction + schema)
- [x] `seeds.yaml` written back after curation (`save_seeds_tool`)
- [x] `load_config` reads seeds from `seeds.yaml` for synthesis prompt
- [x] `curate_seeds` runs even on no-op days (both graph paths converge on curate_seeds)
- [x] Tests for extract_raw_seeds, load_seeds, save_seeds (9 new tests, 27 total)

### Effort

0.5 day — 2 Python tools (~30 lines each), 1 prompt, graph edges, 3-4 tests.

---

## Phase 2 Judgment

**Date:** 2026-02-19
**Verdict:** APPROVED with corrections

### What's right

1. **The problem is real.** `seeds: []` is dead code — the synthesis prompt asks about Seeds but receives nothing. 24 Seeds exist in diary files, never read back. The loop is broken.
2. **LLM curation over regex extraction.** Raw extraction gives 24 Seeds including stale, vague, and answered ones. An LLM can reduce to a focused 10. This is the right tool for the job — it's a judgment call, not a filter.
3. **Running on every execution.** Seeds change when diary changes, not when articles are relevant. Correct to decouple from the article-relevance conditional.
4. **Cap at 10.** Forces prioritization. Without a cap, the list grows monotonically and the synthesis prompt drowns in context.

### What needs correction

**1. Too many new state fields.**

`current_seeds`, `raw_seeds`, `curated_seeds` plus the existing `seeds` — four overlapping lists. The graph state becomes confusing.

**Correction:** Use two fields only:
- `seeds` — loaded from seeds.yaml by `load_config` (already exists, used by synthesis prompt)
- `raw_seeds` — extracted from diary files by `extract_raw_seeds`

The curate_seeds LLM node receives both and outputs directly to `seeds` (overwriting). The `save_seeds` tool reads `state.seeds` and writes to file. No `curated_seeds` field needed.

**2. `load_seeds` and `extract_raw_seeds` should be one tool.**

Two separate tools that both run at startup, both reading files, both populating state. This is two nodes for one logical step.

**Correction:** Merge into `load_config`. It already reads feeds.yaml — extend it to also:
- Read seeds.yaml (if exists) → `seeds`
- Regex-extract from diary files → `raw_seeds`

One tool, one node, two state fields populated.

**3. `save_seeds` is trivial — inline it in `curate_seeds`.**

A 5-line function that writes YAML to a file doesn't need its own tool definition and graph node. The `curate_seeds` Python wrapper can write the file directly after receiving the LLM output.

**Correction:** The curation flow is two nodes, not four:
1. **`curate_seeds` (LLM)** — receives `seeds` + `raw_seeds` + `date`, outputs curated list
2. **`save_seeds` (Python)** — writes to seeds.yaml

Actually, even simpler: make `curate_seeds` a Python tool that:
1. Calls execute_prompt internally? **No** — that violates three-layer. The LLM call must be in the graph YAML.

Keep it as: LLM node `curate_seeds` → Python tool `save_seeds`. Two nodes. The save is trivial but it's a side effect — it belongs in a Python tool, not hidden in an LLM node's post-processing.

**4. seeds.yaml schema is overspecified.**

`planted`, `source` metadata per seed adds complexity for negligible value. The LLM doesn't need to know which file a seed came from — it needs the question text. The 30-day retirement rule based on `planted` date is arbitrary and fragile.

**Correction:** Simple format:
```yaml
# Auto-curated by diary-digest. Do not edit manually.
# Last updated: 2026-02-19
- "What constraint replaces cost as it approaches zero?"
- "Could protocol archaeology be formalized as a graph?"
- "What other graph.yaml fields have silent linter blind spots?"
```

Plain list of strings. The LLM decides what's stale based on content, not dates.

### Revised Phase 2 scope

| Component | Description |
|-----------|-------------|
| `load_config` (modify) | Also reads `seeds.yaml` → `seeds`, regex-extracts diary `**Seed:**` lines → `raw_seeds` |
| `curate_seeds` LLM node | Prompt: current seeds + raw seeds → curated list (max 10). Schema: `CuratedSeeds(seeds: list[str])` |
| `save_seeds` Python tool | Writes `state.curated_seeds` to `seeds.yaml` |
| `prompts/curate_seeds.yaml` | Curation instructions |
| Graph edges | `write_diary → curate_seeds → save_seeds → END` + `filter_relevant → curate_seeds` (no-op path) |
| Tests | extract_raw_seeds, seeds.yaml read/write, cap enforcement |

**Effort:** 0.5 day
