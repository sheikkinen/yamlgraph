---
name: chaplain-ops
description: "Operate the Chaplain automation system. Use when: starting the chaplain, checking pipeline status, submitting proposals to inbox, debugging pipeline failures, retrying failed topics, cleaning worktrees, running the philosopher or inquisitor."
argument-hint: "'start', 'status', 'retry gh-XXX', or 'clean'"
---

# Chaplain Operations

Operate the FSM-based automation runtime for YAMLGraph development lifecycle. Canonical source: `docs/context/chaplain-system.md`.

## Architecture

```
GitHub Issue (chaplain label)
    ↓ inbox_sync.sh
.chaplain/inbox/gh-XXX.md
    ↓ Dispatcher FSM
.chaplain/processing/gh-XXX.md
    ↓ Pipeline FSM (plan → judge → enforce → validate → merge)
    ├→ SUCCESS → .chaplain/done/gh-XXX.md
    └→ FAILURE → .chaplain/failed/gh-XXX.md
```

**Two FSMs:**
- **Dispatcher** (`.chaplain/config/watcher-dispatcher.yaml`): Polls inbox every 10s, spawns pipeline worker per topic
- **Pipeline** (`.chaplain/config/watcher-pipeline-v2.yaml`): Plan → Judge → Enforce → Micro-Remediate → Validate → Merge

**Three-model separation:** Plan (gpt-5.3-codex) → Judge (claude-sonnet-4, fresh eyes) → Enforce (gpt-5.3-codex)

## Common Operations

### Start the System

```bash
.chaplain/scripts/start-system.sh
```

Starts: cleanup → validate → diagrams → web UI (port 3001) → dispatcher.

### Check Status

```bash
.chaplain/scripts/pipeline-status.sh          # Overview
.chaplain/scripts/pipeline-status.sh 339      # Detailed for gh-339
```

### Submit a Proposal

Write a markdown file to `.chaplain/inbox/`:

```bash
cat > .chaplain/inbox/refactor-state-builder.md << 'EOF'
Problem: State builder has grown to 450 lines.
Task: Split into state_builder.py and state_reducer.py.
EOF
```

**Remote submission:** Open a GitHub Issue with the `chaplain` label. `inbox_sync.sh` imports it automatically.

### Retry a Failed Topic

```bash
rm .chaplain/failed/gh-XXX.md
git worktree remove tmp/worktrees/feat/watcher2-gh-XXX --force
git branch -D feat/watcher2-gh-XXX && git push origin --delete feat/watcher2-gh-XXX
gh issue edit XXX --add-label chaplain
```

### Clean Worktrees

```bash
.chaplain/scripts/clean-worktree.sh 339 340 341
```

## Pipeline States

| State | Type | Timeout | Purpose |
|-------|------|---------|---------|
| `setup` | bash | 30s | Branch + worktree creation |
| `plan` | yamlgraph | 600s | FR draft + research + tests |
| `judge` | yamlgraph | 600s | FR evaluation (different model) |
| `enforce_session` | yamlgraph | 3600s | Implement changes |
| `micro_changelog` | python | 30s | Changelog fragment remediation |
| `micro_title` | bash | 30s | Commit title repair |
| `validate_fix` | yamlgraph | 600s | Pre-commit/pytest remediation |
| `sanity_check` | yamlgraph | 1200s | Post-validate review + diary |
| `validate_gate` | python | — | Deterministic gate (max 5 retries) |
| `done` | bash | 300s | Push → PR → merge |

Judge can emit: `APPROVE` → proceed, `AMEND`/`SPLIT` → revise, `REJECT` → fail.

## Queue Directories

| Directory | Purpose |
|-----------|---------|
| `.chaplain/inbox/` | Awaiting pipeline admission |
| `.chaplain/processing/` | Currently being processed |
| `.chaplain/done/` | Completed topics |
| `.chaplain/failed/` | Failed topics |
| `.chaplain/drafts/` | Plan-phase drafts |

## Philosopher & Inquisitor

### Philosopher

Scans `docs/diary/` for recurring patterns, proposes graduations to Scripture:

```bash
.chaplain/philosopher.sh
```

### Inquisitor

Audits recent commits against the Scripture:

```bash
.chaplain/inquisitor.sh
.chaplain/inquisitor.sh --force      # Override worktree gate
.chaplain/inquisitor.sh --propose    # Write fix proposals to inbox
```

## Debugging

### Log Files

```
logs/
├── fsm-dispatcher.log
├── fsm-pipeline-gh-XXX-*.log
└── philosopher-YYYY-MM-DD.log
```

### FSM Validation

```bash
statemachine-validate .chaplain/config/watcher-dispatcher.yaml
statemachine-validate .chaplain/config/watcher-pipeline-v2.yaml
```

## Key Components

| Component | Location |
|-----------|----------|
| Dispatcher config | `.chaplain/config/watcher-dispatcher.yaml` |
| Pipeline config | `.chaplain/config/watcher-pipeline-v2.yaml` |
| Shell library | `.chaplain/lib/watcher/` |
| Custom actions | `.chaplain/actions/` |
| Graphs | `.chaplain/graphs/` |
| ID registry | `.chaplain/id-registry.yaml` |
| Author allowlist | `.chaplain/allowed-authors.txt` |
