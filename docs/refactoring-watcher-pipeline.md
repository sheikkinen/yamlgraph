# Refactoring the Watcher Pipeline

*An architectural reflection on why the Chaplain keeps breaking, and what it should become.*

## The Problem

The watcher pipeline (`watch.sh` → `enforce_worktree.sh` → graphs) has a **43% enforcement failure rate**. Six of the last fourteen enforce runs crashed in 3–6 seconds — before any useful work began. The cause in every case was trivial: a stale branch, unstaged changes, or the main repo sitting on the wrong branch.

Seven feature requests (FR-139, 174, 175, 236, 241, 260, 265) have been filed and implemented to fix pipeline brittleness. All seven are watcher infrastructure fixes. The pattern is clear: each FR patches a new symptom without addressing why symptoms keep appearing.

## The Diagnosis

### What Actually Kills the Pipeline

The pipeline doesn't die from complex failures. It dies from pre-conditions nobody checks:

| Failure | Frequency | Cause | Time to Fix (manually) |
|---------|-----------|-------|----------------------|
| `fatal: branch already exists` | 5 of 6 failures | Stale branch from previous failed run | `git branch -D` (2s) |
| `ValueError: unstaged changes` | 1 of 6 failures | Previous run left debris | `git stash` (1s) |
| Main repo on wrong branch | Persistent | Worktree creation switches HEAD | `git checkout main` (1s) |

The seven guard FRs (bare=true restoration, .pth cleaning, import self-heal, venv validation) are **defense-in-depth for failures that occur during or after execution**. They never fire because the pipeline crashes *before reaching them* — on entry conditions that are trivially fixable but never checked.

### Why the Guards Don't Help

```
Pipeline Execution Timeline:

  Entry         Execution              Cleanup
  ─────         ─────────              ───────
  [PRE-CHECK]   [LLM WORK]            [GUARDS]
   ↑                                    ↑
   Dies here                            FR-139, 174, 236, 241 live here
   (3-6 seconds)                        (never reached)
```

The cleanup trap contains 50+ lines of cascading guards across 7 fix-up operations. These guards are well-engineered. They are also irrelevant to the actual failures.

### The Deeper Pattern

This is `downstream_fix` at architectural scale. Each FR adds a guard where a symptom *manifests*, rather than preventing the condition that *causes* it. The One Law — normalize at the boundary where external data enters — applies to the pipeline itself. The "external data" is the state of the filesystem, git, and venv when the pipeline starts. That boundary has no normalization.

## The Numbers

| Metric | Value |
|--------|-------|
| Total script lines (watch + enforce + bugfix) | 666 |
| Code duplication (enforce vs bugfix) | 50% (216 lines) |
| Error-swallowing patterns in watch.sh | 42+ (31× `2>/dev/null`, 11× `\|\| true`) |
| Implicit assumptions (unchecked pre-conditions) | 34 |
| Cleanup trap operations | 7 (5-level nesting) |
| FRs that are watcher infrastructure fixes | 7 of 7 (100%) |
| Consecutive audits flagging FR-174 without fix | 10+ |
| Enforce failure rate (recent) | 43% (6/14) |
| Time wasted per crash | 3–6s + human intervention to clean up |

## Why This Keeps Happening

The watcher is a **bash-scripted FSM wearing a pipeline costume**. It imperatively mutates shared state (`.git/config`, `.venv` symlinks, worktree directories, editable install metadata), then reactively checks for corruption in a cleanup trap. Every new failure mode requires a new hand-coded guard, which is then forgotten in the duplicate `bugfix_worktree.sh` (which is missing 4 guards from the enforce pipeline).

Three structural problems:

### 1. No Pre-flight Reconciliation

The pipeline assumes it starts in a clean state. It never verifies this. When the assumption is wrong (43% of the time), it crashes immediately.

**What's needed:** A reconciler that runs *before* each phase and brings the world to the expected state. Not an LLM — a deterministic function that checks invariants and applies known fixes.

### 2. Bash Cannot Express State Contracts

Bash has no type system, no structured error handling, no way to express "this function requires X and guarantees Y." Pre-conditions are implicit assumptions scattered across 666 lines. Post-conditions are cleanup traps that swallow errors with `|| true`.

