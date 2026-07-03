# Feature Request: Ban Agent Branching in Main Worktree

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-07-03

## Summary

Add a pre-command-guard rule that blocks `git checkout -b`, `git switch -c`, and `git branch <name>` when executed in the main worktree. Force all branch-based isolation through the chaplain worktree pipeline.

## Value Statement

The sole developer stops finding themselves stranded on abandoned agent branches with 167 stale remotes littering origin.

## Problem

Editor-based Copilot agents sometimes create feature branches in the main worktree as a "responsible" isolation pattern. The agent then:

1. Does work on the branch
2. Never switches back to main
3. Never deletes the branch
4. Pushes the branch to origin

Result: 167 stale remote branches (oldest from 2026-02-22), 0 local branches besides main, and the developer repeatedly discovers they're not on main. The branches are never merged — they're abandoned forks.

The chaplain worktree pipeline (CAP-102) handles branch isolation correctly: create worktree → work → teardown. The problem is exclusively agents branching in the main worktree outside the chaplain pipeline.

### Root cause

The `workspace_is_not_boundary` trap from Scripture: the agent thinks creating a branch is being responsible, but it's actually violating the single-developer, commit-to-main workflow. There is one developer. There is no PR review. Branching adds ceremony without value.

## Proposed Solution

Add a fifth check to `.github/hooks/scripts/pre-command-guard.sh` that blocks branch-creation commands:

```bash
# ── Check 5: branch creation in main worktree ────────────────────────
# Agents must not create branches in the main worktree.
# Isolation goes through chaplain worktrees, not local branches.
# Allow: git branch -d (delete), git branch --list, git branch -a
if echo "$COMMAND" | grep -qE 'git\s+(checkout\s+-b|switch\s+-c|branch\s+[^-])'; then
  # Exclude branch deletion and listing
  if ! echo "$COMMAND" | grep -qE 'git\s+branch\s+(-d|-D|--delete|--list|-a|-r|--merged|--no-merged|--contains|--no-contains|--sort|--show-current)'; then
    audit_log "deny" "branch-create" "${COMMAND:0:200}"
    emit_deny "Branch creation in main worktree is forbidden. Single-developer workflow: commit to main.\\n\\nFor isolated work, submit to .chaplain/inbox/ — the chaplain creates worktrees.\\n\\nTo delete stale branches: git branch -d <name>"
    exit 0
  fi
fi
```

### Stale branch cleanup

Separate one-time action (not part of this FR):
```bash
git branch -r | grep -v 'origin/main\|origin/HEAD' | sed 's/origin\///' | xargs -I{} git push origin --delete {}
```

## Acceptance Criteria

- [ ] `git checkout -b feat/anything` denied by pre-command-guard
- [ ] `git switch -c feat/anything` denied by pre-command-guard
- [ ] `git branch feat/anything` denied by pre-command-guard
- [ ] `git branch -d feat/anything` allowed (deletion)
- [ ] `git branch -a` allowed (listing)
- [ ] `git branch --merged` allowed (query)
- [ ] `git checkout main` allowed (switching, not creating)
- [ ] `git switch main` allowed (switching, not creating)
- [ ] Audit log records denied attempts with `branch-create` reason
- [ ] Hook tests added for all cases
- [ ] Tests pass

## Alternatives Considered

1. **Enforce worktrees everywhere** — Overkill. The chaplain already uses worktrees. The problem is the editor agent, not the pipeline.
2. **Ban all branching including worktree branching** — Would break the chaplain. The hook only fires for editor agent commands, not shell scripts, so chaplain is unaffected regardless — but the semantic distinction matters.
3. **Post-hoc cleanup cron** — Treats symptoms. The agent should be stopped at the point of creation, not cleaned up after.

## Judgement

**Decision:** Approved
**Date:** 2026-07-03

Pain is real: 167 stale remote branches, zero merged, one developer, no PR workflow. Solution is minimal: one regex check in an existing guard script. No new files or infrastructure.

Refinements applied:
- Extended exclusion pattern to include `--contains|--no-contains|--sort|--show-current`
- `git push` of existing branches is out of scope — creation block is the boundary guard

Scope frozen. Authority granted for enforcement.

## Related

- `CAP-102`: Complete worktree teardown self-heal
- `.github/hooks/scripts/pre-command-guard.sh`: Hook implementation target
- Scripture trap: `workspace_is_not_boundary`
- Scripture trap: `vendor_default_as_help` — agent frames branching as courtesy
