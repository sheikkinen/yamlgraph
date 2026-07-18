---
type: feat
scope: hooks
---
- **FR-743 SessionStart Briefing Hook**: `now.py --brief` (≤15-line
  headline briefing, per-seam degradation) delivered fail-open at
  session start via `session-briefing.sh`; `session-probe.sh` records
  the platform contract for SessionStart + the two bundle-discovered
  events (UserPromptSubmit, SessionEnd) to audit.jsonl. Probe verdict
  and receipt witness pend the first fresh session. A1: probe widened
  to six events — **PreCompact** (the flush-before-guillotine moment),
  PostCompact (mechanical compaction-witness recording), and
  PostToolUseFailure, all found in the runtime bundle and absent from
  our hooks documentation. A2: the canonical enums located — **16 hook
  events across two subsystems** (Stop, SubagentStart/Stop,
  TeammateIdle, TaskCreated/Completed, PermissionRequest, Notification
  …) vs 3 documented; the probe now registers all 14 non-tool events.
- A3: probe reads full stdin (head -c truncation broke JSON on
  long prompts). Live telemetry: hooks load WITHOUT restart - 46
  UserPromptSubmit firings from 4 running sessions; stdin carries
  prompt + transcript_path.
