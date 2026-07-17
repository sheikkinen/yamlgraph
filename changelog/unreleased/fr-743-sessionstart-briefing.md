---
type: feat
scope: hooks
---
- **FR-743 SessionStart Briefing Hook**: `now.py --brief` (≤15-line
  headline briefing, per-seam degradation) delivered fail-open at
  session start via `session-briefing.sh`; `session-probe.sh` records
  the platform contract for SessionStart + the two bundle-discovered
  events (UserPromptSubmit, SessionEnd) to audit.jsonl. Probe verdict
  and receipt witness pend the first fresh session.
