# Chaplain Automation Runtime

The `.chaplain/` directory contains the FSM-based Chaplain runtime and shell
library for topic intake, worktree lifecycle management, PR automation, and
forensic failure handling.

## Runtime Entrypoint

Start the system with:

```bash
.chaplain/scripts/start-system.sh
```

Optional inbox override:

```bash
.chaplain/scripts/start-system.sh --inbox .chaplain/inbox
```

## Architecture Overview

The active runtime is the FSM pair below:

1. **Dispatcher FSM**: `.chaplain/config/watcher-dispatcher.yaml`
2. **Pipeline worker FSM**: `.chaplain/config/watcher-pipeline-v2.yaml`

High-level flow:

```text
Inbox sync -> setup -> plan -> capture_fr -> judge -> enforce_session
          -> validate -> sanity_check -> precommit_check -> done
```

## Shell Library Reference

Reusable shell primitives live in `.chaplain/lib/watcher/`:

- `inbox_sync.sh` — sync GitHub issues with `chaplain` label to inbox
- `dedup_gate.sh` — merged-FR dedup gate before cycle admission
- `preflight.sh` — environment and hook integrity checks
- `worktree_setup.sh` — branch + worktree setup
- `worktree_teardown.sh` — safe teardown with corruption guards
- `create_pr.sh` — PR create/reuse logic
- `wait_ci.sh` — CI polling and result handling
- `merge_pr.sh` — squash merge handling
- `post_merge.sh` — post-merge inbox/topic reconciliation; resolves FR token (`FR-[0-9]+`) from PR title, scans inbox for matching files, moves them to `.chaplain/done/` (consumed-completed queue); checks merged PR state with `gh pr view --json state --jq '.state'`; moves merged topics from `.chaplain/processing/` to `.chaplain/done/` (missing processing topic is an explicit idempotent no-op; unmerged/unknown state skips processing cleanup); creates `.chaplain/done/` automatically when missing; reconciles local main after merge with `git stash push --include-untracked` → `git pull --rebase --quiet origin main` → conditional `git stash pop`. This contract moves merged topics from .chaplain/processing/ to .chaplain/done/.
- `metrics.sh` — cycle metrics emission

## Usage

Start services:

```bash
.chaplain/scripts/start-system.sh
```

Watch logs:

```bash
tail -f logs/fsm-dispatcher.log logs/fsm-ui.log
```

Submit a local topic:

```bash
echo "Implement feature X" > .chaplain/inbox/feature-x.md
```

## Environment and Configuration

Key environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `POLL` | `10` | Dispatcher poll interval (seconds) |
| `TIMEOUT_CI` | `1800` | CI wait timeout (seconds) |
| `METRIC_DIR` | `tmp/pipeline-metrics` | Metrics output directory |
| `BODY_SIZE_CAP` | `10000` | Max synced issue body size |

Required tools: `gh`, `jq`, `yamlgraph`, `pre-commit`, `statemachine-*`.

## Troubleshooting

### Startup failures

- Check syntax and executable bit:
  - `bash -n .chaplain/scripts/start-system.sh`
  - `ls -l .chaplain/scripts/start-system.sh`
- Validate FSM configs:
  - `statemachine-validate .chaplain/config/watcher-dispatcher.yaml`
  - `statemachine-validate .chaplain/config/watcher-pipeline-v2.yaml`

### Worktree/setup failures

- `git worktree prune`
- Ensure clean main working tree before cycle admission.

### CI/merge failures

- `gh pr checks <PR_NUMBER>`
- `bash .chaplain/lib/watcher/wait_ci.sh --pr <PR_NUMBER>`

## Forensic and Failure Workflow Mapping

After watcher2 retirement, failure handling maps as follows:

1. **Dispatcher phase** moves picked topics into `.chaplain/processing/`.
2. **Pipeline failure transition** moves topics to `.chaplain/failed/`.
3. **Forensic graph** remains at `.chaplain/graphs/watcher-forensic/graph.yaml`.
4. **Diary instrumentation** remains in `.chaplain/lib/diary.py`.
5. **Failure artifacts** are preserved for investigation; no silent cleanup path.

## Retry/Requeue Failed GitHub Topics

When retrying a failed `gh-<NUM>.md` topic, run:

```bash
rm .chaplain/failed/gh-<NUM>.md
git worktree remove tmp/worktrees/feat/watcher2-gh-<NUM> --force
git branch -D feat/watcher2-gh-<NUM> && git push origin --delete feat/watcher2-gh-<NUM>
gh issue edit <NUM> --add-label chaplain
```

`inbox_sync.sh` skips issues already present in `.chaplain/failed/`,
`.chaplain/processing/`, or `.chaplain/inbox/`. Removing the failed marker first
is mandatory for re-import.
