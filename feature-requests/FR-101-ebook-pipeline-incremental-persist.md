# Feature Request: FR-101 eBook Pipeline Iteration — Incremental Persist + Chapter-Level Judge

**Priority:** HIGH
**Type:** Improvement
**Status:** Superseded
**Superseded-by:** FR-103
**Verdict:** AMEND → AUTHORITY GRANTED → SUPERSEDED
**Judged:** 2026-02-25
**Amended:** 2026-02-25
**Effort:** 2.5 hours
**Requested:** 2026-02-25
**Depends-on:** FR-100

## Summary

Revise the eBook authoring pipeline (`examples/ebook/graph.yaml`) to persist outputs at each stage and introduce chapter-level judge+amend cycles. The current pipeline stores all intermediate state in memory and only writes files at the end — if the pipeline fails before `write_chapters`, all work is lost. Additionally, the single judge at the end found major hallucination issues (fabricated Commandments) that could have been caught and corrected per-chapter.

## Problem

The FR-100 pipeline run revealed two critical design flaws:

1. **Late persistence:** All 6 chapters are held in state until `write_chapters` runs at the end. ~15 minutes of copilot+LLM work is lost if the pipeline fails.

2. **Late judgment:** The single `judge_draft` node at the end found that Ch01 (Doctrine) had 9/10 Commandments fabricated. By the time this was discovered, all chapters were already written. A per-chapter judge could have caught and fixed this immediately.

3. **Missing file context:** Writing prompts told the LLM to use research but didn't provide explicit file listings, leading to hallucination instead of verbatim quoting.

## Proposed Solution (Amended)

> **Amendment rationale:** Original proposal was over-engineered (32 nodes, 24 persist points).
> The judgment identified that the root cause is **prompt quality**, not infrastructure.
> This amended solution focuses on the primary fix with minimal node changes.

### Root Cause: Missing Verbatim Content in Prompts

The fabrication happened because:
1. Research prompts returned *conclusions* and *summaries* instead of verbatim quotes
2. Write prompts asked LLM to "use the research" without explicit source text
3. LLM then invented content when asked to elaborate on summaries

### Primary Fix: Prompt Quality

**Research prompts** must output verbatim quotes with citations:
```yaml
schema:
  name: ChapterResearch
  fields:
    summary: {type: str, description: "Brief summary of findings"}
    verbatim_quotes:
      type: list[str]
      description: "EXACT text from source files, with file:line citations"
    source_files:
      type: list[str]
      description: "Files actually read"
```

**Write prompts** must include anti-hallucination directive:
```yaml
user: |
  ## CRITICAL: Do Not Invent
  - Quote Commandments, Prayers, and doctrine EXACTLY as found in research
  - If the exact text is not in the research, write: "[Not found in research]"
  - NEVER paraphrase doctrinal content

  ## Verbatim Quotes from Research
  {% for quote in verbatim_quotes %}
  {{ quote }}
  {% endfor %}
```

### Simplified Node Pattern (per chapter)

Replace the current `research → write` pairs with a 3-step pattern:

```
research_<chapter> (copilot)
    ↓
write_<chapter> (LLM with inline validation)
    ↓
persist_<chapter> (tool) → writes to docs/ebook/<chapter>.md
```

**Key insight:** The judge doesn't need a separate copilot node. Add inline validation
to the write prompt: the LLM self-checks against verbatim_quotes before output.

### Persistence Strategy (Simplified)

Write once per chapter, immediately after the write node:

```
docs/ebook/
  00-introduction.md          # Written by persist_introduction
  01-doctrine.md              # Written by persist_doctrine
  ...                         # Each persist node writes one file
```

No `.drafts/` directory — state is in LangGraph checkpoints. Persistence is for
resumability via `skip_if_exists: true`.

### Key Files Context in Prompts

Each research prompt should explicitly list the files it must read. Each writing prompt should include this context so the LLM knows what sources are authoritative:

**Chapter 00 — Introduction:**
- `README.md` — Project overview
- `ARCHITECTURE.md` — Design philosophy
- `CLAUDE.md` — Development process
- `.github/copilot-instructions.md` — The Scripture

**Chapter 01 — Doctrine:**
- `.github/copilot-instructions.md` — **Primary source** (10 Commandments, Sermon, Rite, Prayer)
- `CLAUDE.md` — Development commands
- `docs/confessions.md` — noqa pattern example

