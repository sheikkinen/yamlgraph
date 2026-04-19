# Pipeline & Process Audit

**Date:** 2026-04-19
**Context:** Philosopher session — mapping all pipelines, assessing maturity, identifying gaps
**Trigger:** After knowledge-layer reconstruction analysis, examined the operational machinery

## Pipeline Inventory

18 distinct pipelines govern YAMLGraph. The full flow:

```
Human thought → GitHub Issue (chaplain label)
       ↓ (auto-sync, 5s polling)
Chaplain watch.sh → LLM: Plan → Judge
       ↓ (approve/reject)
enforce_worktree.sh → LLM: Implement → Test → Demo → Pre-commit → PR
       ↓
36 pre-commit hooks (local gate)
       ↓
6 CI checks (remote gate)
       ↓
Squash merge to main
       ↓
finalize_merge.sh (MANUAL — the one gap)
       ↓
Inquisitor audit (post-hoc)
       ↓
Philosopher (periodic, dormant)
       ↓
Graduation → Scripture → back to enforcement
```

### Pipelines by Category

| # | Pipeline | Trigger | Purpose |
|---|----------|---------|---------|
| 1 | Chaplain daemon | Polling 5s | Inbox → Plan → Judge → Enforce |
| 2 | Enforce worktree | From Chaplain | Isolated TDD implementation |
| 3 | Bugfix worktree | From Chaplain (Type: Bug) | Condemn → Fix → Verify |
| 4 | Inquisitor audit | Manual/hook | Post-hoc compliance audit |
| 5 | Inquisitor propose | Manual --propose | Convert violations → FRs |
| 6 | Philosopher | Manual (intended periodic) | Diary pattern → Scripture graduation |
| 7 | Pre-commit suite | git commit | 36 hooks, fail-fast |
| 8 | Commit message hooks | git commit | Conventional Commits, FR refs |
| 9 | commitlint CI | PR open/edit | PR title validation |
| 10 | conflict-check CI | PR | Unresolved merge markers |
| 11 | changelog-gate CI | PR | Fragment exists for feat/fix |
| 12 | changelog-req-gate CI | PR | Fragment references valid REQ |
| 13 | diary-gate CI | PR | Diary reflection exists |
| 14 | demo-gate CI | PR | demo-output.log for demo changes |
| 15 | test CI | PR | pytest 80% coverage + ruff + lint-imports |
| 16 | security CI | PR | pip-audit CVE scan |
| 17 | Release script | Manual | Bump → freeze → tag |
| 18 | Finalize merge | Manual | Changelog + FR status + diary stub |

## Today's Evidence

