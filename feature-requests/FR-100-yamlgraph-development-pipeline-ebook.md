# Feature Request: FR-100 YAMLGraph Development Pipeline eBook

**Priority:** LOW
**Type:** Feature
**Status:** In Progress
**Effort:** 3 days
**Requested:** 2026-02-25
**Implemented:** 2026-02-25 (scaffold)

## Implementation Progress

### Commit bd1d6ce — Scaffold Complete
- ✅ `examples/ebook/graph.yaml` exists and passes `yamlgraph graph lint`
- ✅ Research prompts exist for all six chapters in `examples/ebook/prompts/source/`
- ✅ Writing prompts exist for all six chapters in `examples/ebook/prompts/write/`
- ✅ `judge_draft.yaml` prompt exists in `examples/ebook/prompts/`
- ✅ A Python write-chapters tool in `examples/ebook/nodes/writing.py`
- ✅ A unit test for the `write_chapters_tool` exists in `tests/unit/test_ebook_writing.py`
- ✅ REQ-YG-091, CAP-32 added to ARCHITECTURE.md and req_coverage.py
- ✅ `docs/ebook/README.md` with pandoc build instructions
- ✅ `docs/ebook/_build.sh` produces HTML via pandoc
- ✅ `docs/ebook/dist/` already covered by existing `.gitignore` pattern

### Remaining Work (Phase 4-5)
- [ ] Run the full authoring pipeline to generate chapters
- [ ] Review output for accuracy; iterate on prompts
- [ ] Judge findings and address issues
- [ ] Final read-through of all chapters

### Notes
- Renamed `research/` prompts directory to `source/` to avoid `.gitignore` conflict with global `research/` pattern

## Summary

Produce a standalone eBook (`docs/ebook/`) that documents the YAMLGraph development pipeline end-to-end — pre-commit hooks, doctrine, the chaplain watch loop, the inquisitor audit loop, and the diary system — authored chapter-by-chapter via a YAMLGraph pipeline using copilot nodes for research and LLM nodes for writing, producing renderable Markdown with Mermaid diagrams, tables, and annotated YAML excerpts.

## Value Statement

New contributors and external adopters get a single authoritative narrative — not scattered reference files — that explains *why* each pipeline component exists, how they interconnect, and how to operate them from day one; and the writing of the book itself demonstrates the YAMLGraph pipeline in action.

## Problem

YAMLGraph has a sophisticated development pipeline — pre-commit quality gates, Copilot-driven planning, automated diary keeping, background auditing — but this pipeline is undocumented as a coherent whole. Knowledge lives in fragments:

- `CLAUDE.md` / `.github/copilot-instructions.md` — doctrine and commands
- `.pre-commit-config.yaml` — hooks, but no narrative
- `.chaplain/watch.sh` + `inquisitor.sh` — scripts, but no explanation of purpose
- `examples/copilot/graph.yaml` — the workflow, but no onboarding guide
- `docs/diary.md` — accumulated history, but no schema explained upfront
- `examples/diary_digest/` — digestion graph, but purpose buried in commit history

A new contributor must read ~10 files, cross-reference feature requests, and infer intent. There is no single readable artifact that tells the story.

## Proposed Solution

### Structure

A six-chapter eBook rendered from `docs/ebook/` Markdown source:

```
docs/ebook/
  00-introduction.md        # Why this pipeline exists; the Scripture in context
  01-doctrine.md            # CLAUDE.md decoded: Commandments, Sermon, Rite
  02-precommit-gates.md     # Every hook in .pre-commit-config.yaml, annotated
  03-chaplain-pipeline.md   # watch.sh → copilot graph → Plan → Judge → Diary
  04-inquisitor.md          # inquisitor.sh: audit loop, findings, post-commit hook
  05-diary-system.md        # diary.md schema, diary_rotate.py, diary_digest graph
  _build.sh                 # pandoc Markdown → HTML (PDF nice-to-have)
  README.md                 # How to build and contribute
```

### Authoring Pipeline

The eBook is **written by a YAMLGraph graph** (`examples/ebook/graph.yaml`), chapter by chapter, following the multi-chapter LLM writing pattern from `examples/demos/novel_generator` and the copilot research node pattern from `examples/copilot/graph.yaml`. Execution is sequential: each chapter runs as a research+write node pair.

1. A **copilot research node** per chapter gathers authoritative source material from the codebase
2. An **LLM writing node** per chapter drafts the chapter from gathered research
3. A **judge node** (copilot) reviews the full draft for accuracy and completeness
4. A **write node** (Python tool) assembles chapters into `docs/ebook/`

