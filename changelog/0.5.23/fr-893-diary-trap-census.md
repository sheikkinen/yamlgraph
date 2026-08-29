---
type: feat
scope: census
req: REQ-YG-624
---
- **FR-893 Diary Trap Census**: diary adapters + rubric bind to the
  unchanged corpus_census pipeline; an LLM-free recurrence aggregator
  groups census ledgers by canonical trap label with distinct-entry
  counting, enforces a hidden-canary run gate, writes a public-safe
  recurrence table under docs/diary/census/ (no evidence spans committed),
  and drafts .chaplain/inbox graduation proposals for candidates at the
  Scripture bar. `scripts/diary_census.sh` runs the month×decade-batched
  full-corpus census. (REQ-YG-624)
