---
type: feat
scope: examples
req: REQ-YG-530
---
- **FR-691 Plot Threads and Throughlines**: novel_fandom gains a derived story layer — `Thread` (decomposition by conflict) and `Throughline` (decomposition by character) Pydantic schemas plus five pure mechanical gates in `nodes/thread_gates.py`: citation integrity, ledger walk (a release needs a prior raise by FR-690 sequence), cap-and-distinctness (≤8 threads, distinct carrier sets, non-empty opposition), id stability across regeneration, and throughline acceptance (sequence-ordered, cited, slack-or-taut, non-zero-delta majors). Gates are arithmetic, not LLM tasks. (REQ-YG-530)
