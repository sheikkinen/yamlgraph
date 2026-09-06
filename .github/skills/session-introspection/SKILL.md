---
name: session-introspection
description: "Situation awareness across parallel agent sessions. Use when: starting work in this workspace, checking what other sessions are active right now, avoiding parallel-session git collisions (one_session_one_repo), seeing FRs in motion, reconstructing token/cost history, or introspecting VS Code session stores."
---

# Session Introspection — the situation board and its siblings

Spike suite in `scripts/vscode/` (stdlib-only, read-only). Run these
BEFORE starting multi-commit work in a shared repo, and whenever you
need to know what the other live sessions are doing.

## The one to run first

```bash
python3 scripts/vscode/now.py            # last 8h; --window 2 for tighter
```

Prints: live sessions (titles, models, recency) × git state per
implicated repo — branch, **staged files (the interleave tripwire)**,
recent commits with FR/NC refs — × FRs in motion with statuses, plus an
explicit `⚠ INTERLEAVE HAZARD` flag when a repo has staged work and
multiple live sessions. This is the `one_session_one_repo` staged-check
ritual as one command.

Answers before you act:
- Is another session already judging/enforcing the FR I'm about to touch?
- Is there staged work in this repo that is not mine?
- What landed in the last hours that my context predates?

## The other angles

| Script | Question |
|---|---|
| `scripts/vscode/stores.py` | Where does session data live, how big, which workspaces active? |
| `scripts/vscode/ledger.py --by-model` | Requests/tokens/cost-range per day and per model, all workspaces |
| `scripts/vscode/session_ledger.py --csv --all-workspaces` | **What did each session do and cost, per request?** — exact vendor-persisted `copilotCredits` via full patch replay; prompts, per-turn summaries, model, workspace per row (FR-898). Markdown per session or pivot-ready CSV; `--session <id>`, `--window <hours>` |
| `scripts/vscode/portrait.py` | Recent session titles + measured same-hour concurrency per day |
| `scripts/vscode/timesheet.py --month YYYY-MM` | Day-grouped "what did I work on" report across a date range — repo, branch, one-line description per session (`--repo <substr>` to scope one project) |
| `python3 scripts/fr_board.py` (add `--project projects/ninchat_voice` for the cross-repo view) | **What's next?** — the plan-state board (FR-740), computed live from `feature-requests/*.md` and printed to stdout (FR-858 retired the committed cache): active FRs, gates with owners and pre-drafted questions, parse-failure rows exposing status lag. Run this BEFORE re-deriving priorities from FR files by hand |
| `docs/world-context.md` | **What's happening outside the repo?** — the world file (FR-744): distilled external context the philosopher grounds graduations against. `now.py` prints its pointer with age; the age label IS the scheduler — when it flags `⚠ STALE`, refresh with `yamlgraph graph run graphs/world_distill/graph.yaml --var date=$(date +%F)` |

## Facts worth knowing (measured 2026-07-16)

- Session data: `~/Library/Application Support/Code/User/workspaceStorage/<hash>/chatSessions/*.jsonl`
  — per-request timestamps, modelId, promptTokens/outputTokens. The
  price sheet lives in `debug-logs/*/models.json`.
- The chronicle DB indexes debug-logs (2-line markers) — vacuous;
  narrative lives in chatSessions titles (indexed ≠ informative).
- `promptTokens` conflates cache reads with fresh input (billed ~10×
  apart) — treat cost figures as ranges.
- Peak measured concurrency 6 same-hour sessions (2026-07-14) — the
  day of the recorded interleave incidents. Hazard is real, use the flag.

See `scripts/vscode/README.md` for the full store map and limits.
