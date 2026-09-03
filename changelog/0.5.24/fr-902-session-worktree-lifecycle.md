---
type: feat
scope: hooks
req: REQ-YG-629
---
- **FR-902 Session Worktree Lifecycle**: every session gets its own git
  worktree lane (`session/<session-id>`) created idempotently on
  SessionStart (live-flag gated for human review), a PreToolUse ownership
  guard fencing writes to the owning lane, fenced per-turn checkpoint
  commits with `Session-Id`/`Request-Index` trailers on Stop, lossless
  `worktree.sh gc` for session lanes, session-lane listing in `now.py`,
  and `session_join.py` correlating requests to checkpoints with
  model/credit provenance. (REQ-YG-629)
