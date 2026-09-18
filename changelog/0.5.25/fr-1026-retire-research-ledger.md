---
type: removal
scope: research
req: REQ-YG-623
---
- **FR-1026 Retire the research provenance ledger**: `feature-requests/research-runs.jsonl`,
the SHA-256 append in `scripts/research.sh`, and `research_preflight.py
--verify-promotion` are gone. The verifier was invoked by no hook, CI step or
script; the only way to satisfy it after correcting a brief was to re-run
research, which on FR-1022 produced a record the judge had never read. The
judge's substance read of the promoted record — once — is the research gate;
the closed-brief preflight, artifact schema check, prior-art block and record
header are unchanged. (REQ-YG-623)
