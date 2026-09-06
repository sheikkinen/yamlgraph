# Chaplain System Context

> FSM-based automation runtime for the YAMLGraph development lifecycle.
> Updated: 2026-05-19

## Overview

The Chaplain system automates feature delivery from GitHub Issue intake through PR merge. Two FSM instances (dispatcher + pipeline worker) orchestrate a Plan → Judge → Enforce → Micro-Remediate → Validate → Merge lifecycle, using YAMLGraph graphs for LLM steps and shell scripts for git/CI operations.

| Component | Role | Location |
|-----------|------|----------|
| **Dispatcher FSM** | Poll inbox, queue topics | `.chaplain/config/watcher-dispatcher.yaml` |
| **Pipeline FSM** | Plan → Judge → Enforce → Merge per topic | `.chaplain/config/watcher-pipeline-v2.yaml` |
| **Shell library** | Git, CI, cleanup primitives | `.chaplain/lib/watcher/` |
| **Custom actions** | FSM action implementations | `.chaplain/actions/` |
| **YAMLGraph graphs** | LLM-powered plan/judge/enforce/forensic | `.chaplain/graphs/` |
| **Philosopher** | Diary pattern scanner, graduation proposer | `.chaplain/philosopher.sh` + `graphs/philosopher/` |
| **Inquisitor** | Commit audit against Scripture | `.chaplain/inquisitor.sh` |

```
GitHub Issue (chaplain label)
    ↓ inbox_sync.sh
.chaplain/inbox/gh-XXX.md
    ↓ Dispatcher FSM
.chaplain/processing/gh-XXX.md
    ↓ Pipeline FSM (plan → judge → enforce → micro-remediate → validate → merge)
    ├→ SUCCESS → .chaplain/done/gh-XXX.md
    └→ FAILURE → .chaplain/failed/gh-XXX.md
```

---

## Dispatcher FSM

**Config:** `.chaplain/config/watcher-dispatcher.yaml`

Sequential polling controller. Discovers topics in inbox, spawns pipeline worker for each.

**States:** `idle` → `syncing_inbox` → `processing_topic` → `idle` (loop)

| Transition | Trigger | Action |
|------------|---------|--------|
| idle → syncing_inbox | `timeout(10)` | Poll every 10s |
| syncing_inbox → processing_topic | `topic_found` | Move topic to processing/, spawn pipeline FSM |
| syncing_inbox → idle | `no_topics` | Inbox empty |
| processing_topic → idle | `topic_done` / `error` | Pipeline completed or failed |
| \* → stopped | `stop` | Graceful shutdown |

**Key actions:**
- `syncing_inbox`: Calls `inbox_sync.sh`, finds first `*.md` in inbox/, moves to processing/
- `processing_topic`: Spawns `statemachine .chaplain/config/watcher-pipeline-v2.yaml` (timeout 1800s)

---

## Pipeline FSM

**Config:** `.chaplain/config/watcher-pipeline-v2.yaml`

Executes the full lifecycle for a single topic/FR.

```
setup → plan → capture_fr → judge ──┐
                            ↑ revise│
                            └───────┘
                                    ↓
                          enforce_session
                                    ↓
                          micro_changelog
                                    ↓
                            micro_title
                                   ↓
                          sanity_check → validate_gate → done → completed
                                             ↑
                                             │ fix_needed (max 5)
                                             └── validate_fix → sanity_check
                          (all errors) → failed → stopped
```

### Pipeline Actions

| State | Type | Tool | Timeout | Purpose |
|-------|------|------|---------|---------|
| `setup` | bash_context | preflight.sh + worktree_setup.sh | 30s | Branch + worktree creation |
| `plan` | yamlgraph_async | step-plan-unified.yaml | 600s | FR draft + research + tests + verify-red |
| `capture_fr` | bash_context | git diff/ls-files | 10s | Find newest FR path |
| `judge` | yamlgraph_async | step-judge-v2.yaml | 600s | Fresh session, different model |
| `enforce_session` | yamlgraph_async | enforce-session.yaml | 3600s | Implement changes |
| `micro_changelog` | changelog_gen | Python action | 30s | Deterministic changelog fragment remediation |
| `micro_title` | bash | git commit title repair | 30s | Deterministic Conventional Commit + FR title repair |
| `validate_fix` | yamlgraph_async | validate-session.yaml | 600s | Precommit/pytest remediation |
| `sanity_check` | yamlgraph_async | sanity-check-session.yaml | 1200s | Post-validate review + diary |
| `validate_gate` | validate_gate | Python action | — | Deterministic gate (max 5 retries) |
| `done` | bash | push/create PR/wait CI/merge/cleanup | 300s | Push → PR → merge |
| `failed` | bash | Move to .chaplain/failed/ | — | Cleanup on failure |

### Three-Model Separation

| Phase | Model | Rationale |
|-------|-------|-----------|
| Plan | gpt-5.3-codex | Planning + research |
| Judge | claude-sonnet-4 | Fresh eyes, prevents anchoring bias |
| Enforce | gpt-5.3-codex | Implementation |

### Judge Loop