| Metric | Value |
|--------|-------|
| Commits | 36 (30 automated, 6 manual) |
| PRs merged | 8 (#123–#130, all Chaplain-driven) |
| Inquisitor audits | 5 (#210–#215) |
| GitHub issues consumed | 3 (#124→FR-252, #125→FR-253, #119→FR-254) |
| Philosopher graduations | 0 (lifetime) |
| Stale worktrees | 2 |
| Manual steps | 1 (finalize_merge.sh) |

Key observation: Issues #124 and #125 (filed by Philosopher this session) were auto-synced, Chaplain-generated FRs, enforced via worktree, merged as PRs #128 and #129, with #124 correctly sequenced as prerequisite for #125. The pipeline performed dependency resolution without human intervention.

## Process Maturity Assessment

| Level | Description | Status |
|-------|-------------|--------|
| 0. Manual | Human does everything | Passed |
| 1. Scripted | Scripts automate steps | Passed |
| 2. Gated | Automation blocks bad changes | **Current** (36 hooks + 6 CI checks) |
| 3. Self-healing | System detects and proposes fixes | Partial (Inquisitor --propose exists but isn't default) |
| 4. Autonomous | System detects, fixes, verifies without human | Emerging (Chaplain auto-merge) |
| 5. Evolving | System modifies its own rules from experience | Aspirational (Philosopher exists, 0 graduations) |

## What Works

**The pipeline eats its own tail.** GitHub issue → FR → worktree → TDD → PR → merge → audit. Closed loop for 95% of the workflow.

**The worktree pattern is battle-hardened.** Isolated git worktree, symlinked .venv, cleanup trap handles bare-repo corruption, stale .pth entries, broken editable installs. If LLM produces garbage, worktree is deleted — zero pollution.

**36 pre-commit hooks are the backbone.** import-linter enforcing three-layer boundaries is the single most valuable hook. The hooks are annoying. That's the point. Scripture: "When hooks feel slow, let that be the sign they guard."

## What Should Change (Priority Order)

### 1. Automate finalize_merge.sh
**Gap:** The one manual step in an otherwise closed loop. After squash merge, human must run script to create changelog fragment, update FR status, generate diary stub. If forgotten, Inquisitor catches it post-hoc — but that's Level 2 (detect) not Level 3 (self-heal).

**Fix:** GitHub Actions workflow on `push to main` or `watch.sh` post-merge phase polling for recently merged PRs.

**Effort:** 0.5 day.

### 2. Inquisitor --propose as default
**Gap:** 215 lifetime audits. Detection without action is ritual. The Inquisitor *can* propose fixes but defaults to advisory mode — write diary entry, move on. The 12-cycle deadlock (same REQ cross-wiring detected repeatedly, never fixed) was diagnosed earlier today as a structural consequence of this design.

**Fix:** 1-line change: make `--propose` the default. Advisory mode becomes `--audit-only` flag.

**Effort:** 1 line + test.

### 3. Worktree garbage collection
**Gap:** 2 stale worktrees right now (fr-196, fr-255). Cleanup trap handles normal exits; crashed/interrupted runs leave orphans.

**Fix:** `watch.sh` checks for worktrees older than 24h and cleans them.

**Effort:** 10 lines in watch.sh.

### 4. Activate the Philosopher
**Gap:** 456 diary entries, 15K lines. 0 graduated heuristics. The knowledge-capture pipeline has never completed its loop. Graduation threshold (≥3 occurrences) may be too high, or the LLM prompt isn't precise enough.

**Fix:** Lower threshold to 2. Run weekly via cron or watch.sh timer.

**Effort:** 0.5 day.

### 5. Pipeline timing metrics
**Gap:** No observability. How long does enforce_worktree take? What's LLM cost per FR? PR failure rate? Only visibility is terminal scroll and LangSmith traces.

**Fix:** Emit timing JSON from enforce_worktree.sh to tmp/pipeline-metrics/. Not urgent but cheap.

**Effort:** 0.5 day.

## Traps Identified

**detection_without_action:** The Inquisitor pattern — detecting violations and recording them without proposing fixes. 215 diary entries that document drift without correcting it. The cure exists (--propose mode) but isn't the default. This is the `audit_as_ritual` trap from Scripture, manifested in process architecture.

**dormant_subsystem:** The Philosopher has all the infrastructure (scanning, LLM analysis, inbox proposal) but has never completed its loop. A subsystem that exists but never fires is worse than one that doesn't exist — it creates the illusion of coverage. Either activate it or delete it.

**manual_in_automated:** One manual step (finalize_merge.sh) in an otherwise automated pipeline creates a reliability cliff. Automation is only as reliable as its weakest link. The human forgetting to run the script is not an edge case — it's the expected failure mode.

## Seed

*The pipeline is 95% closed-loop. The remaining 5% is: one manual step (finalize_merge.sh), one dormant subsystem (Philosopher), and one advisory-default (Inquisitor). Fixing all three would make the system self-healing without being self-directing. The human provides intent (issues) and doctrine (Scripture). Everything between is machinery. Is that the right boundary — or should the Philosopher's graduation loop close too, making the system self-directing?*
