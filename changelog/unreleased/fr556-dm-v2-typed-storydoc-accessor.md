---
type: feat
scope: examples
req:
---
- **FR-556 DM v2 Typed StoryDoc Contract + Sole Accessor (Contract A)**: Added a permissive Pydantic `StoryDoc`/`Chapters`/`ChapterCard` backbone to `examples/dungeon_master/api/story_doc.py` with `parse()` (boundary validation) and `validate_chapter_card()` (raising `InvalidChapterCard`). Promoted `chapter_nav` to the one typed accessor: added the `chapter_turns` getter and the `write_chapter_card` setter that rejects a structurally-invalid card before committing. Migrated the read-only instruments cluster (`witness_metrics`, `prose_continuity`, `prompt_salience`) off the raw `doc["chapters"]...` reach-in onto the accessor, and routed `expand_chapters` through the setter so chapter authoring funnels through one validated write seam. The boundary parse is bound to writes, not reads, so loading a legacy book that degrades today never raises mid-run (J2). 42/42 live books validate against `StoryDoc`.