`judge` can emit: `APPROVE` → proceed, `AMEND`/`SPLIT` → revise → re-plan, `REJECT` → fail.

### Validate Loop

`validate_gate` runs up to 5 times. On failure: `fix_needed` → `validate_fix` → retry. After 5: move to `failed`.

### Post-Enforce Micro-Remediation

Before deterministic gate validation, pipeline v2 now runs two cheap idempotent repair steps:

1. `micro_changelog`: generate a missing changelog fragment via `changelog_gen_action.py`.
2. `micro_title`: repair latest commit title contract when needed (`feat` must include `FR-XXX`).

If either micro-step fails, control falls back to `validate_fix`.

---

## Graphs

### Plan Graphs — `.chaplain/graphs/watcher-plan/`

| Graph | Purpose |
|-------|---------|
| `step-plan-unified.yaml` | Unified FR drafting + research + tests + verify-red (single copilot session) |
| `step-judge-v2.yaml` | FR evaluation with different model (no anchoring) |

**Prompts:** `plan-unified.yaml`, `plan.yaml`, `research.yaml`, `write-acceptance-tests.yaml`, `judge.yaml`, `summarize.yaml`

### Enforce Graphs — `.chaplain/graphs/watcher-enforce/`

| Graph | Purpose |
|-------|---------|
| `enforce-session.yaml` | Context planning → assemble → implement (FR-337) |
| `validate-session.yaml` | Precommit/pytest remediation |
| `sanity-check-session.yaml` | Post-validate review: FR/code alignment, diff proportionality, diary |

**Enforce flow:** Load module map → Plan context (Inception Mercury-2) → Assemble context → Enforce (gpt-5.3-codex)

**Tools:** `load_module_map_tool`, `assemble_context_tool`

### Diary Graph — `.chaplain/graphs/watcher-diary/graph.yaml`

Single copilot node: reads topic, writes diary reflection (FR-273).

### Forensic Graph — `.chaplain/graphs/watcher-forensic/graph.yaml`

Copilot node with full tool access: analyzes pipeline failures (FR-285). Input: `failure_reason`, `topic_content`, `log_files`, `worktree_state`.

### Philosopher Graph — `.chaplain/graphs/philosopher/graph.yaml`

10-phase diary scanner for pattern graduation:

```
scan → analyze → distill → unwrap_distill → challenge → unwrap_challenge
  → propose → load_context → reflect → write_diary
```

- Scans `docs/diary/` for **Trap:**, **Heuristic:**, **Seed:** markers
- Distills strongest candidate, runs devil's advocate gate (FR-195)
- Approved proposals → `.chaplain/inbox/` for pipeline admission
- Writes philosopher's own diary entry

**Usage:**
```bash
.chaplain/philosopher.sh              # Run once
.chaplain/philosopher.sh --once       # Explicit once mode
```

---

## Shell Library — `.chaplain/lib/watcher/`

| Script | Purpose |
|--------|---------|
| `common.sh` | Shared logging (`log_info`, `log_warn`, `log_error`) |
| `inbox_sync.sh` | Import GitHub issues with `chaplain` label, filter by author allowlist |
| `dedup_gate.sh` | Skip already-merged FRs before cycle admission |
| `preflight.sh` | Environment checks, hook integrity, stale worktree cleanup |
| `worktree_setup.sh` | Create git worktree + branch from main |
| `worktree_teardown.sh` | Remove worktree with corruption guards, reconcile main |
| `create_pr.sh` | Create or reuse PR for a branch |
| `wait_ci.sh` | Poll CI status (30s interval, 600s timeout) |
| `merge_pr.sh` | Squash merge via `gh` CLI |
| `post_merge.sh` | Resolve FR token, move topic to done/, reconcile local main |
| `metrics.sh` | Emit cycle timing metrics to `tmp/pipeline-metrics/` |
| `finalize_lib.sh` | Extract FR metadata, create changelog fragment, update FR status, diary stub |

### Additional Tools

| File | Purpose |
|------|---------|
| `lib/watcher/diary.py` | Write diary entries to `docs/diary/` |
| `lib/watcher/worktree.py` | Worktree creation tool (force-add drafts, symlink .venv) |

---

## Custom FSM Actions — `.chaplain/actions/`

| Action | Purpose |
|--------|---------|
| `bash_context_action.py` | Run bash, parse JSON stdout into context |
| `git_commit_action.py` | Stage + commit with hook retry |
| `yamlgraph_async_action.py` | Execute yamlgraph graph, route output to FSM events |
| `changelog_gen_action.py` | Generate changelog fragment from FR metadata |
| `verify_red_action.py` | Run pytest expecting failure (TDD RED) |
| `validate_gate_action.py` | Deterministic CI-parity gate (pre-commit, title, branch, diary) |
| `precommit_action.py` | Run pre-commit with retry on hook auto-fixes |
| `failure_cleanup_action.py` | Move failed topic to `.chaplain/failed/` |

---

## Philosopher & Inquisitor

### Philosopher (`.chaplain/philosopher.sh`)

Nightly scanner for recurring diary patterns. Proposes graduations to Scripture.

