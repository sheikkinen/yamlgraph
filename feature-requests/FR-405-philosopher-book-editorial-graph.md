# FR-405: Philosopher Book Editorial Graph

**Priority:** Medium
**Type:** Enhancement
**Status:** Implemented
**Effort:** Medium
**Requested:** 2026-05-17

## Summary

Add a separate editorial graph for the Philosopher's Book that reads generated chapter drafts from a folder, uses an LLM-powered map pass to edit chapters in parallel, and writes the edited chapters plus an editorial report to a new output folder.

## Value Statement

Book authors get a repeatable editorial workflow that compresses overstretched chapters, reduces repetition, and preserves the Philosopher voice without manually editing every draft.

## Problem

The initial Philosopher's Book chapters contain strong arguments and voice, but the text is stretched in places. Several chapters repeatedly invoke the same incidents, restate the One Law, and continue proving a thesis after the reader has already understood it.

The current `examples/demos/philosopher_book/graph.yaml` is a generation graph: it plans and writes chapters from trap definitions and diary searches. Editing is a different concern. If chapter generation is expanded to also perform editorial judgment, the graph risks mixing creation, review, rewriting, and file persistence in one workflow.

The editorial need is specific:

1. Read chapter markdown files from an existing folder.
2. Build enough global context to avoid isolated per-chapter edits.
3. Edit each chapter for compression, distinction, and reduced repetition.
4. Save complete edited markdown files to a separate folder without overwriting drafts.
5. Produce a report showing what changed and where repetition was reduced.

## Proposed Solution

Create a new graph under `examples/demos/philosopher_book/`, for example:

```text
examples/demos/philosopher_book/editorial_graph.yaml
examples/demos/philosopher_book/prompts/editorial_brief.yaml
examples/demos/philosopher_book/prompts/edit_chapter.yaml
```

The graph should be separate from FR-404's chapter-generation graph and should use deterministic Python tools for filesystem effects.

### Pipeline

```yaml
load_chapters -> build_editorial_brief -> edit_chapters -> save_edited_chapters -> write_editorial_report
```

### Node responsibilities

#### `load_chapters`

Python node that reads markdown chapter files from `input_dir`.

Expected behavior:

- Accept `input_dir` and optional `glob_pattern`, defaulting to `*.md`.
- Treat `input_dir` as repo-relative by default and reject path traversal outside the repository.
- Sort chapter files by filename.
- Return chapter records containing:
  - `filename`
  - `path`
  - `chapter_num` when parseable from `ch-NN-...`
  - `title`
  - `text`
  - `word_count`
- Raise a clear error when no chapter files are found.

#### `build_editorial_brief`

LLM node that receives all chapter metadata and excerpts, then produces a global editorial brief.

The brief should identify:

- repeated incidents across chapters, such as NC-291, FR-179, and NC-220
- chapters that need stronger distinctness
- chapter-specific editorial jobs
- global style constraints to preserve
- maximum acceptable compression guidance

This node is the editorial boundary. It prevents the map pass from becoming 21 isolated editors with no book-level memory.

The brief must not blindly pass every full chapter into one prompt when the input folder is large. The implementation should provide bounded excerpts and metadata sufficient for book-level editorial judgment, while full chapter text remains available to the per-chapter map item.

#### `edit_chapters`

Map node over loaded chapters. Each item receives the chapter text and the global editorial brief.

The map sub-node should use an LLM prompt with a structured output schema:

```yaml
schema:
  name: EditedChapter
  fields:
    edited_markdown:
      type: str
      description: Complete edited chapter markdown
    editorial_notes:
      type: list[str]
      description: Brief notes explaining major cuts, preserved repetitions, and chapter-boundary decisions
    compression_summary:
      type: str
      description: One paragraph describing what changed
```

The prompt should instruct the LLM to:

- preserve authorial voice, concrete incidents, quoted diary excerpts, and core thesis
- remove repeated proof, repeated aphoristic restatement, and examples that only confirm the same point
- prefer 15-30% compression unless the chapter is already tight
- sharpen what this chapter uniquely argues compared with neighboring chapters
- avoid introducing new incidents, new claims, or unsupported references
- return complete edited markdown, not a patch

#### `save_edited_chapters`

Python node that writes collected edited chapters to `output_dir`.

Expected behavior:

- Create `output_dir` if needed.
- Treat `output_dir` as repo-relative by default and reject path traversal outside the repository.
- Preserve original filenames.
- Write only `edited_markdown` to chapter files.
- Never overwrite `input_dir` unless `output_dir` is explicitly the same path.
- Return saved file paths and word-count deltas.

