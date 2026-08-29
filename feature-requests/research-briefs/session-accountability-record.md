# Problem brief: no session-scoped accountability record — prompt, intent, model, repo, and cost are never joined

**Prior art:** FR-743 (platform-contract probe: SessionStart / UserPromptSubmit /
Stop measured, stdin schemas recorded in `.github/hooks/logs/audit.jsonl`);
FR-425 (classify-emit fire-and-forget DGRAM to a classifier daemon — emit
path exists, classification consumer was daemon-scoped); FR-446 family /
session-introspection skill (`scripts/vscode/ledger.py` reconstructs
token/cost history forensically, after the fact, across all workspaces).

## Problem statement

Nothing records, per agent session, what was asked, with what intent, on
which model, in which repo, and what it cost. The pieces all exist but are
never joined at session scope:

- The platform fires `UserPromptSubmit` (stdin carries the verbatim
  `prompt`), `SessionStart` (stdin carries `model`), and `Stop` (fires when
  the agent finishes a turn; stdin carries `session_id`, `transcript_path`,
  but no usage fields) — measured by the FR-743 probe on 2026-07-18 and
  recorded in `.github/hooks/logs/audit.jsonl`. Since that probe, these
  events have had no consumer beyond the SessionStart briefing.
- Token and cost data live outside the repo in VS Code workspace storage
  (`chatSessions/*.jsonl` per-request promptTokens/outputTokens; price
  sheet in `debug-logs/*/models.json`). `ledger.py` proves the join is
  computable — but only as a manual, all-workspaces forensic query, not as
  a per-session record produced at the moment the session runs.
- The intent of a prompt (new feature, bug fix, question, release,
  refactor, reflection…) is never captured anywhere; usage analysis by
  intent class is impossible without re-reading transcripts.

The consequence: budget accountability ("this session cost X and was spent
on Y") requires archaeology across three stores, and the operator — who
consumes a large share of a shared department inference budget — cannot
answer "what did today's sessions do and what did each cost" without
running forensic scripts and reading transcripts. A session leaves no
self-describing ledger entry behind.

## Classification

measurement

## Constraints

- Hook scripts run synchronously inside the agent lifecycle; latency added
  to `UserPromptSubmit` is paid on every prompt of every session. FR-743
  set the precedent budget: hard timeout, fail-open, exit 0 on any
  failure — a lifecycle hook that blocks or breaks the session is worse
  than no record.
- The `Stop` event stdin carries NO usage fields (measured stdin keys:
  `cwd`, `hook_event_name`, `session_id`, `stop_hook_active`, `timestamp`,
  `transcript_path`). Any cost figure must be joined from external stores
  (workspace storage) or from the transcript, and those stores may lag the
  event.
- `promptTokens` conflates cache reads with fresh input (billed ~10×
  apart) — cost figures are ranges, not points (session-introspection
  skill, measured 2026-07-16). A record that prints a false-precision
  point cost is a plausible wrong answer.
- Verbatim prompts can contain secrets; the FR-425 emit path redacts
  KEY/TOKEN/SECRET/PASSWORD patterns before anything leaves the hook.
  The same boundary applies to any prompt capture.
- `.github/hooks/logs/` is gitignored for `*.jsonl`; whether the new
  record is committed or local is a policy decision with privacy
  consequences either way.
- No LLM call may sit synchronously in a lifecycle hook path (FR-425
  solved this with fire-and-forget DGRAM to a daemon; FR-743 banned LLM
  from the briefing path outright). Intent classification is an LLM-shaped
  task; where it executes is constrained by the latency budget.
- Multiple sessions run in parallel in this workspace (measured peak: 6
  same-hour sessions); a shared append target is a write-contention
  boundary — the record must be session-scoped or append-atomic.
- Scripture: normalize at the boundary where external data enters;
  `gate_checks_shape_not_substance` — a record that exists but says
  nothing (empty intent, missing cost) is compliance theatre.

## Witnessed incidents

- 2026-07-18, `.github/hooks/logs/audit.jsonl` (FR-743 probe records):
  `UserPromptSubmit` fired with the full prompt on stdin; `Stop` fired at
  agent finish. Both events measured, schema recorded — and since then
  consumed by nothing that produces a durable per-session record.
- 2026-07-16, session-introspection skill "Facts worth knowing": cost
  history is reconstructible only by `ledger.py` across all workspaces;
  the chronicle DB indexes debug-logs vacuously ("indexed ≠ informative");
  per-session narrative lives only in chatSessions titles.
- 2026-08-29 (this session): the operator asked what sessions cost and
  what they were for; answering requires joining audit.jsonl, chatSessions
  JSONL, and models.json by hand — no artifact exists that any session
  wrote about itself.