**Chapter 02 — Pre-commit Gates:**
- `.pre-commit-config.yaml` — **Primary source** (all hook definitions)
- `scripts/absolution.py`
- `scripts/req_coverage.py`
- `scripts/noqa_confession.py`
- `scripts/diary_rotate.py`

**Chapter 03 — Chaplain Pipeline:**
- `.chaplain/watch.sh` — Watch loop script
- `examples/copilot/graph.yaml` — **Primary source** (Plan→Judge→Summarize→Write)
- `examples/copilot/prompts/*.yaml` — Stage prompts
- `examples/shared/diary.py` — write_diary tool

**Chapter 04 — Inquisitor:**
- `.chaplain/inquisitor.sh` — Audit script
- `.pre-commit-config.yaml` — post-commit hook definition
- `docs/diary.md` — Sample audit entries

**Chapter 05 — Diary System:**
- `docs/diary.md` — **Primary source** (schema, examples)
- `scripts/diary_rotate.py` — Rotation logic
- `examples/diary_digest/graph.yaml` — Digest pipeline
- `examples/shared/diary.py` — Entry format

### Graph Structure (Simplified)

```yaml
# 19 nodes total: 6 chapters × 3 nodes + START
nodes:
  # Pattern repeats for each chapter
  research_introduction:
    type: copilot
    prompt: source/introduction
    state_key: research_introduction

  write_introduction:
    type: llm
    prompt: write/introduction
    variables:
      research: "{state.research_introduction}"
      verbatim_quotes: "{state.research_introduction.verbatim_quotes}"
    state_key: chapter_introduction

  persist_introduction:
    type: tool
    tool: persist_chapter
    variables:
      content: "{state.chapter_introduction}"
      filename: "00-introduction.md"
    skip_if_exists: true

edges:
  - from: START
    to: research_introduction
  - from: research_introduction
    to: write_introduction
  - from: write_introduction
    to: persist_introduction
  - from: persist_introduction
    to: research_doctrine
  # ... pattern continues for all 6 chapters ...
  - from: persist_diary
    to: END
```

## Acceptance Criteria (Amended)

### Prompt Quality (Primary Fix)
- [ ] All 6 research prompts include `verbatim_quotes: list[str]` in schema
- [ ] All 6 research prompts list specific files to read (per chapter file map above)
- [ ] All 6 write prompts include anti-hallucination directive
- [ ] Write prompts render `verbatim_quotes` with Jinja2 loop

### Per-Chapter Persistence
- [ ] `persist_chapter` tool created in `examples/ebook/nodes/`
- [ ] 6 persist nodes in graph (one per chapter)
- [ ] `skip_if_exists: true` on persist nodes for resumability
- [ ] Total node count ≤20

### Inline Validation
- [ ] Write prompts include self-check instruction: "Verify all doctrine text matches verbatim_quotes"
- [ ] Schema includes `validation_notes: str` field for self-reported issues

### Testing
- [ ] Unit test for `persist_chapter` tool
- [ ] Run Ch01 Doctrine in isolation and verify Commandments match source

## Implementation Approach (Amended)

### Phase 1 — Prompt Quality Fix (30 min)
1. Add `verbatim_quotes: list[str]` to all 6 research prompt schemas
2. Add `source_files: list[str]` to research schemas
3. Add anti-hallucination directive to all 6 write prompts
4. Add Jinja2 loop to render verbatim_quotes in write prompts

### Phase 2 — Persist Tool + Graph (1.5 hours)
1. Create `persist_chapter` tool in `examples/ebook/nodes/writing.py`
2. Add 6 persist nodes to graph (one per chapter)
3. Rewire edges: research → write → persist → next_research
4. Add `skip_if_exists: true` to persist nodes
5. Validate with `yamlgraph graph lint`

### Phase 3 — Test Run (30 min)
1. Run Ch01 Doctrine in isolation
2. Verify Commandments match `.github/copilot-instructions.md` exactly
3. If pass, run full pipeline

**Total: ~2.5 hours**

## Related

- FR-100: Initial eBook pipeline scaffold
- `.chaplain/watch.sh`: Example of per-stage persistence pattern
- Judge findings from FR-100 run: `/tmp/ebook_run.log`

## Appendix: Node Count Comparison

