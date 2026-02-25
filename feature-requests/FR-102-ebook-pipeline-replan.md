# Feature Request: FR-102 eBook Pipeline — Consolidated Replan

**Priority:** HIGH
**Type:** Redesign
**Status:** Superseded
**Superseded-by:** FR-103
**Requested:** 2026-02-25
**Depends-on:** FR-100

## Summary

This FR consolidates learnings from FR-100 (initial implementation) and FR-101 (over-engineered revision) to produce a minimal, effective pipeline redesign.

## Problem Recap

FR-100 pipeline run (2026-02-25) revealed:
1. **Ch01 Doctrine:** 9/10 Commandments fabricated by LLM (hallucination)
2. **Ch05 Diary:** 121KB output (oversized — likely raw research embedded)
3. **Ch00 Intro:** TOC misordered
4. **Late judgment:** Single judge at end found issues after all chapters written
5. **Late persistence:** All state in memory until `write_chapters` at line 195

Root cause: Write prompts received *conclusions*, not *verbatim source content*.

---

## Graph Comparison

### Current: FR-100 (14 nodes)

```
START
  ↓
research_introduction (copilot)
  ↓
write_introduction (llm)
  ↓
research_doctrine (copilot)
  ↓
write_doctrine (llm)
  ↓
research_precommit (copilot)
  ↓
write_precommit (llm)
  ↓
research_chaplain (copilot)
  ↓
write_chaplain (llm)
  ↓
research_inquisitor (copilot)
  ↓
write_inquisitor (llm)
  ↓
research_diary (copilot)
  ↓
write_diary (llm)
  ↓
write_chapters (tool) ← ONLY persist point
  ↓
judge_draft (copilot) ← ONLY judge point
  ↓
END
```

| Metric | Value |
|--------|-------|
| Total nodes | 14 |
| Copilot nodes | 7 |
| LLM nodes | 6 |
| Tool nodes | 1 |
| Persist points | 1 (end) |
| Judge points | 1 (end) |
| Time to detect hallucination | ~15 min (after all chapters) |

**Problems:**
- ✗ No intermediate persistence (crash = lost work)
- ✗ Late judgment (hallucination detected too late)
- ✗ Research prompts return summaries, not verbatim quotes

---

### FR-101 Original (32 nodes) — REJECTED

```
Per chapter (×6):
  research_<ch> (copilot)
    ↓
  persist_research_<ch> (tool)
    ↓
  write_<ch> (llm)
    ↓
  persist_chapter_<ch> (tool)
    ↓
  judge_<ch> (copilot)
    ↓
  persist_judge_<ch> (tool)
    ↓
  amend_<ch> (llm, conditional)

Final:
  judge_final (copilot)
    ↓
  END
```

| Metric | Value |
|--------|-------|
| Total nodes | 32 |
| Persist points | 24 (4 per chapter) |
| Judge points | 7 (1 per chapter + final) |

**Why rejected:**
- ✗ 129% node increase
- ✗ DRY violation (identical 5-node pattern ×6)
- ✗ Over-engineered for actual problem
- ✗ 24 persist calls is excessive

---

### FR-101 Amended (19 nodes) — PROPOSED

```
Per chapter (×6):
  research_<ch> (copilot)
    ↓
  write_<ch> (llm)
    ↓
  persist_<ch> (tool) ← writes chapter to disk

Final:
  judge_final (copilot) ← validates all chapters
    ↓
  END
```

| Metric | Value |
|--------|-------|
| Total nodes | 19 |
| Persist points | 6 (1 per chapter) |
| Judge points | 1 (final, validates all) |

**Improvements:**
- ✓ Per-chapter persistence (resumable)
- ✓ Prompt quality fix (primary hallucination cure)
- ✓ 36% node increase (vs 129%)
- ⚠ Still late judgment

---

## The Missing Piece: Inline Validation

The FR-101 amendment proposes "inline validation" in write prompts, but this is implicit. A cleaner approach:

### Option A: Post-Write Validation Node (22 nodes)

Add a validation node after each write:

```
research_<ch> (copilot)
    ↓
write_<ch> (llm)
    ↓
validate_<ch> (llm) ← checks against research.verbatim_quotes
    ↓
persist_<ch> (tool)
```

| Metric | Value |
|--------|-------|
| Total nodes | 22 (6×3 + 4 shared) |
| Validation points | 6 |
| Effort | +30 min for validation prompts |

