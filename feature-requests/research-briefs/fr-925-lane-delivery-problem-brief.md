# Problem brief: FR-902 lane exists but the agent never learns it

<!-- Closed input for the research route (FR-890). Incident record only;
     no solution content. -->

**Prior art:** filename-noun hits ("problem, brief") on census/corpus briefs are unrelated subject matter — not applicable. `fr-888-problem-brief.md` is genuine adjacent precedent (main-write guard; FR-902 built the lane this brief concerns); distinguished: this brief is about lane *delivery* to agent context, not write guarding.

## Problem statement

FR-902 creates an isolated git worktree ("lane") for every agent session
at SessionStart and denies out-of-lane writes at PreToolUse. Both halves
work. But the delivery half fails: the hook announces the lane with two
plain-stdout lines, and the editor captures SessionStart hook stdout
into telemetry and discards it — the message never enters the agent's
context. The hook's own comment promises a fallback ("briefing orders
after this hook"), but the session briefing carries no lane information
at all. The result: the agent works in the shared main checkout by
default, unaware its lane exists, until its first write-shaped command
trips the guard. Read-only work, analysis, and the terminal's working
directory stay silently out-of-lane for entire turns. Discovery today
depends on either a denial firing or the operator asking.

## Classification

enforcement/latency-critical

## Constraints

- SessionStart hook stdout is not delivered to agent context in VS Code
  Copilot; the one hook output channel proven to reach the agent is the
  structured `hookSpecificOutput` JSON used by the PreToolUse guard.
- The lane record already exists on disk per session
  (`.github/hooks/logs/session-lanes/<sid>.json`); the session id is
  derivable by the agent from its debug-log path.
- An interim advisory instruction now lives in copilot-instructions.md
  (commit b8fbd24d); any mechanical delivery must not contradict it.
- The lane guard must keep denying genuinely out-of-lane writes; fixing
  the false positive must not open a hole where a command claims a lane
  cwd it does not use.
- Hooks are fail-open on their own errors and bounded by short
  timeouts; no daemon, no background watcher.
- Live-gating discipline applies: behavior changes to hooks ship dark
  and are armed by the operator (`fr902.live` precedent).

## Witnessed incidents

- Session 9acc40e0 (2026-08-30): SessionStart hook ran ok (audit:
  approve/lane ready, lane record written), yet turn 1's LLM request
  contains zero occurrences of "session lane" / "Work there" — verified
  in the session debug log. The agent ran its whole first turn in the
  main checkout; the operator had to ask "are we in worktree".
- Diary 2026-08-30 ("the binding that passed every test and delivered
  nothing"): the same trap class — every component green, the seam
  between surface and consumer unexercised — recorded twice in one day
  for FR-904/FR-905 before recurring here.
