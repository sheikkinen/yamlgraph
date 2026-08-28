---
type: fix
scope: research
req: REQ-YG-623
---
- **FR-896 Research Route Precedent Traceability**: precedent claims are now reconciled in code at the reducer boundary — committed FR/CAP/path/Scripture identifiers must exist, explicit `brief-echo` rows are demoted (retained, excluded from scoring), fabricated identifiers fail with named violations, librarian URLs are reconciled against recorded tool results, closed class/verdict enums replace free text, `convergent xN` annotation replaces the label-entropy class gate, personas receive a deterministic committed-context block, and every run appends an integrity provenance line to `feature-requests/research-runs.jsonl` verifiable via `research_preflight.py --verify-promotion`. (REQ-YG-623)