### Option B: Two-Call Write Node (19 nodes)

Use a single LLM node with structured output that includes self-validation:

```yaml
schema:
  name: ChapterOutput
  fields:
    content: {type: str, description: "Chapter markdown"}
    validation_notes: {type: str, description: "Self-check against verbatim quotes"}
    all_doctrine_quoted: {type: bool, description: "True if all Commandments/Prayers quoted exactly"}
```

If `all_doctrine_quoted: false`, the chapter is flagged for review.

### Option C: Map Node (7 nodes) — DRY

**Use YAMLGraph map node to process chapters identically:**

```yaml
nodes:
  chapters_config:
    type: python
    tool: load_chapters  # Returns list of {name, num, files}
    state_key: chapters

  process_chapters:
    type: map
    over: "{state.chapters}"
    subgraph: chapter_pipeline
    state_key: written_chapters

  judge_final:
    type: copilot
    prompt: judge_final
    state_key: judgment

chapter_pipeline:  # Subgraph for each chapter
  nodes:
    research:
      type: copilot
      prompt: source/{chapter.name}
    write:
      type: llm
      prompt: write/{chapter.name}
    persist:
      type: tool
      tool: persist_chapter
```

| Metric | Value |
|--------|-------|
| Main graph nodes | 3 |
| Subgraph nodes | 3 |
| Total unique nodes | 6 |
| Persist points | 6 (via map iteration) |
| DRY compliant | ✓ |

### Option D: Merged Chapter Nodes (8 nodes) — SIMPLEST

**Insight:** The research→write split caused the hallucination.

- **Copilot nodes** can read files (tools) but output is unstructured
- **LLM nodes** can produce structured output but can't read files
- Research returned *summaries*, write *invented* from summaries

**Solution:** Merge into a single copilot node per chapter that:
1. Reads specific files
2. Writes the chapter with verbatim quotes
3. Returns markdown directly

```
START
  ↓
write_introduction (copilot) ← reads files + writes chapter
  ↓
persist_introduction (tool)
  ↓
write_doctrine (copilot)
  ↓
persist_doctrine (tool)
  ↓
... (4 more chapters)
  ↓
judge_final (copilot)
  ↓
END
```

**Combined prompt example (doctrine):**
```yaml
system: |
  You are writing Chapter 01: Doctrine for the YAMLGraph eBook.
  You have access to read files. Quote doctrine EXACTLY - never paraphrase.

user: |
  ## Files to Read
  1. `.github/copilot-instructions.md` — READ THIS FIRST for 10 Commandments
  2. `CLAUDE.md` — Development commands

  ## Chapter Requirements
  Write "Doctrine: The Scripture Decoded" with:
  1. The 10 Commandments — **QUOTE VERBATIM** from copilot-instructions.md
  2. The Sermon workflow
  3. The Knowledge Graph YAML
  4. The Rite of Correction
  5. The Agents' Prayer — **QUOTE VERBATIM**

  Format as markdown. Use > for block quotes of doctrine text.
```

| Metric | Value |
|--------|-------|
| Total nodes | 8 (6 write + 1 judge + 1 persist shared?) |
| Copilot nodes | 7 |
| LLM nodes | 0 |
| Persist points | 6 |
| Hallucination risk | LOW (copilot reads source directly) |

**Why this works:**
- Copilot reads `.github/copilot-instructions.md` → quotes verbatim
- No intermediate "research" summary that loses fidelity
- Single prompt per chapter = simpler prompts directory

**Tradeoff:**
- ✗ No structured schema validation (copilot returns markdown)
- ✓ But hallucination was the bigger problem

### Option E: Merged Write + Judge-Amend Subgraph (14 nodes) — ROBUST

**Insight:** Book-level judgment isn't actionable. By the time we find errors, all chapters are written. Judge-amend must run per chapter.

**Key insight:** The chapter prompt already lists source files. The chapter content should include inline file references (citations). The judge extracts file paths from the content — no need to pass source_files separately.

**Pattern per chapter:**
```
write_<chapter> (copilot)
    ↓
validate_<chapter> (subgraph) ← judge-amend cycle
    ↓
persist_<chapter> (tool)
```

