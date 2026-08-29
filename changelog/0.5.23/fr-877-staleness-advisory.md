---
type: feat
scope: examples
req: REQ-YG-622
---
- **FR-877 Memory Curation Staleness Advisory**: apply now records a post-apply live baseline (`.curation-state.json`, forgotten paths absent — a forget-run yields zero immediate drift); `advisory.py` (pure stdlib, zero egress) diffs the live corpus by sha256 and prints one line at/above threshold or for a never-curated corpus; SessionStart runs it fail-open via `memory-advisory.sh` with bounded JSONL failure evidence. Detection mechanical, execution deliberate. (REQ-YG-622)