**What's needed:** Each pipeline phase expressed as a Python function with typed pre-conditions and post-conditions. Pydantic models for pipeline state. Failures are values, not exit codes.

### 3. Duplication Creates Drift

`enforce_worktree.sh` and `bugfix_worktree.sh` share 50% of their code via copy-paste. When FR-174/236/241 hardened the enforce pipeline, the bugfix pipeline was not updated. This is not a lapse — it's structural. Duplication guarantees drift.

**What's needed:** A single pipeline engine that handles both enforce and bugfix as configurations, not as separate scripts.

## The Architecture That Should Exist

### Design Principles

1. **Reconcile, don't assume.** Before each phase, observe actual state, compare to expected state, apply minimal fix. Like a Kubernetes controller, not a shell script.

2. **Contracts, not traps.** Each phase declares what it needs (pre-conditions) and what it produces (post-conditions). Violations are raised, not swallowed.

3. **One engine, many workflows.** Enforce and bugfix are configurations of the same pipeline, not duplicate scripts.

4. **Failures are data.** A phase that fails returns a structured error that the pipeline can reason about. Not an exit code. Not stderr. A Pydantic model.

5. **The LLM does the work, not the plumbing.** The orchestration layer is deterministic Python. The LLM is invoked only for creative tasks (plan, implement, judge). State reconciliation, git operations, and venv management are never delegated to an LLM.

### Proposed Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Pipeline Runner                    │
│  (Python, replaces watch.sh + enforce + bugfix)      │
│                                                      │
│  for item in inbox:                                  │
│      pipeline = load_workflow(item.type)  # enforce/bugfix │
│      for phase in pipeline.phases:                   │
│          state = reconcile(phase.pre_conditions)      │
│          result = phase.execute(state)                │
│          verify(phase.post_conditions, result)        │
│          state = state.merge(result)                  │
└─────────────────────────────────────────────────────┘

┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  Reconciler        │  │  Phase             │  │  Verifier          │
│                    │  │                    │  │                    │
│  • branch exists?  │  │  • plan            │  │  • FR file exists? │
│    → delete it     │  │  • research        │  │  • worktree valid? │
│  • wrong branch?   │  │  • create_worktree │  │  • venv healthy?   │
│    → checkout main │  │  • judge           │  │  • tests pass?     │
│  • dirty tree?     │  │  • implement       │  │  • PR created?     │
│    → stash         │  │  • test            │  │                    │
│  • stale worktree? │  │  • finalize        │  │                    │
│    → remove it     │  │                    │  │                    │
│  • venv broken?    │  │  (each is a Python │  │  (each returns     │
│    → reinstall     │  │   function with    │  │   Pass/Fail with   │
│                    │  │   typed state)     │  │   structured error)│
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

### Phase Contract Example

```python
@dataclass
class PhaseContract:
    """What a phase requires and guarantees."""
    pre_conditions: list[Callable[[PipelineState], CheckResult]]
    execute: Callable[[PipelineState], PhaseResult]
    post_conditions: list[Callable[[PipelineState], CheckResult]]
    reconcilers: list[Callable[[CheckResult], None]]  # auto-fixes for known failures


@dataclass
class CheckResult:
    ok: bool
    detail: str
    fixable: bool  # can the reconciler handle this?


# Example: the "create worktree" phase
create_worktree_phase = PhaseContract(
    pre_conditions=[
        check_on_main_branch,       # git branch --show-current == "main"
        check_no_stale_worktrees,   # git worktree list has no orphans
        check_branch_not_exists,    # target branch doesn't exist locally or remotely
        check_clean_working_tree,   # no unstaged changes (excluding allowed paths)
        check_venv_healthy,         # .venv exists, python works, yamlgraph importable
    ],
    execute=create_worktree_fn,
    post_conditions=[
        check_worktree_exists,      # directory exists at expected path
        check_venv_symlinked,       # .venv symlink resolves to main venv
        check_branch_created,       # branch exists and points to main
    ],
    reconcilers=[
        fix_checkout_main,          # git checkout main
        fix_remove_stale_worktrees, # git worktree remove + git branch -D
        fix_delete_stale_branch,    # git branch -D <branch>
        fix_stash_changes,          # git stash
        fix_reinstall_venv,         # pip install -e .
    ],
)
```