**Chapter prompt requirement (citation style):**
```yaml
# prompts/chapter/doctrine.yaml
user: |
  ## Files to Read
  1. `.github/copilot-instructions.md` — Primary source
  2. `CLAUDE.md` — Development commands

  ## Writing Requirements
  - Include file references inline when quoting
  - Use citation format: "As defined in `<file>`:"
  - Quote doctrine VERBATIM within > block quotes

  Example citation:
  > As defined in `.github/copilot-instructions.md`:
  >
  > **1. Thou shalt research before coding** — Let infinite agents explore...
```

**The validate subgraph (simplified):**
```yaml
# subgraphs/validate_chapter.yaml
name: validate_chapter
description: Judge-amend cycle for a single chapter

input:
  chapter: str  # Contains inline file references as citations

nodes:
  judge:
    type: copilot
    prompt: judge/chapter
    backend: cli
    cli_flags:
      allow_all_paths: true
    variables:
      chapter: "{input.chapter}"
    state_key: judgment
    # Output: {passed: bool, issues: list[str], critical: bool}

  amend:
    type: copilot
    prompt: amend/chapter
    backend: cli
    cli_flags:
      allow_all_paths: true
    variables:
      chapter: "{input.chapter}"
      issues: "{state.judgment.issues}"
    state_key: amended_chapter
    # Only run if judge found issues
    run_if: "not {state.judgment.passed}"

edges:
  - from: START
    to: judge
  - from: judge
    to: amend
    condition: "not {state.judgment.passed}"
  - from: judge
    to: END
    condition: "{state.judgment.passed}"
  - from: amend
    to: END

output:
  chapter: "{state.amended_chapter or input.chapter}"
  validation_passed: "{state.judgment.passed}"
```

**Main graph structure (simplified):**
```yaml
nodes:
  write_doctrine:
    type: copilot
    prompt: chapter/doctrine
    state_key: chapter_doctrine

  validate_doctrine:
    type: subgraph
    graph: subgraphs/validate_chapter
    variables:
      chapter: "{state.chapter_doctrine}"  # ← just the chapter, no source_files
    state_key: validated_doctrine

  persist_doctrine:
    type: tool
    tool: persist_chapter
    variables:
      content: "{state.validated_doctrine.chapter}"
      filename: "01-doctrine.md"

edges:
  - from: write_doctrine
    to: validate_doctrine
  - from: validate_doctrine
    to: persist_doctrine
```

**Judge prompt (extracts file refs from content):**
```yaml
# prompts/judge/chapter.yaml
system: |
  You are a technical reviewer validating chapter content.
  Your job: verify quoted content matches the cited source files.

user: |
  ## Chapter Content
  {chapter}

  ## Validation Process
  1. Find all file citations in the chapter (format: `path/to/file`)
  2. Read each cited file
  3. Verify quoted content matches the source EXACTLY
  4. Check for fabricated content not in any source

  ## Validation Checks
  - Are Commandments/Prayers quoted VERBATIM?
  - Do code examples match cited sources?
  - Is any content fabricated (claims not in cited files)?

  Return structured findings.

schema:
  name: ChapterJudgment
  fields:
    passed: {type: bool, description: "True if all quotes verified"}
    issues: {type: list[str], description: "Specific issues with file:line refs"}
    critical: {type: bool, description: "True if fabrication detected"}
    files_verified: {type: list[str], description: "Files that were read and checked"}
```

**Amend prompt (uses same citations):**
```yaml
# prompts/amend/chapter.yaml
system: |
  You fix chapter content based on reviewer feedback.
  You have access to read source files. Quote EXACTLY from sources.

user: |
  ## Current Chapter
  {chapter}

  ## Issues to Fix
  {% for issue in issues %}
  - {{ issue }}
  {% endfor %}

  Read the cited source files to get correct content.
  Rewrite the chapter with all issues fixed.
  Maintain the citation format: "As defined in `<file>`:"
```

| Metric | Value |
|--------|-------|
| Main graph nodes | 18 (6×3: write + validate + persist) |
| Subgraph nodes | 2 (judge + amend) |
| Total unique definitions | 14 |
| Persist points | 6 |
| Validation points | 6 (per-chapter) |
| Hallucination detection | Per chapter (early) |

**Why this is robust:**
- ✓ Errors caught immediately after each chapter
- ✓ Amend happens while context is fresh
- ✓ Subgraph is reusable (DRY)
- ✓ Judge can read source files to verify quotes
- ✓ Structured judgment output (schema)