| Variable | Default | Purpose |
|----------|---------|---------|
| `DIARY_DIR` | `docs/diary` | Diary source |
| `INBOX` | `.chaplain/inbox` | Proposal output |
| `LOOKBACK_DAYS` | `30` | Scan window |
| `GRADUATION_THRESHOLD` | `3` | Minimum recurrences to propose |

### Inquisitor (`.chaplain/inquisitor.sh`)

Audit daemon reviewing recent commits against the Scripture.

**Phases:** Gather evidence → Investigate (Conventional Commits, CHANGELOG, ARCHITECTURE, tests, diary, noqa) → Judge (✓ COMPLIANT / ⚠ DRIFT / ✗ VIOLATION) → Record diary entry

**Gates:**
- Worktree gate (FR-142): Skip in worktrees (enforce in progress)
- Commit-delta gate (FR-131): Skip if no feat/fix since last audit

**Flags:** `--force` (override worktree gate), `--propose` (write fix proposals to inbox)

---

## Scripts — `.chaplain/scripts/`

| Script | Purpose |
|--------|---------|
| `start-system.sh` | Full startup: cleanup → validate → diagrams → start UI (port 3001) → start dispatcher |
| `pipeline-status.sh` | Queue counts, active worktrees, log summaries, open PRs |
| `clean-worktree.sh` | Remove worktree + branches for given issue numbers |

### Starting the System

```bash
.chaplain/scripts/start-system.sh
# Optional inbox override:
.chaplain/scripts/start-system.sh --inbox .chaplain/inbox
```

**Output:** Web UI at `http://localhost:3001`, dispatcher polling inbox every 10s.

### Checking Status

```bash
.chaplain/scripts/pipeline-status.sh        # Overview
.chaplain/scripts/pipeline-status.sh 339    # Detailed for gh-339
```

---

## State & Configuration

### ID Registry (`.chaplain/id-registry.yaml`)

Monotonically increasing IDs for CAP-XX and REQ-YG-XXX (FR-180).

### Author Allowlist (`.chaplain/allowed-authors.txt`)

One author per line. Used by `inbox_sync.sh` to filter issues (FR-251).

### Queue Directories

| Directory | Purpose |
|-----------|---------|
| `.chaplain/inbox/` | Topics awaiting pipeline admission |
| `.chaplain/processing/` | Topic currently being processed |
| `.chaplain/done/` | Completed topics |
| `.chaplain/failed/` | Failed topics |
| `.chaplain/drafts/` | Plan-phase drafts |
| `.chaplain/inbox-fsm/` | FSM-specific inbox (alternative) |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `POLL` | `10` | Dispatcher poll interval (seconds) |
| `TIMEOUT_CI` | `1800` | CI wait timeout (seconds) |
| `METRIC_DIR` | `tmp/pipeline-metrics` | Metrics output directory |
| `BODY_SIZE_CAP` | `10000` | Max synced issue body size |

---

## Logging & Debugging

### Log Files

```
logs/
├── fsm-ui.log                 — Web UI lifecycle
├── fsm-dispatcher.log         — Dispatcher FSM events
├── fsm-pipeline-gh-XXX-*.log  — Pipeline worker logs
└── philosopher-YYYY-MM-DD.log — Philosopher daemon log
```

### FSM Validation

```bash
statemachine-validate .chaplain/config/watcher-dispatcher.yaml
statemachine-validate .chaplain/config/watcher-pipeline-v2.yaml
```

### Retrying Failed Topics

```bash
rm .chaplain/failed/gh-XXX.md
git worktree remove tmp/worktrees/feat/watcher2-gh-XXX --force
git branch -D feat/watcher2-gh-XXX && git push origin --delete feat/watcher2-gh-XXX
gh issue edit XXX --add-label chaplain
```

---

## Design Patterns

| Pattern | Description |
|---------|-------------|
| **Three-model separation** | Plan/Judge/Enforce use different LLMs to prevent anchoring bias |
| **Validate loop with ceiling** | `validate_gate` retries up to 5 times before failing |
| **Context substitution** | FSM context dict populates `{var}` in action commands |
| **Idempotent operations** | All shell scripts safe to re-run (worktree, changelog, diary) |
| **Post-merge reconciliation** | FR token resolution, topic queue cleanup, local main rebase |
| **Graph chaining** | FSM actions invoke YAMLGraph graphs as subprocesses |
| **Author allowlist** | Inbox sync filters by allowed-authors.txt (FR-251) |

---

## Cross-References

- [.chaplain/README.md](../../.chaplain/README.md) — Runtime README
- [CLAUDE.md](../../CLAUDE.md) — Dev commands and architecture
- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) — The Scripture
- [docs/letter-to-the-philosopher.md](../letter-to-the-philosopher.md) — Philosopher identity document
- [.chaplain/docs/fsm-diagrams/](../../.chaplain/docs/fsm-diagrams/) — Generated FSM diagrams
- [capabilities/CAP-128-chaplain-documentation.yaml](../../capabilities/CAP-128-chaplain-documentation.yaml) — Documentation capability spec