Each chapter has a dedicated prompt YAML in `examples/ebook/prompts/`, following the `prompts_relative: true` pattern.

```yaml
# examples/ebook/graph.yaml (sketch)
name: ebook_pipeline
description: "Write the YAMLGraph development pipeline eBook chapter by chapter"

state:
  output_dir: str       # docs/ebook/
  date: str

nodes:
  research_introduction:
    type: copilot
    prompt: research/introduction
    backend: cli
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
    state_key: research_introduction
    timeout: 300

  write_introduction:
    type: llm
    prompt: write/introduction
    variables:
      research: "{state.research_introduction}"
    state_key: chapter_introduction

  # ... repeat pattern for each chapter ...

  judge_draft:
    type: copilot
    prompt: judge_draft
    backend: cli
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
    state_key: judge_result
    timeout: 500

  write_chapters:
    type: python
    tool: write_chapters_tool
    state_key: written
```

### Chapter Sketches

**00 Introduction** — "This project is self-documenting machinery." Brief tour of all components; full-pipeline Mermaid sequence diagram.

**01 Doctrine** — The 10 Commandments and Sermon explained with concrete codebase examples. The Knowledge Graph entry (`normalize at the boundary`) illustrated with a before/after code table.

**02 Pre-commit Gates** — Complete hook table (hook ID | purpose | what it catches | when it fires). Annotated excerpts from `.pre-commit-config.yaml`. Each of `absolution.py`, `req_coverage.py`, `noqa_confession.py`, `diary_rotate.py`, `changelog-required`, `feat-requires-fr` gets a short section.

**03 Chaplain Pipeline** — Mermaid sequence diagram: `inbox/*.md` → `watch.sh` → `graph run examples/copilot/graph.yaml` → Plan (copilot node) → Judge (copilot node) → Summarize (LLM) → `write_diary` (Python tool) → `drafts/`. Each stage annotated with the FR that introduced it.

**04 Inquisitor** — Purpose: background doctrinal compliance audit after every commit. How the `post-commit` hook fires `inquisitor.sh`. The four audit steps (Gather → Investigate → Judge → Record) as a Mermaid flowchart. Sample ✓/⚠/✗ findings table.

**05 Diary System** — `docs/diary.md` entry schema (Context, Heuristic, Seed) with a real example. `diary_rotate.py` rotation logic. `diary_digest` graph as a Mermaid diagram: how it synthesises monthly entries into a digest. How the Seed field drives future feature requests.

### Build

```bash
# Install pandoc (one-time)
brew install pandoc

# Write the ebook (runs the authoring pipeline)
yamlgraph graph run examples/ebook/graph.yaml \
    --var output_dir=docs/ebook \
    --var date="$(date +%Y-%m-%d)" \
    --full

# Render to HTML/PDF
docs/ebook/_build.sh
# Outputs: docs/ebook/dist/yamlgraph-dev-pipeline.html
#          docs/ebook/dist/yamlgraph-dev-pipeline.pdf  (if pandoc+latex)
```

### Prompt Structure

Each chapter has two prompts in `examples/ebook/prompts/`:

```
examples/ebook/prompts/
  research/
    introduction.yaml    # Copilot research instructions: gather sources
    doctrine.yaml
    precommit_gates.yaml
    chaplain_pipeline.yaml
    inquisitor.yaml
    diary_system.yaml
  write/
    introduction.yaml    # LLM writing instructions: draft chapter from research
    doctrine.yaml
    precommit_gates.yaml
    chaplain_pipeline.yaml
    inquisitor.yaml
    diary_system.yaml
  judge_draft.yaml       # Copilot: review full draft for accuracy
```

Research prompts instruct the copilot node to read specific source files and return structured findings. Writing prompts instruct the LLM to produce Markdown with Mermaid diagrams and tables where appropriate — no raw code walls, no unsupported claims.

## Acceptance Criteria

### eBook Content
- [ ] `docs/ebook/` directory created with five chapter files (`00`–`05`), `_build.sh`, and `README.md`
- [ ] Each chapter readable end-to-end without needing to open source files to understand the concept (cross-references allowed as pointers, not prerequisites)
- [ ] Chapter 00 includes a full-pipeline Mermaid sequence or flowchart diagram
- [ ] Chapter 02 includes a complete hook table matching `.pre-commit-config.yaml`
- [ ] Chapter 03 Mermaid sequence diagram accurately reflects current `examples/copilot/graph.yaml` edges
- [ ] Chapter 04 includes a sample ✓/⚠/✗ findings table with at least one example of each classification
- [ ] Chapter 05 documents diary entry schema with a real example entry
- [ ] Each chapter links back to originating FR(s) where relevant
- [ ] No new Python library dependencies introduced
- [ ] `docs/ebook/*.md` chapter files are committed to the repository as generated artifacts; the authoring pipeline may be re-run to regenerate them; the committed state is the canonical snapshot

