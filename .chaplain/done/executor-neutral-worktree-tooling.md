# Executor-Neutral Git Worktree Tooling (wt)

## Problem

Three parallel worktree implementations exist, none shared, none operator-facing:

1. `.chaplain/lib/watcher/worktree_setup.sh` / `worktree_teardown.sh` — chaplain FSM only.
   Coupled to topics (`--topic <file>`), hardcodes `feat/watcher2-` branch prefix, emits
   JSON for `bash_context_action`.
2. `scripts/copilot_instrument.sh` — own disposable-worktree logic under
   `tmp/copilot-instrumentation/`, own teardown.
3. `.chaplain/scripts/clean-worktree.sh` — issue-number-based cleanup only.

The chaplain teardown embeds incident-paid knowledge the manual path cannot reach:
`core.bare=true` corruption repair (FR-139), stale `.pth` cleanup (FR-174), editable-install
revalidation (FR-241), venv symlinking, merged-PR collision guard (FR-275). Raw `git worktree`
commands in a manual session would re-hit every one of those mines.

Meanwhile the FR-662 pre-command-guard blocks `git checkout -b` / `git switch -c` in the main
worktree but permits `git worktree add -b` — the lane for isolated manual work exists but is
unpaved. The denial message offers only "commit to main" or "submit to inbox", omitting the
third option the hook itself allows. Result (measured 2026-05-01..07-07): 83% of commits are
direct-to-main; isolation costs either ~2h pipeline latency or a minefield.

## Proposal

Extract one executor-neutral worktree lifecycle tool, e.g. `scripts/worktree.sh` (alias `wt`):

- `wt new <name>` — worktree + branch from main under `tmp/worktrees/`, venv symlink,
  merged-PR collision guard (logic extracted from `.chaplain/lib/watcher/worktree_setup.sh`)
- `wt spike <name>` — same, marked disposable: no FR expected, teardown without PR; on
  removal require a one-line diary note stating what the spike taught (productive-failure
  vocabulary for exploration)
- `wt list` — worktree inventory with branch + age (extend what
  `.chaplain/scripts/pipeline-status.sh` half-does)
- `wt rm <name>` — full teardown with FR-139/FR-174/FR-241 self-healing (extracted from
  `worktree_teardown.sh`)

Consumers converge on the shared tool:

- `.chaplain/lib/watcher/worktree_setup.sh` / `worktree_teardown.sh` become thin wrappers
  (topic → name mapping + FSM JSON envelope preserved — no chaplain behavior change)
- `scripts/copilot_instrument.sh` uses `wt new`/`wt rm` instead of private logic
- FR-662 denial message in `.github/hooks/scripts/pre-command-guard.sh` gains the third
  option: "For isolated manual work: scripts/worktree.sh new <name>"

## Acceptance criteria

- Single source of truth for worktree create/teardown; watcher shell behavior unchanged
  (existing pipeline tests / a dry-run of setup+teardown prove parity)
- `wt rm` applies all three self-healing steps (bare-corruption, stale .pth, editable install)
- `wt spike` teardown prompts/records a diary line; no FR or PR required for spikes
- Hook message updated; hook still denies bare `checkout -b`/`switch -c` in main worktree
- No new dependencies; bash + existing helpers only

## Non-goals

- No change to FSM states or pipeline flow
- No auto-PR/auto-merge for manual worktrees — merging stays the operator's judgement
- Not a git porcelain replacement; only the lifecycle verbs above

## Context

Origin: diary-2026-07-07-the-scribe-bypasses-the-scripture.md (manual-vs-chaplain reflection;
83/17 split; spike-mode seed) and docs/development-process.md §3.1. This harmonizes the two
executors at their shared boundary: latency (one command each way), task shape (spike mode
legitimizes failable prototypes), transaction cost (no PR ceremony for isolation).
