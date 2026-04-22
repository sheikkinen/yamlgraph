# Watcher Pipeline Refactor Plan (v3 — rewrite)

This document is the implementation plan for the watcher2 pipeline.
Replaces monolithic `watch.sh` + separate enforce/bugfix scripts with a single orchestrator.

---

## 1) Objective

Single orchestrator (`watcher2.sh`) that:

- polls inbox for work
- isolates all work in a git worktree (planning, enforcement, audit — everything)
- merges via PR, waits for CI, cleans up on success
- logs all failures visibly; never silently suppresses

---

## 2) Scope

### In scope

- new `watcher2.sh` orchestrator
- sourced shell libraries in `.chaplain/lib/`
- yamlgraph copilot/LLM invocations for planning, enforcement, audit
- worktree lifecycle: create → work → PR → CI → merge → teardown

### Out of scope

- Python orchestration replacement
- FR lifecycle semantics changes
- Chaplain graph topology redesign

---

## 3) Pipeline Flow

```
watcher2.sh (polling loop on main)
  │
  │ ── poll ──────────────────────────────────────────────────
  │
  ├─ source lib/inbox_sync.sh         # GH issue import → inbox/
  ├─ pick next inbox item             # exit loop iteration if empty
  │
  │ ── worktree ──────────────────────────────────────────────
  │
  ├─ source lib/preflight.sh          # prune stale worktrees/branches
  ├─ source lib/worktree_setup.sh     # create worktree + branch from main
  ├─ cd into worktree                 # ALL subsequent work happens here
  │
  │ ── plan (copilot session 1) ──────────────────────────────
  │
  ├─ yamlgraph: plan                  # new session — read topic, draft FR
  ├─ yamlgraph: research              # resume — gather evidence
  ├─ yamlgraph: write_acceptance      # resume — failing tests (RED)
  ├─ pytest: run tests (expect failures) # enforce TDD discipline
  ├─ yamlgraph: judge                 # resume — approve/reject FR
  ├─ [if rejected → teardown, continue]
  ├─ commit after each step. precondition: FR and only FR edited so far, no other work. commit message: "chore: FR-XXX <one-line description>"
  │
  │ ── enforce (copilot session 2) ───────────────────────────
  │
  ├─ yamlgraph: implement             # new session — TDD red→green
  ├─ yamlgraph: test_and_demo         # resume — run tests, create demos
  ├─ yamlgraph: critique_and_distill  # resume — evaluate, write diary
  ├─ shell script: finalize           # pre-commit, commit, push
  ├─ yamlgraph: fix finalize          # resume if needed — pre-commit, commit, push
  ├─ commit after each step.
  │
  │ ── audit (copilot session 3) ─────────────────────────────
  │
  ├─ yamlgraph: inquisitor            # new session — audit findings → docs/diary
  ├─ commit.
  │
  │ ── merge ─────────────────────────────────────────────────
  │
  ├─ source lib/create_pr.sh          # gh pr create
  ├─ source lib/wait_ci.sh            # poll CI status until pass/fail
  ├─ [if CI fail → log, keep worktree, continue]
  ├─ source lib/merge_pr.sh           # gh pr merge --squash
  │
  │ ── cleanup ───────────────────────────────────────────────
  │
  ├─ cd back to main repo
  ├─ source lib/worktree_teardown.sh  # remove worktree, prune branch
  ├─ source lib/post_merge.sh         # close GH issue, finalization
  ├─ source lib/metrics.sh            # emit pipeline timing JSON
  │
  └─ sleep, next iteration
```

---

## 4) Key Design Decisions

### 4.1 Everything in the worktree

All yamlgraph operations (plan, enforce, inquisitor) run inside the worktree.
This means:
- FR file is created and committed in the branch, not on main
- Tests are written and run in the branch
- Diary entries, changelog fragments — all in the branch
- Main stays clean until merge

### 4.2 Diary after every yamlgraph step

After each yamlgraph node, a small copilot node resumes the same session and appends a diary entry to `docs/diary/`. This captures reasoning, decisions, and context while the session is still warm — no separate summarization pass needed.

### 4.3 Session model

| Phase group | Session | Where |
|---|---|---|
| plan → research → acceptance → judge (+ diary after each) | session 1 (resume chain) | worktree |
| implement → test → critique → finalize (+ diary after each) | session 2 (resume chain) | worktree |
| inquisitor (+ diary) | session 3 (independent) | worktree |
| shell phases (preflight, worktree, CI, merge) | no LLM | main or worktree |