**Tradeoff:**
- More complex than Option D
- Requires subgraph support (already exists in YAMLGraph)
- ~2x nodes vs Option D

**Key design decision:** Single amend iteration (not loop). If amend fails, the persist still happens but `validation_passed: false` is tracked. A final book-level review can flag chapters that failed validation.

---

## Recommendation

**Option E (Merged Write + Judge-Amend Subgraph)** is the recommended approach:
- Directly addresses root cause (copilot reads files)
- Per-chapter validation catches errors early
- Subgraph is reusable and DRY
- Structured judgment enables tracking

**Fallback: Option D** if subgraph adds too much complexity for this use case.

## Acceptance Criteria (Option E)

### Primary (Merged Chapter Prompts)
- [ ] 6 combined chapter prompts in `prompts/chapter/` directory
- [ ] Each prompt lists specific files to read
- [ ] Each prompt includes "QUOTE VERBATIM" directive for doctrine
- [ ] Remove old `prompts/source/` and `prompts/write/` directories

### Judge-Amend Subgraph
- [ ] `subgraphs/validate_chapter.yaml` created
- [ ] `prompts/judge/chapter.yaml` with verification checklist
- [ ] `prompts/amend/chapter.yaml` with fix instructions
- [ ] Judge returns structured `ChapterJudgment` schema
- [ ] Amend only runs if `judgment.passed == false`

### Per-Chapter Persistence
- [ ] Each chapter written to disk after validation
- [ ] `skip_if_exists: true` for resumability
- [ ] Validation status tracked per chapter

### Validation
- [ ] Ch01 Doctrine re-run produces exact Commandments from `.github/copilot-instructions.md`
- [ ] No fabricated content in any chapter
- [ ] Judge catches fabrication in test with known-bad input

## Implementation Plan (Option E)

### Phase 1: Create Judge-Amend Subgraph (30 min)
1. Create `subgraphs/validate_chapter.yaml`
2. Create `prompts/judge/chapter.yaml` with verification logic
3. Create `prompts/amend/chapter.yaml` with fix instructions
4. Test subgraph in isolation with sample chapter

### Phase 2: Create Merged Chapter Prompts (45 min)
1. Create `prompts/chapter/` directory
2. Create 6 merged prompts:
   - `introduction.yaml` — reads README, ARCHITECTURE, CLAUDE, copilot-instructions
   - `doctrine.yaml` — reads copilot-instructions (primary), CLAUDE
   - `precommit_gates.yaml` — reads .pre-commit-config.yaml, scripts/
   - `chaplain_pipeline.yaml` — reads examples/copilot/
   - `inquisitor.yaml` — reads .chaplain/, .pre-commit-config.yaml
   - `diary_system.yaml` — reads docs/diary.md, scripts/diary_rotate.py
3. Each prompt includes "QUOTE VERBATIM" for doctrine text

### Phase 3: Graph Restructure (30 min)
1. Remove all `research_*` nodes
2. Convert `write_*` nodes from `type: llm` to `type: copilot`
3. Add 6 `validate_*` subgraph nodes
4. Add 6 `persist_*` tool nodes
5. Update edges: write → validate → persist → next_write
6. Remove final `judge_draft` (validation now per-chapter)

### Phase 4: Test Run (30 min)
1. Run Ch01 Doctrine in isolation
2. Verify judge catches if Commandments don't match source
3. Verify amend fixes issues
4. Run full pipeline

**Total: ~2.5 hours**

## Files to Create/Modify

| File | Action |
|------|--------|
| `examples/ebook/subgraphs/validate_chapter.yaml` | CREATE: judge-amend subgraph |
| `examples/ebook/prompts/judge/chapter.yaml` | CREATE: verification prompt |
| `examples/ebook/prompts/amend/chapter.yaml` | CREATE: fix prompt |
| `examples/ebook/prompts/chapter/*.yaml` | CREATE: 6 merged chapter prompts |
| `examples/ebook/prompts/source/` | DELETE: no longer needed |
| `examples/ebook/prompts/write/` | DELETE: no longer needed |
| `examples/ebook/graph.yaml` | REWRITE: 18 nodes (6×(write+validate+persist)) |
| `examples/ebook/nodes/writing.py` | ADD: `persist_chapter` function |

## Related

- FR-100: Initial scaffold (current implementation)
- FR-101: Over-engineered revision (rejected, amended)
- Judge findings: 9/10 Commandments fabricated in Ch01
