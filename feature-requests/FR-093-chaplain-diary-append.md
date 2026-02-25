# FR-093: Chaplain Diary Append

**Status:** Implemented
**Requirement:** REQ-YG-090
**Capability:** CAP-31

## Value Statement

Every Plan→Judge session generates insights and decisions worth preserving. Without automatic logging, these lessons evaporate. This feature ensures the Chaplain workflow automatically appends a structured diary entry after each run, maintaining continuity of the development log.

## Objective

Extend `.chaplain/graph.yaml` with `summarize` and `write_diary` nodes so that every Plan→Judge run automatically records a diary entry to `docs/diary.md`.

## Implementation

### Changes Made

1. **`.chaplain/graph.yaml`** — Added two new nodes:
   - `summarize`: LLM node that distills Plan→Judge output into DiaryEntry
   - `write_diary`: Python tool node that appends formatted entry
   - New state fields: `date`, `diary_prefix`, `diary_entry`, `written`
   - Updated edges: `judge → summarize → write_diary → END`

2. **`.chaplain/prompts/summarize.yaml`** — New prompt with:
   - Jinja2 template receiving `plan_output` and `judge_output`
   - Inline Pydantic schema for DiaryEntry (theme, body, seed)

3. **`.chaplain/watch.sh`** — Added vars:
   - `--var date="$(date +%Y-%m-%d)"`
   - `--var diary_prefix="Chaplain"`

4. **`examples/diary_digest/nodes/writing.py`** — Modified:
   - `format_diary_entry()` accepts `prefix` parameter (default "World Digest")
   - `write_diary()` reads `diary_prefix` from state

5. **Tests** — Unit tests tagged with `@pytest.mark.req("REQ-YG-090")`:
   - `test_format_diary_entry_with_custom_prefix`
   - `test_format_diary_entry_default_prefix`

## Acceptance Criteria

- [x] `.chaplain/graph.yaml` includes `summarize` (LLM) and `write_diary` (Python tool) nodes
- [x] `.chaplain/prompts/summarize.yaml` exists with inline Pydantic schema (theme, body, seed)
- [x] Diary entry header uses `"Chaplain"` prefix (not `"World Digest"`)
- [x] `format_diary_entry()` accepts a configurable prefix parameter (backward-compatible default)
- [x] `watch.sh` passes `--var date=$(date +%Y-%m-%d)` to the graph
- [x] Unit tests for `format_diary_entry()` with custom prefix
- [x] Tests tagged with `@pytest.mark.req("REQ-YG-090")`
- [x] REQ-YG-090 added to ARCHITECTURE.md
- [x] CHANGELOG.md updated

## References

- Related: FR-084 (Watch.sh Migration)
- Related: FR-072 (Daily Digest example)
- Scripture: Commandment 10 (preserve and improve the doctrine)
