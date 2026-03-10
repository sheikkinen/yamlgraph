---
type: feat
scope: diary
req: REQ-YG-131
---
- **FR-134 Diary Folder Refactor — Replace Single File with Date-Prefixed Entries**: Replace the monolithic `docs/diary.md` with a `docs/diary/` folder of date-prefixed entry files, eliminating merge conflicts caused by concurrent appends from `finalize_merge.sh`, `diary_rotate.py`, `inquisitor.sh`, and `examples/shared/diary.py`. (REQ-YG-131)
