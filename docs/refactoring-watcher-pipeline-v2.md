# Watcher-Enforcer Pipeline: Step-by-Step Overview

*A factual map of what happens, in what order, and where things break.*

## The Full Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│  watch.sh (infinite loop, 5s poll)                              │
│                                                                  │
│  1. IMPORT ─── GitHub issues → .chaplain/inbox/*.md              │
│  2. PICK   ─── first .md from inbox                              │
│  3. PLAN   ─── copilot graph (plan → research → worktree         │
│                  → acceptance tests → judge → diary)             │
│  4. ROUTE  ─── rejected? skip. bug? bugfix. else → enforce       │
│  5. ENFORCE ── enforce_worktree.sh → enforce graph               │
│  6. CLOSE  ─── close GitHub issue if enforce succeeded            │
│  7. AUDIT  ─── inquisitor.sh --propose                           │
│  8. METRICS ── write JSON timing to tmp/pipeline-metrics/        │
│  9. FINALIZE ─ detect merged PRs, create finalization PRs        │
│                                                                  │
│  sleep 5, loop                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Import (watch.sh lines 27–52)

**Input:** GitHub issues labeled `chaplain`
**Output:** `.chaplain/inbox/gh-<num>.md`

```
gh issue list --label chaplain
  │
  ├─ for each issue:
  │   ├─ skip if gh-<num>.md already exists in inbox
  │   ├─ check author against allowed-authors.txt (FR-251)
  │   ├─ truncate body if > 10,000 chars (FR-251)
  │   ├─ write to .chaplain/inbox/gh-<num>.md
  │   │   (with audit header: <!-- author: @username -->)
  │   └─ remove 'chaplain' label from issue
  │
  └─ all gh calls wrapped in 2>/dev/null || continue
     (GitHub being down = silent skip)
```

**Can fail:** Network, auth token expired, rate limit. All silently swallowed.

---

## Step 2: Pick (watch.sh lines 55–56)

**Input:** `.chaplain/inbox/`
**Output:** `$topic_file` (first .md found)

```
topic_file=$(find .chaplain/inbox -maxdepth 1 -name "*.md" | head -1)
if empty → sleep 5, continue
```

**Can fail:** Cannot fail — `find` always returns.

---

## Step 3: Plan (watch.sh lines 58–68 → copilot graph)

**Input:** `$topic_file`
**Output:** FR draft in `.chaplain/drafts/`, worktree, acceptance tests, diary entry

```
yamlgraph graph run .chaplain/graphs/copilot/graph.yaml
  │
  │  Node 1: plan (copilot, 500s timeout)
  │    read topic file → draft FR to .chaplain/drafts/
  │
  │  Node 2: research (copilot, 1000s timeout)
  │    gather evidence, write research_brief
  │    (resumes plan session)
  │
  │  Node 3: create_worktree (python tool)
  │    ├─ glob .chaplain/drafts/*.md
  │    │   ├─ 0 files → FileNotFoundError, pipeline halts
  │    │   └─ 2+ files → ValueError, pipeline halts
  │    ├─ git add -f <draft>  (force-add past .gitignore, FR-265)
  │    ├─ git commit --no-verify "docs(FR): stage draft..."
  │    │   (idempotent: "nothing to commit" = success)
  │    ├─ derive branch name from draft filename
  │    ├─ git worktree add tmp/worktrees/feat/<branch> -b <branch> main
  │    ├─ validate .venv health (FR-174)
  │    ├─ ln -sf .venv → worktree/.venv
  │    └─ validate symlink resolves (FR-174)
  │
  │  Node 4: write_acceptance_tests (copilot, 600s timeout)
  │    generate failing pytest tests from FR acceptance criteria
  │    (runs inside worktree)
  │
  │  Node 5: judge (copilot, 1000s timeout)
  │    evaluate FR + research + tests → Approved / Rejected
  │
  │  Node 6: summarize (llm)
  │    distill to diary entry (theme, body, seed)
  │
  │  Node 7: write_diary (python tool)
  │    write docs/diary/YYYY-MM-DD-chaplain.md
  │
  └─ total timeout budget: ~3100s (51 min)
```

**Can fail:** LLM timeout, multiple drafts, branch already exists, venv broken. Graph failure = no new FR, no downstream routing.

---

## Step 4: Route (watch.sh lines 71–115)

**Input:** Before/after diff of `feature-requests/`
**Output:** Decision to skip, bugfix, or enforce

```
new_fr = diff(before, after feature-requests/)
  │
  ├─ no new FR → skip to metrics
  │
  ├─ grep Status.*Rejected → skip, EXIT_CODE=0
  │
  ├─ grep Type.*Bug → scripts/bugfix_worktree.sh "$new_fr"
  │                    capture EXIT_CODE
  │
  └─ else → scripts/enforce_worktree.sh "$new_fr"
             capture EXIT_CODE
```

**Can fail:** Grep regex breaks if FR format changes. Silent misroute.

---

## Step 5: Enforce (enforce_worktree.sh → enforce graph)

**Input:** FR path, base branch (default: main)
**Output:** PR created and pushed, or crash + cleanup

This is where 43% of failures occur. Two phases: **shell setup** and **graph execution**.

### Phase A: Shell Setup (enforce_worktree.sh lines 47–177)

```
  ┌─ VALIDATE
  │   ├─ FR file exists?
  │   ├─ derive branch name (python helper)
  │   ├─ derive worktree path (python helper)
  │   └─ clean working tree? (python helper, excludes diary/.chaplain/FRs)
  │       └─ FAILS HERE: unstaged changes → ValueError → exit 1
  │
  ├─ COMMIT FR TO MAIN (unless pre-existing worktree from step 3)
  │   ├─ git add "$FR_PATH"
  │   ├─ git commit --no-verify
  │   └─ git push
  │
  ├─ REGISTER CLEANUP TRAP (fires on any exit)
  │   ├─ write metrics JSON
  │   ├─ cd back to main dir
  │   ├─ git worktree remove --force
  │   ├─ git branch -D (if no remote)
  │   ├─ check/fix bare=true corruption (FR-139)
  │   ├─ clean stale .pth entries (FR-174)
  │   └─ validate/self-heal editable install (FR-241)
  │
  ├─ CREATE WORKTREE
  │   ├─ git worktree add <dir> -b <branch> main
  │   │   └─ FAILS HERE: branch already exists → fatal → exit
  │   ├─ validate .venv health
  │   ├─ ln -sf .venv → worktree/.venv
  │   ├─ validate symlink
  │   └─ add .venv to worktree .gitignore
  │
  └─ ENTER WORKTREE
      ├─ cd $WORKTREE_DIR
      └─ unset GIT_DIR GIT_WORK_TREE (FR-139)
```

### Phase B: Graph Execution (enforce graph, inside worktree)

```
yamlgraph graph run .chaplain/graphs/enforce/graph.yaml
  │
  │  Node 1: implement (copilot, 3600s = 60 min)
  │    read FR → write failing tests → implement → refactor
  │    (single session, all subsequent nodes resume this)
  │
  │  Node 2: test_and_demo (copilot, 900s = 15 min)
  │    run full pytest suite, create/update examples
  │
  │  Node 3: critique_and_distill (copilot, 600s = 10 min)
  │    evaluate against FR acceptance criteria
  │    write diary reflection
  │
  │  Node 4: finalize (copilot, 1500s = 25 min)
  │    run pre-commit hooks, fix failures
  │    git commit, git push
  │    gh pr create, gh pr merge --squash
  │
  └─ total timeout budget: 6600s (110 min)
```

### Phase C: Post-Assertions (enforce_worktree.sh lines 190–196)

```
  cd back to $MAIN_DIR
  check core.bare != "true" (FR-139)
  if corrupted → git config core.bare false
```

### Phase D: Cleanup Trap (fires on exit, success or failure)

```
  ┌─ write metrics JSON (best-effort, || true)
  ├─ cd $MAIN_DIR || true
  ├─ git worktree remove --force $WORKTREE_DIR 2>/dev/null || true
  ├─ git branch -D $BRANCH 2>/dev/null || true (if no remote)
  ├─ if bare=true → git config core.bare false
  ├─ python3: clean_stale_pth_entries(.venv, worktree) || true
  └─ if "import yamlgraph" fails:
      └─ pip install -e . --quiet
          └─ if still fails: log error, give up
```

**7 cleanup operations, all guarded with `|| true`. If cleanup itself crashes, state corruption persists until next manual intervention.**

---

## Step 6: Close Issue (watch.sh lines 105–114)

```
if EXIT_CODE == 0 AND inbox file matches "gh-*.md":
  extract issue number
  gh issue close $num --comment "Implemented in $(git rev-parse --short HEAD)"
```

**Can fail:** gh unavailable. Wrapped in `2>/dev/null || true`.

---

## Step 7: Audit (watch.sh lines 119–125)

```
if new FR was created AND enforcement succeeded:
  .chaplain/inquisitor.sh --propose | tee tmp/inquisitor-*.log
```

The inquisitor:
1. **Gate:** skip if in worktree (FR-142), skip if no new feat/fix commits (FR-131)
2. **Audit:** read last 5 commits, CHANGELOG, diary, Scripture → classify as ✓/⚠/✗
3. **Record:** write `docs/diary/YYYY-MM-DD-inquisitor-audit-<N>.md`
4. **Propose (if --propose):** scan last 5 audits for persistent ✗ VIOLATIONS → write fix proposals to `.chaplain/inbox/`

**Can fail:** Wrapped in `|| true`. Inquisitor failure never stops the watcher.

---

## Step 8: Metrics (watch.sh lines 127–151)

```
write JSON to tmp/pipeline-metrics/chaplain-cycle-<timestamp>.json:
  { pipeline, inbox_item, fr_generated, verdict, enforce_outcome, total_seconds }
```

**Can fail:** Best-effort, `2>/dev/null || true`.

---

## Step 9: Finalize (watch.sh lines 153–229)

```
if gh authenticated:
  git checkout main && git pull
  read last-finalized-at timestamp from .chaplain/state/

  for each PR merged since last check:
    extract FR number from branch name (fr-NNN)
    find feature-requests/FR-NNN-*.md
    skip if already Status=Implemented

    create branch chore/finalize-<fr-num>
    ├─ create changelog fragment
    ├─ update FR status to Implemented
    ├─ create diary stub
    ├─ git commit --no-verify
    ├─ git push
    ├─ gh pr create
    └─ gh pr merge --squash

  update .chaplain/state/last-finalized-at
```

**Can fail:** Many ways — gh, git, regex. Each PR is independent; one failure doesn't block others. All wrapped in defensive checks.

---

## State Locations

| What | Where | Lifecycle |
|------|-------|-----------|
| Incoming topics | `.chaplain/inbox/*.md` | Created by import or manually. Consumed by plan. |
| FR drafts | `.chaplain/drafts/*.md` | Created by plan node. Committed by create_worktree. |
| Feature requests | `feature-requests/FR-*.md` | Created from draft. Lives forever. Status field updated. |
| Worktrees | `tmp/worktrees/feat/fr-*/` | Created by create_worktree or enforce script. Removed by cleanup trap. |
| Diary entries | `docs/diary/YYYY-MM-DD-*.md` | Created by write_diary, summarize, inquisitor. Permanent. |
| Pipeline metrics | `tmp/pipeline-metrics/*.json` | Created per cycle. Never consumed by pipeline. |
| Last finalization | `.chaplain/state/last-finalized-at` | Updated after finalization pass. |
| Allowed authors | `.chaplain/allowed-authors.txt` | Static allowlist for GitHub issue import. |

---

## Where It Breaks (Observed Failures)

| # | Failure | Step | Cause | Fix (manual) | Fix (needed) |
|---|---------|------|-------|-------------|-------------|
| 1 | `fatal: branch already exists` | 5A (worktree) | Previous run crashed, stale branch left | `git branch -D <branch>` | Pre-flight: delete stale branch |
| 2 | `ValueError: unstaged changes` | 5A (validate) | Previous run left debris, or finalization step left repo dirty | `git stash` or `git checkout .` | Pre-flight: stash or clean |
| 3 | Main repo on wrong branch | 5A (implicit) | Worktree creation or finalization switched HEAD | `git checkout main` | Pre-flight: ensure on main |
| 4 | Stale worktrees lingering | 5A (implicit) | Cleanup trap failed or was interrupted | `git worktree remove --force <dir>` | Pre-flight: prune stale worktrees |
| 5 | LLM timeout | 3, 5B | Copilot or API latency | Re-run | Retry with backoff (not implemented) |
| 6 | `.venv` symlink broken | 5A (symlink) | Main venv reinstalled or moved | `pip install -e .` | Already guarded by FR-174 |

**Failures 1–4 account for all 6 recent crashes. All are pre-condition failures in step 5A. All are trivially fixable with 1-line git commands. None are currently checked before the step that fails.**

---

## The Missing Pre-flight

What should happen at the top of `enforce_worktree.sh` (and `bugfix_worktree.sh`), before anything else:

```bash
# ensure we're on main
git checkout main 2>/dev/null

# clean stale worktrees
git worktree prune

# delete target branch if it already exists locally
git branch -D "$BRANCH" 2>/dev/null || true

# stash any debris from previous runs
if ! python3 -c "from yamlgraph.utils.worktree_helpers import validate_clean_working_tree; validate_clean_working_tree()" 2>/dev/null; then
    git stash --include-untracked -m "enforce-preflight-$(date +%s)"
fi
```

Four commands. Would have prevented every recent failure.

---

*April 2026*