### 4.3 Git operations

| Operation | Who | Where |
|---|---|---|
| create branch + worktree | `lib/worktree_setup.sh` | main repo |
| all commits during work | copilot `finalize` node | worktree |
| push branch | copilot `finalize` node | worktree |
| create PR | `lib/create_pr.sh` | either (uses `gh`) |
| wait for CI | `lib/wait_ci.sh` | either (uses `gh`) |
| squash merge | `lib/merge_pr.sh` | either (uses `gh`) |
| remove worktree + branch | `lib/worktree_teardown.sh` | main repo |
| pull main after merge | `lib/worktree_teardown.sh` | main repo |

### 4.4 Failure modes

| Failure | Action |
|---|---|
| FR rejected by judge | teardown worktree, continue to next item |
| copilot node fails | log, teardown worktree, continue |
| CI fails | log, keep worktree for inspection, continue |
| merge conflict | log, keep worktree, continue |
| shell preflight fails | hard fail cycle, retry next poll |

### 4.5 Design rules

- Each `lib/*.sh` is stateless: reads env vars, writes stdout/files.
- Orchestrator owns all control flow and error routing.
- No `2>/dev/null || true` on operations where failure matters.
- Bug vs feature routing: orchestrator checks FR type after judge, selects enforce graph variant.

---

## 5) Acceptance Criteria

1. All yamlgraph operations run inside a worktree, never on main.
2. PR is created, CI passes, and merge completes before worktree removal.
3. Rejected FRs trigger clean teardown without merge attempt.
4. CI failure preserves the worktree for manual inspection.
5. No silent failure suppression on git or gh operations.
6. Pipeline metrics emitted for every cycle (success and failure).

---

## 6) Risks and Controls

- **Risk:** CI polling hangs forever.
  **Control:** timeout in `wait_ci.sh`; teardown on timeout.

- **Risk:** worktree accumulation on repeated CI failures.
  **Control:** `preflight.sh` prunes worktrees older than N hours.

- **Risk:** copilot commits to wrong branch/repo.
  **Control:** worktree isolation guarantees branch. Validate `git branch --show-current` before commit.

- **Risk:** race between inbox poll and worktree work.
  **Control:** move inbox file to processing dir before starting; single-threaded loop.

---

## 7) Enabling Feature: `--start-node` + `--state-file`

Watcher2 requires running shell scripts between copilot nodes while preserving session state.
This needs a new yamlgraph CLI capability: start a graph at a named node with pre-loaded state.

### 7.1 CLI interface

```bash
# Run a single node (or from a node to END)
yamlgraph graph run graph.yaml \
  --start-node implement \
  --state-file tmp/state.json \
  --stop-after implement \
  --full

# State file is written on exit (updated with node's output)
```