#### `write_editorial_report`

Python node that writes a report, for example `editorial-report.md`, to `output_dir`.

The report should include:

- original and edited word counts
- compression ratio per chapter
- map-produced editorial notes
- global brief summary
- any chapters outside the target compression range

## Example Usage

```bash
yamlgraph graph run examples/demos/philosopher_book/editorial_graph.yaml \
  --var input_dir="outputs/philosopher-book/chapters" \
  --var output_dir="outputs/philosopher-book/edited-chapters"
```

## Acceptance Criteria

- [ ] A separate editorial graph exists and does not replace the FR-404 generation graph.
- [ ] `load_chapters` reads chapter markdown files from a repo-contained input folder and raises when none are found.
- [ ] The graph builds a global editorial brief before per-chapter editing.
- [ ] The graph uses a `type: map` node to edit chapters with LLM calls.
- [ ] Each map item receives both the chapter text and the global editorial brief.
- [ ] Edited chapters are written to a repo-contained output folder with original filenames preserved.
- [ ] Original chapter files are not modified by default.
- [ ] An editorial report is written with word-count deltas and editorial notes.
- [ ] Unit tests cover chapter loading, missing-input errors, path traversal rejection, output path preservation, and report generation.
- [ ] Demo output proves the graph ran against sample chapters.
- [ ] Documentation explains the distinction between generation and editorial graphs.

## Judgement

Approved with amendments.

The proposal solves the correct problem at the correct boundary. The current Philosopher's Book generation graph creates drafts; it should not also own editorial compression. A separate editorial graph preserves the generation workflow while adding a repeatable revision pass for the observed problem: stretched chapters, repeated incidents, and insufficient chapter distinctness.

The strongest design choice is the global editorial brief before the map pass. Without it, the implementation would fall into the same trap it is meant to fix: local chapter edits would trim sentence-level repetition while missing book-level reuse of NC-291, FR-179, NC-220, and the One Law. The brief makes the editorial boundary explicit before parallel fan-out.

The implementation is authorized under these constraints:

1. Filesystem access belongs to Python tools, not LLM prompts. LLM nodes may edit prose and produce structured editorial notes; Python nodes must load, validate, save, and report.
2. `input_dir` and `output_dir` must be constrained to repo-contained paths unless a future FR explicitly authorizes broader filesystem access.
3. The global brief must be token-bounded. Use chapter metadata and excerpts for book-level diagnosis; pass full text only to each chapter's own map item.
4. The map node should rely on YAMLGraph's existing `type: map` parallel fan-out and `max_items` safety cap. Do not invent a `sequential` option for this FR.
5. The output folder must be separate by default so the original drafts remain available for comparison.

## Implementation Notes

Implemented:

- `examples/demos/philosopher_book/editorial_graph.yaml`
- `examples/demos/philosopher_book/prompts/editorial_brief.yaml`
- `examples/demos/philosopher_book/prompts/edit_chapter.yaml`
- `load_chapters`, `save_edited_chapters`, and `write_editorial_report` in `examples/demos/philosopher_book/tools.py`
- FR-405 unit coverage in `tests/unit/test_philosopher_book.py`
- REQ-YG-405 registration in `ARCHITECTURE.md` and `capabilities/CAP-150-philosopher-book-demo.yaml`

Execution of the editorial LLM graph is intentionally deferred. The graph and
deterministic tools are implemented and lintable, but no `demo-output.log` was
regenerated for this change because the requested enforcement scope explicitly
deferred execution while chapters may still be generated.

## Alternatives Considered

### Edit directly in the existing generation graph

Rejected. Chapter generation and editorial revision are different concerns. Keeping the editorial pass separate allows drafts to be regenerated or edited independently.

### Let the LLM write files directly

Rejected. The LLM should own prose judgment, not filesystem effects. Python tools should handle path validation, directory creation, filename preservation, and report writing.

### Pure per-chapter parallel editing with no global brief

Rejected. Local chapter edits can reduce sentence-level repetition but miss cross-chapter repetition. A global brief normalizes the editorial boundary before the map pass.

### Sequential editing as the default

Rejected. Each chapter edit is independent once the global brief exists, so YAMLGraph's existing `type: map` fan-out is the natural fit. Provider limits should be handled through input batching, provider/model choice, timeout settings, and the existing `max_items` cap rather than by adding undocumented map semantics.

## Related

- `feature-requests/FR-404-philosopher-book.md`
- `examples/demos/philosopher_book/graph.yaml`
- `examples/demos/philosopher_book/tools.py`
- `examples/demos/map/graph.yaml`
- `examples/demos/python-map/graph.yaml`
