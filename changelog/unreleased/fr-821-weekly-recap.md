---
type: feat
scope: recap
req: REQ-YG-604
---
- **FR-821 Weekly Recap Publication**: `scripts/weekly_recap.py` renders the recap graph (CAP-195, unmodified) into `docs/recaps/<ISO-week>.md` with a frozen section contract; deterministic substantive-window guard excludes recap-only automation commits before any LLM call; node errors raise instead of publishing a partial recap. Scheduled publication via `.github/workflows/weekly-recap.yml` automation PR + auto-merge. (REQ-YG-604)