### Authoring Pipeline
- [ ] `examples/ebook/graph.yaml` exists and passes `yamlgraph graph lint`
- [ ] Research prompts exist for all six chapters in `examples/ebook/prompts/research/`
- [ ] Writing prompts exist for all six chapters in `examples/ebook/prompts/write/`
- [ ] `judge_draft.yaml` prompt exists in `examples/ebook/prompts/`
- [ ] Running `yamlgraph graph run examples/ebook/graph.yaml --var output_dir=docs/ebook --var date=...` produces all chapter files
- [ ] A Python write-chapters tool in `examples/ebook/nodes/` assembles output to `docs/ebook/`
- [ ] A unit test for the `write_chapters_tool` exists in `tests/unit/` and passes; it mocks chapter state and asserts that files are written to the correct output directory; the test is tagged `@pytest.mark.req("REQ-YG-XXX")` and a corresponding requirement is added to `ARCHITECTURE.md`

### Build
- [ ] `_build.sh` produces valid HTML via pandoc (`pandoc` optional; HTML sufficient, PDF nice-to-have)
- [ ] `docs/ebook/README.md` documents `pandoc` as build prerequisite with install instructions and contribution guide
- [ ] `docs/ebook/dist/` added to `.gitignore`

## Alternatives Considered

1. **Handwrite chapters directly** — Rejected: the point of YAMLGraph is to demonstrate what it can do. Using the pipeline to write the eBook about the pipeline is self-demonstrating and the canonical dog-food test for copilot + LLM node composition.
2. **Single long README section** — Rejected: README is already long; narrative needs chapters and flow.
3. **Reference site (MkDocs/Sphinx)** — Rejected: over-engineering for a narrative guide. Markdown + pandoc is minimal viable; can be promoted later.
4. **Video walkthrough** — Rejected: text survives refactoring, video does not. Text is searchable, diffable, version-controlled.

## Implementation Approach

### Phase 1 — Scaffold (0.5 day)
1. Create `examples/ebook/` directory structure
2. Write stub `graph.yaml` with all nodes wired
3. Add `docs/ebook/dist/` to `.gitignore`
4. Create `docs/ebook/README.md` with build instructions

### Phase 2 — Research Prompts (0.5 day)
Write the six research prompts. Each prompt instructs the copilot node to:
- Read specific source files (listed explicitly)
- Return structured Markdown: summary, key facts, verbatim excerpts to quote, diagram sources

### Phase 3 — Writing Prompts (0.5 day)
Write the six writing prompts. Each prompt:
- Receives `{research}` variable with copilot findings
- Instructs the LLM to produce a chapter in Markdown with Mermaid diagrams, tables, and annotated YAML excerpts
- Specifies required sections per chapter (from chapter sketches above)
- References style: "readable narrative, not API docs; explain *why*, not just *what*"

### Phase 4 — Run Pipeline & Refine (1 day)
- Run the full authoring pipeline
- Review output for accuracy; iterate on prompts where chapters are thin or incorrect
- Run judge node; address findings

### Phase 5 — Build Script & Polish (0.5 day)
- Write `_build.sh`
- Verify HTML output
- Final read-through of all chapters

## Related

- `CLAUDE.md` — Primary source for Chapter 01
- `.pre-commit-config.yaml` — Primary source for Chapter 02
- `examples/copilot/graph.yaml` — Primary source for Chapter 03
- `.chaplain/watch.sh`, `.chaplain/inquisitor.sh` — Primary sources for Chapters 03–04
- `examples/diary_digest/` — Primary source for Chapter 05
- `docs/diary.md` — Living artefact documented in Chapter 05
- `examples/demos/novel_generator/` — Pattern reference for multi-chapter LLM writing pipeline
- FR-068: Chaplain watch loop
- FR-076: Inquisitor
- FR-081: Copilot node type
- FR-084: Watch migration to copilot node graph
- FR-093: Diary append integration
- FR-097: Shared diary utilities
- FR-098: Consolidated copilot graph