| Metric | FR-100 | FR-101 (Original) | FR-101 (Amended) |
|--------|--------|-------------------|------------------|
| Nodes per chapter | 2 | 5 | 3 |
| Total nodes | 14 | 32 | 19 |
| Persist points | 1 | 24 | 6 |
| Judge points | 1 | 7 | 0 (inline) |
| Resume points | 0 | 24 | 6 |

## Judgment

> **✅ ADDRESSED** — This FR has been amended per the judgment below.
> The proposed solution now uses 19 nodes (not 32) and 6 persist points (not 24).

**Verdict: AMEND**

The FR correctly identifies problems (late persistence, late judgment, hallucination) but proposes a solution that is **over-engineered** for the actual need. The graph would grow from 14 to 32 nodes with significant duplication. Return to Plan with the following amendments.

### Examination Summary

| Aspect | Finding |
|--------|--------|
| Problem Identification | ✅ Accurate — Judge findings confirm 9/10 Commandments fabricated |
| Root Cause Analysis | ✅ Correct — Missing file context caused hallucination |
| Persistence Strategy | ⚠ Over-complex — 24 persist nodes is excessive |
| Node Count | ⚠ 32 nodes = 129% increase — high maintenance burden |
| Graph Duplication | ✗ 6× duplication of the same pattern |

### Critical Issues

#### 1. Pattern Duplication (DRY Violation)

The FR proposes repeating an identical 5-node pattern for all 6 chapters:
```
research_<X> → persist_research_<X> → write_<X> → persist_chapter_<X> → judge_<X> → persist_judge_<X> → amend_<X>
```

This violates Commandment 8: *"Kill all entropy and false idols."*

**Resolution:** Use a **map node** with a single well-defined chapter pipeline. Define chapters as a list and process each identically.

#### 2. Wrong Abstraction Level for Persistence

The FR proposes 24 persist nodes. But `write_chapters_tool` already exists and was the correct approach — it just ran at the end.

**Resolution:** Instead of 24 persist nodes, use a **single persist-per-chapter pattern** where the subgraph writes after the amend step. Total: 6 writes, not 24.

#### 3. The Real Bug: Missing Source Content in Prompts

The fabrication happened because the write prompts received *conclusions* from copilot research, not *verbatim source content*. The LLM then paraphrased/invented when asked to "use the research."

**Resolution (Primary Fix):**
- Research prompts should output **verbatim quotes with file:line citations**
- Write prompts should include an anti-hallucination directive: *"Quote exactly. Never paraphrase Commandments, Prayers, or doctrinal text."*

This is correctly identified in the FR but buried under infrastructure concerns.

### Revised Approach (Minimal)

**Phase 1: Fix the actual bug (30 min)**
1. Add explicit file lists to each research prompt's system context
2. Add anti-hallucination directive to write prompts
3. Research prompt schema should require `verbatim_quotes: list[str]` field

**Phase 2: Add chapter-level judgment (1.5 hours)**
1. Replace single `judge_draft` with per-chapter judge inside existing `write_<X>` nodes (use a 2-call pattern)
2. Or: add a single `validate_chapter` node after each write that checks against sources

**Phase 3: Simple persistence (optional, 30 min)**
1. Add `skip_if_exists: true` to write nodes (already the default)
2. Write each chapter to disk immediately after generation via existing `write_chapters_tool` modified to write incrementally

**Total: ~2.5 hours vs. 6+ hours for the 32-node approach**

### Acceptance Criteria Amendments

| Original | Amendment |
|----------|----------|
| "Each research node followed by a persist node" | **Remove** — persist once per chapter, not per stage |
| "24 persist points" | **Change to:** "6 persist points (one per chapter)" |
| "32 nodes" | **Change to:** "≤20 nodes (map node or 6 chapter groups with 3 nodes each)" |
| "Create `persist_to_file` Python tool" | **Keep** — but use once per chapter, not 4× per chapter |
| Explicit file lists in prompts | **Keep** — this is the primary fix |
| Anti-hallucination directive | **Keep** — this is critical |
| Chapter-level judge | **Keep** — add as inline validation or post-write check |

### The Judge Decrees

Amend the FR with focus on:

1. **Prompt quality** (add verbatim quote requirements)
2. **Per-chapter validation** (judge immediately after write, before next chapter)
3. **Simple persistence** (write to disk after each chapter, not after each stage)

Resubmit with ≤20 nodes and explicit prompt content fixes.

*What survives the fire may merge.*

---

**Amendment applied:** 2026-02-25. FR now proposes 19 nodes and 6 persist points. Authority granted.