| Flag | Purpose |
|---|---|
| `--start-node <name>` | Begin execution at this node instead of START |
| `--state-file <path>` | Load state from JSON before run; write updated state after run |
| `--stop-after <name>` | Stop after this node completes (don't follow edges to next) |

### 7.2 State file format

```json
{
  "plan_result": {
    "output": "...",
    "session_id": "abc-123",
    "exit_code": 0,
    "backend": "cli",
    "model": "claude-sonnet-4.6"
  },
  "topic_file": ".chaplain/inbox/my-topic.md",
  "judge_result": null
}
```

- `CopilotResult` serializes to/from JSON (Pydantic `.model_dump()` / `.model_validate()`)
- State file is the contract between shell orchestrator and graph nodes
- Session IDs survive across invocations via the state file

### 7.3 Orchestrator usage

```bash
STATE="tmp/pipeline-state.json"

# Initialize state
echo '{"topic_file": "'$TOPIC'"}' > "$STATE"

# Plan phase — each step is a separate invocation with shell work in between
yamlgraph graph run .chaplain/graphs/watcher.yaml \
  --start-node plan --stop-after plan \
  --state-file "$STATE" --full

yamlgraph graph run .chaplain/graphs/watcher.yaml \
  --start-node research --stop-after research \
  --state-file "$STATE" --full

yamlgraph graph run .chaplain/graphs/watcher.yaml \
  --start-node write_acceptance --stop-after write_acceptance \
  --state-file "$STATE" --full

# Shell: verify RED tests
pytest tests/ -x --no-cov -q || echo "RED confirmed"

yamlgraph graph run .chaplain/graphs/watcher.yaml \
  --start-node judge --stop-after judge \
  --state-file "$STATE" --full

# Shell: check verdict, commit FR
source lib/check_verdict.sh "$STATE"
git add feature-requests/ && git commit -m "chore: FR-XXX draft"

# Enforce phase — new session, same state file
yamlgraph graph run .chaplain/graphs/watcher.yaml \
  --start-node implement --stop-after implement \
  --state-file "$STATE" --full

# Shell: run tests
pytest tests/ -q --no-cov

yamlgraph graph run .chaplain/graphs/watcher.yaml \
  --start-node test_and_demo --stop-after test_and_demo \
  --state-file "$STATE" --full

# ...etc
```

### 7.4 Implementation scope

| Component | Change |
|---|---|
| `yamlgraph/cli/graph_commands.py` | Add `--start-node`, `--state-file`, `--stop-after` flags |
| `yamlgraph/graph_loader.py` | Accept pre-loaded state dict; wire start edge to named node |
| `yamlgraph/executor.py` | Write state to file after execution |
| `yamlgraph/models/` | Ensure `CopilotResult` round-trips through JSON |

### 7.5 Why this over alternatives

- **vs. one graph per phase (Option A):** Session resume works across all nodes in one graph. No graph duplication.
- **vs. python tool nodes (Option B):** Shell logic stays in shell. Orchestrator sees every step. No wrappers.
- **Cost:** ~4 files changed in yamlgraph core. State serialization is the only non-trivial part.

---

## 8) Implementation Phases

### Phase 1: Git skeleton (no LLM)

Shell-only loop proving the worktree lifecycle end-to-end.

```
watcher2.sh
  ├─ source lib/inbox_sync.sh         # import GH issues
  ├─ pick next inbox item
  ├─ source lib/preflight.sh          # prune stale worktrees
  ├─ source lib/worktree_setup.sh     # create worktree + branch
  ├─ cd into worktree
  ├─ touch placeholder file           # simulate work
  ├─ run pre-commit                   # validate hooks work in worktree
  ├─ git commit
  ├─ git push
  ├─ source lib/create_pr.sh
  ├─ source lib/wait_ci.sh
  ├─ source lib/merge_pr.sh
  ├─ cd back to main
  ├─ source lib/worktree_teardown.sh
  ├─ source lib/post_merge.sh         # close GH issue
  └─ source lib/metrics.sh
```

**Exit criteria:** inbox item → worktree → PR → CI green → merge → cleanup, fully automated.

### Phase 2: Diary copilot node

Add a single yamlgraph copilot invocation inside the worktree to validate LLM integration.

- One copilot graph: read inbox topic, write a diary entry to `docs/diary/`
- Uses `--export-state` to prove state chaining works
- Commit diary, push, PR, merge as in phase 1

**Exit criteria:** copilot writes diary in worktree, merges to main.

### Phase 3: Planning + judging

Add plan session (copilot session 1):

- plan → research → write_acceptance → judge (resume chain)
- Shell: `pytest` after write_acceptance to verify RED
- Shell: check judge verdict, abort if rejected
- Commit FR + tests after each step

**Exit criteria:** FR drafted, tests written, verdict rendered — all in worktree branch.

### Phase 4: Enforcement

Add enforce session (copilot session 2):

- implement → test_and_demo → critique_and_distill (resume chain)
- Shell: finalize (pre-commit, commit, push)
- Copilot: fix finalize if pre-commit fails (resume)
- Inquisitor audit (copilot session 3)

**Exit criteria:** full pipeline — inbox → plan → enforce → PR → CI → merge → cleanup.

### Phase 5: Retire old pipeline

- Remove `watch.sh`, `scripts/enforce_worktree.sh`, `scripts/bugfix_worktree.sh`
- Update CLAUDE.md and reference docs
- Run watcher2 as primary for N cycles, monitor

---

## 9) Deliverables

- `watcher2.sh` (new orchestrator)
- `.chaplain/lib/`: `inbox_sync.sh`, `preflight.sh`, `worktree_setup.sh`, `worktree_teardown.sh`, `create_pr.sh`, `wait_ci.sh`, `merge_pr.sh`, `post_merge.sh`, `metrics.sh`
- yamlgraph CLI: `--import-state`, `--export-state` flags (FR-269, merged)
- per-phase copilot graphs
- retired: `watch.sh`, `scripts/enforce_worktree.sh`, `scripts/bugfix_worktree.sh`
