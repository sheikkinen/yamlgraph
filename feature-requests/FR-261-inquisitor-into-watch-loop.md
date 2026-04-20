# Feature Request: Move Inquisitor from Pre-Commit Hook into watch.sh Loop

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-20

## Summary

Remove the `inquisitor-background` post-commit hook and run the Inquisitor as a step inside `.chaplain/watch.sh`, making watch.sh the single orchestrator for all automated pipelines.

## Value Statement

Pipeline maintainers get a single orchestration point for all audit and enforcement activity, eliminating fire-and-forget log noise and enabling the watch loop to act on Inquisitor findings.

## Problem

The Inquisitor runs as a post-commit pre-commit hook (`inquisitor-background`), launched via `nohup` into the background on every commit. This is the wrong integration point:

1. **Fire-and-forget**: Output goes to `.chaplain/inquisitor.log` — no feedback loop, nobody reads it.
2. **Wrong trigger**: Runs per-commit, but audits are meaningful per-pipeline-cycle, not per-commit. The commit-delta gate (FR-131) already skips most runs.
3. **Redundant with watch.sh**: The watch loop already polls for work and runs Plan→Judge→Enforce pipelines. The Inquisitor is the only pipeline triggered outside of it.
4. **Pre-commit bloat**: 36+ hooks already; an async background process doesn't belong in a synchronous hook framework.

The `--propose` flag (FR-118) already writes findings to `.chaplain/inbox/`, which is where watch.sh picks up work — the Inquisitor is already half-integrated with the watch loop.

## Proposed Solution

### 1. Remove the hook from `.pre-commit-config.yaml`

Delete the `inquisitor-background` hook definition (lines 261–269).

### 2. Add Inquisitor step to watch.sh

Insert an Inquisitor run after each successful enforce cycle (step 6 in the current loop), before post-merge finalization:

```bash
# --- Inquisitor audit (FR-261) ---
# Run after enforce cycle completes; --propose feeds findings back into inbox
log "Running Inquisitor audit..."
.chaplain/inquisitor.sh --propose >> "$LOG_DIR/inquisitor-$(date +%Y%m%d-%H%M%S).log" 2>&1 || true
```

### 3. Preserve existing gates

The Inquisitor's own gates remain unchanged:
- **Worktree gate (FR-142)**: Skips when running in a worktree — still relevant since enforce uses worktrees.
- **Commit-delta gate (FR-131)**: Skips when no feat:/fix: commits since last audit — prevents ritual loops.

No changes to `inquisitor.sh` itself are required. The `--force` flag remains available for manual runs.

### 4. Update CLAUDE.md

Remove any reference to `inquisitor-background` as a pre-commit hook. Document the new trigger point in watch.sh.

## Acceptance Criteria

- [x] `inquisitor-background` hook removed from `.pre-commit-config.yaml`
- [x] `watch.sh` runs `.chaplain/inquisitor.sh --propose` after each successful enforce cycle
- [x] Inquisitor log output captured to a timestamped file (not lost to `/dev/null`)
- [x] Inquisitor failure does not block the watch loop (`|| true`)
- [x] Worktree gate (FR-142) and commit-delta gate (FR-131) continue to function
- [x] `--force` manual invocation still works: `.chaplain/inquisitor.sh --force`
- [x] No Inquisitor runs triggered by pre-commit/post-commit hooks
- [x] watch.sh invocation includes `--propose` flag (prevents audit_as_ritual relocation)
- [x] Test verifies `inquisitor-background` hook absent from `.pre-commit-config.yaml`
- [x] Documentation updated (CLAUDE.md hook count, watch.sh flow description)

## Alternatives Considered

1. **Timer-based cadence in watch.sh** (e.g., run every N cycles or every M minutes): Adds complexity for marginal benefit. Running after each enforce cycle is already a large reduction from per-commit, and the commit-delta gate prevents unnecessary work.

2. **Keep hook but redirect output to watch.sh inbox**: Would preserve the per-commit trigger, defeating the purpose. The hook framework is the wrong place for async background processes.

3. **Separate cron job**: Fragments orchestration further. The watch loop is already running and has the right context.

## Related

- **FR-076**: Chaplain Inquisitor — original implementation
- **FR-118**: Inquisitor Auto-Propose — `--propose` flag feeding inbox
- **FR-126**: Propose Verify Resolution — verify before proposing
- **FR-131**: Commit-Delta Gate — pre-flight skip on no feat/fix commits
- **FR-142**: Inquisitor Worktree Gate — skip in worktrees
- **FR-156**: Audit-Loop Gate Fix — SHA extraction and duplicate-range fix
- `.chaplain/inquisitor.sh` — audit script
- `.chaplain/watch.sh` — polling orchestrator
- `.pre-commit-config.yaml` — hook definitions (lines 261–269)

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Classification:** Pattern reconfiguration. No new abstraction; mechanical relocation of trigger point with strong diary/precedent evidence (FR-175, 226 audits, `audit_as_ritual` trap).

**Annotations:**
1. Refined "Tests added" AC → specific: verify hook absent from `.pre-commit-config.yaml`.
2. Added explicit AC for `--propose` flag inclusion to prevent relocating `audit_as_ritual`.
3. No scope concerns — single responsibility, minimal change surface.

**Judge:** Claude Opus 4.6, 2026-04-20

## Research Brief

### Competitive Landscape