### What Changes

| Current | Proposed |
|---------|----------|
| `watch.sh` (232 lines bash) | `pipeline_runner.py` — Python polling loop with structured logging |
| `enforce_worktree.sh` (224 lines bash) | `workflows/enforce.py` — phase list with contracts |
| `bugfix_worktree.sh` (210 lines bash) | `workflows/bugfix.py` — same engine, different phase config |
| Cleanup trap (7 operations, 50 lines) | Post-conditions + reconcilers on each phase |
| 42 error-swallowing patterns | Structured `CheckResult` / `PhaseResult` — failures are values |
| 34 implicit assumptions | Explicit pre-condition checks with auto-fix |
| `worktree_helpers.py` (7 functions) | Reused as reconciler implementations |
| `.chaplain/state/` (1 file) | Pipeline state model tracking current phase, retries, errors |

### What Stays

- **The YAML graphs** (`copilot/graph.yaml`, `enforce/graph.yaml`) — these are the LLM orchestration layer and they work. The problem is the bash shell around them.
- **The workflow** (plan → research → judge → enforce → audit) — the steps are right. The execution model is wrong.
- **The guards** (FR-139, 174, 241) — these become reconciler functions. The logic is sound; it just lives in the wrong place (cleanup traps instead of pre-flight checks).
- **Sequential enforcement** (FR-175) — correct design decision. The runner preserves this.

### Migration Path

This is not a rewrite. It's a **progressive extraction**:

1. **Extract the reconciler.** Write `pipeline_preflight.py` with the pre-condition checks and auto-fixes. Call it from `enforce_worktree.sh` as a first line: `python3 -m yamlgraph.pipeline.preflight || exit 1`. This alone would have prevented all 6 recent failures.

2. **Unify enforce and bugfix.** Extract shared logic from both scripts into `pipeline_common.sh` (or Python). Eliminate the 50% duplication that causes guard drift.

3. **Replace the cleanup trap.** Move post-condition verification to Python. The bash trap calls `python3 -m yamlgraph.pipeline.postchecks` instead of 50 lines of nested bash guards.

4. **Replace the shell scripts.** Once pre-flight, execution, and post-checks are all in Python, the bash scripts are thin wrappers. Replace them with a Python runner.

5. **Replace watch.sh.** The polling loop, inbox management, and GitHub sync become a Python process with structured state and proper error handling.

Each step is independently valuable. Each step can be tested and deployed. The pipeline keeps running throughout.

## The Question Nobody Asked

The seven guard FRs, the 43% failure rate, the 10+ audit cycles without fix — these are symptoms of a system that was built to demonstrate a workflow and then pressed into production service. The watcher runs continuously, processes real FRs, creates real PRs. But its infrastructure is still demo-grade bash.

The question isn't "how do we add more guards?" or "should we add an orchestrator agent?" The question is: **should the orchestration layer be bash at all?**

The answer, after 666 lines of evidence, is no.

## Risks and Open Questions

1. **Is the reconciler itself brittle?** If pre-flight checks have bugs, they could make things worse (e.g., deleting a branch that's still needed). Each reconciler needs its own tests and a dry-run mode.

2. **What about the graphs that call shell commands?** The copilot nodes invoke `gh copilot` via shell. The enforce graph runs in a worktree. These shell interactions remain even after Python extraction. The boundary between Python orchestration and shell tools must be explicit.

3. **State persistence across crashes.** If the Python runner crashes mid-phase, what state is recoverable? The current system has no checkpointing beyond git commits. A phase registry (`pipeline_state.json`) would track what completed and what needs retry.

4. **Watch loop lifecycle.** The current `while true` loop with 5s sleep is crude but functional. A Python replacement could use `watchdog` for filesystem events, but polling is simpler and more predictable. Start with polling; optimize later if needed.

5. **The Inquisitor's independence.** The Inquisitor runs post-enforcement and writes to the inbox, creating a feedback loop. In the Python runner, this becomes a phase that can be scheduled independently, not just triggered by `|| true` after enforcement.

---

*The Philosopher observes: Seven FRs to fix a pipeline is not engineering — it's archaeology. Each layer preserves the assumptions of the layer below. The refactoring is not about better guards. It's about a foundation that doesn't need them.*

*— April 2026*