No competing LLM orchestration framework (LangGraph, CrewAI, AutoGen, Google ADK, OpenAI Agents SDK) ships an analogous "Inquisitor" — a post-hoc compliance auditor wired into git hooks. The closest patterns are:

- **GitHub Actions `workflow_run` trigger**: The industry standard for post-merge audit is a CI workflow triggered by push/merge events, not a git hook. GitHub Actions supports `on: push` and `on: workflow_run` for chaining steps after a merge, giving centralized logging and status checks. This is the model watch.sh already follows for enforcement.
- **pre-commit framework**: The pre-commit project explicitly documents `post-commit` as a supported stage, but the [official docs](https://pre-commit.com/) focus on synchronous pre-commit checks. Using `nohup ... &` inside a hook to run async background work is an anti-pattern — it circumvents the hook framework's lifecycle (exit code, output capture).
- **Task runners (Make, Just, Taskfile)**: Common pattern is a single orchestrator file that sequences lint → test → audit → deploy. This is exactly what watch.sh already is. Adding Inquisitor as a step is the natural fit.

**Verdict**: No framework-level feature to build. The proposal correctly identifies a **process reconfiguration** — moving a trigger point, not building new capability.

### Existing Abstractions

| Abstraction | File | Relevance |
|---|---|---|
| `inquisitor.sh` | `.chaplain/inquisitor.sh` | The audit script itself — **unchanged** by this FR |
| `watch.sh` orchestrator | `.chaplain/watch.sh` (222 lines) | Single polling loop for Plan→Judge→Enforce→Finalize. The insertion point is after line 115 (enforce cycle) and before line 143 (post-merge finalization) |
| `inquisitor-background` hook | `.pre-commit-config.yaml:261–269` | The hook to remove — `nohup .chaplain/inquisitor.sh > .chaplain/inquisitor.log 2>&1 &` |
| Commit-delta gate (FR-131) | `.chaplain/inquisitor.sh:31–48` | Unchanged; skip logic still applies |
| Worktree gate (FR-142) | `.chaplain/inquisitor.sh:21–29` | Unchanged; suppresses audit in enforce worktrees |
| `--propose` mode (FR-118) | `.chaplain/inquisitor.sh:90–114` | Already writes to `.chaplain/inbox/` — watch.sh's input queue |
| Inquisitor tests | `tests/unit/test_inquisitor_gate.py`, `test_inquisitor_auto_propose.py`, `test_inquisitor_worktree_gate.py` | Existing gate tests remain valid; need new test for hook removal |

**No overlapping node types, tools, or graph abstractions** — this is purely shell-level plumbing.

### Diary Precedents

1. **FR-175 Sequential Enforcement** (`docs/diary/2026-03-09-reflection-fr-175-sequential-enforcement.md`): Directly parallel situation. watch.sh originally spawned enforcement with `nohup ... &` (fire-and-forget). This caused merge conflicts on shared bookkeeping files. The fix: remove `&` and `nohup`, run foreground, accept linear wall-clock cost. **The Inquisitor hook is the last surviving instance of this anti-pattern.**

2. **Watch-Enforce-Merge Dance** (`docs/diary/2026-03-09-reflection-watch-enforce-merge.md`): Documents the pain of parallel fire-and-forget processes in the pipeline. The conclusion — "serialize at the orchestration layer" — directly supports moving the Inquisitor into watch.sh's sequential flow.

3. **Pipeline Process Audit** (`docs/diary/2026-04-19-pipeline-process-audit.md`): Explicitly identifies the Inquisitor as the one pipeline triggered outside watch.sh (item #4 in the pipeline inventory). Flags `detection_without_action` as the core trap. Recommends making `--propose` the default — a natural complement to this FR.

4. **Inquisitor Long March** (`docs/diary/2026-03-07-digest.md`): Documents the 10-audit CALCIFIED finding lifespan and graduates the heuristic: "When a finding survives 3 audits, spawn a feature request to automate the fix." The current fire-and-forget hook suppresses feedback; integrating into watch.sh enables the auto-propose loop.

5. **`audit_as_ritual` trap** (Scripture Knowledge Graph): "3+ audits without fix → ritual, not process." 226 lifetime inquisitor audit diary entries confirm the pattern. Moving into watch.sh with `--propose` transforms detection into action.

### Usage Evidence

- Inquisitor audit diary entries: **226** (lifetime across 2026-03-07 to 2026-04-20)
- Inquisitor-related tests: **3 files** (gate tests, auto-propose test, worktree gate test)
- Inquisitor-related capabilities: **3** (CAP-36 auto-propose, CAP-39 commit-delta gate, CAP-42 worktree gate)
- Pre-commit hooks: **27 repo entries**, 36+ individual hooks — removing one reduces bloat
- watch.sh already handles: inbox polling, Plan→Judge, enforce, bugfix, finalize, GitHub Issue sync, metrics
- Real-world use cases beyond the proposal: **`--propose` as default** (cited in pipeline audit as priority #2) — a natural follow-up FR

### Classification Signal

- **Abstraction level**: pattern (process reconfiguration, not new code abstraction)
- **Recommended approach**: **build** — the change is mechanical (remove hook, add 3 lines to watch.sh), low-risk, and the evidence strongly supports it: 226 audits, 3 diary entries documenting the exact anti-pattern, and the FR-175 precedent proving the cure works
- **Key risk**: If `--propose` is not made the default simultaneously, the Inquisitor merely moves from one fire-and-forget location (hook→log) to another (watch.sh→log), reproducing the `audit_as_ritual` trap in a new venue
