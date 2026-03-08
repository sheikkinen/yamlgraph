# Feature Request: Inquisitor worktree gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add a worktree-detection gate to `inquisitor.sh` that suppresses audit and propose phases when running inside a git worktree (i.e., during an enforce pipeline), ensuring the Inquisitor only fires on completed work on the main working tree.

## Value Statement

The enforce pipeline stops triggering wasteful Inquisitor audits on every intermediate commit, eliminating noise, wasted API calls, and stale proposals during in-progress FR implementation.

## Problem

The Inquisitor is registered as a `post-commit` hook (`.pre-commit-config.yaml`, line 175). It fires after **every** commit, including commits made inside git worktrees during the enforce pipeline (`scripts/enforce_worktree.sh`).

During a typical enforce cycle, the copilot nodes in `examples/enforce/graph.yaml` create multiple commits (implement, test, pre-commit fixes, PR submission). Each commit triggers the Inquisitor, which:

1. **Wastes copilot API calls** — audits against incomplete, mid-implementation code
2. **Produces misleading findings** — violations are expected during in-progress work (missing diary, incomplete CHANGELOG, etc.)
3. **Writes diary entries in the worktree** — these entries exist only on the feature branch, not main, and may create merge conflicts or be lost after worktree cleanup
4. **Writes proposals to the worktree's `.chaplain/inbox/`** — the watch.sh daemon (running on main) never sees them; they're discarded on worktree cleanup
5. **Undermines the commit-delta gate (FR-131)** — the gate correctly finds `feat:`/`fix:` commits in the worktree branch and proceeds, when it should not

The root cause: the Inquisitor has no awareness of its execution context. It treats worktree commits identically to main-branch commits, but the enforce pipeline's intermediate commits are not "completed work" — they are work in progress.

This aligns with the `audit_as_ritual` trap from the Knowledge Graph:
```yaml
audit_as_ritual: "3+ audits without fix → ritual, not process"
```

Auditing mid-enforce commits is ritual, not process — the work hasn't stabilized.

## Proposed Solution

Add a **worktree gate** as the first check in `inquisitor.sh`, before the existing commit-delta gate (FR-131). The gate detects whether the script is running inside a git worktree and exits early if so.

### Detection method

In a git worktree, the `.git` entry at the repository root is a **file** (containing `gitdir: ...`), not a **directory**. This is a reliable, zero-cost shell check:

```bash
# --- Worktree gate (FR-142) ---
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -n "$REPO_ROOT" && -f "$REPO_ROOT/.git" ]]; then
    echo "⏭️  Inquisitor: Running in a git worktree (enforce pipeline in progress). Skipping audit."
    echo "   Audits run on main after the FR/PR is merged."
    exit 0
fi
```

### Placement in `inquisitor.sh`

```
#!/usr/bin/env bash
# ...header comments...
set -euo pipefail
cd "$(dirname "$0")/.."

# Flag parsing (existing)
FORCE=""
PROPOSE=""
while [[ $# -gt 0 ]]; do ...

# --- Worktree gate (FR-142) --- ← NEW, runs first
# --- Commit-delta gate (FR-131) --- ← existing
# --- Audit phase (FR-076) --- ← existing
# --- Propose phase (FR-118) --- ← existing
```

### Flag interaction

| Flag | Worktree gate behavior |
|------|----------------------|
| (none) | Gate active — skip in worktree |
| `--force` | Gate **bypassed** — force audit even in worktree |
| `--propose` | Gate active — no propose in worktree |
| `--force --propose` | Gate bypassed — audit + propose in worktree |

The `--force` flag already exists and naturally overrides this gate, maintaining the existing escape hatch pattern from FR-131.

### Why not branch-name detection?

Branch names (`feat/FR-XXX-*`) are convention-dependent and fragile. The `.git` file check is a structural guarantee — git itself creates this distinction. If the enforce pipeline ever changes its branch naming convention, the gate still works.

## Acceptance Criteria

- [ ] `inquisitor.sh` exits with code 0 and a clear message when running inside a git worktree
- [ ] Gate is placed before the commit-delta gate (FR-131) — worktree check is cheaper and more decisive
- [ ] `--force` flag bypasses the worktree gate (consistent with FR-131 behavior)
- [ ] Gate degrades gracefully: if `git rev-parse` fails or `.git` path is ambiguous, gate is skipped (audit proceeds)
- [ ] No changes to audit logic, propose logic, or commit-delta gate
- [ ] Gate logic is pure shell (no Python, no copilot call) — consistent with FR-131 pattern
- [ ] Header comment updated to document FR-142
- [ ] Test: verify gate fires in a worktree context and skips in main context
- [ ] Post-merge: Inquisitor audit on main correctly audits the merged enforce commits

## Alternatives Considered

1. **Remove post-commit hook from worktrees entirely** — Rejected. Pre-commit hook installation is shared via `.git/hooks/`; there's no per-worktree opt-out for specific hooks without modifying git's hook mechanism. The gate inside the script is simpler.

2. **Lock file (`.chaplain/inquisitor.lock` set by enforce_worktree.sh)** — Rejected. The lock file would exist on main but the Inquisitor runs in the worktree. Cross-worktree file coordination adds complexity. The structural `.git` file check needs no coordination.

3. **Environment variable (`ENFORCE_IN_PROGRESS=1`)** — Rejected. Requires the enforce pipeline to export the variable, and all commit-making nodes in the enforce graph to inherit it. The structural check is self-contained.

4. **Branch name pattern matching (`feat/FR-*`)** — Rejected. Convention-dependent; breaks if branch naming changes. The `.git` file check is a git structural guarantee.

5. **Disable `--propose` in worktrees but keep audit** — Rejected. Even audit-only is wasteful on incomplete work. The findings are unreliable and the diary entries land in the worktree, not main.

## Judgement

**Verdict:** APPROVED — 2026-03-08

**Rationale:** Scope is clear, minimal, and internally consistent. The detection method (`-f "$REPO_ROOT/.git"`) is a git structural guarantee — zero-cost, no coordination, no convention dependency. Flag interaction is explicitly defined. All 9 acceptance criteria are binary pass/fail. Implementation follows the established FR-131 gate pattern exactly. Five alternatives were considered and rejected with sound rationale. The FR correctly identifies the `audit_as_ritual` trap and provides the precise cure.

**Scope frozen.** Authority granted to implement.

## Related

- **FR-131** (`feature-requests/FR-131-inquisitor-commit-delta-gate.md`): Commit-delta gate — this FR adds a complementary gate before it
- **FR-076** (`feature-requests/FR-076-chaplain-inquisitor.md`): Original Inquisitor design
- **FR-118** (`feature-requests/FR-118-inquisitor-auto-propose.md`): `--propose` flag — gate must compose with it
- **FR-106** (`feature-requests/FR-106-parallel-worktree-pipeline.md`): Worktree enforce pipeline that creates the context this FR detects
- **FR-128** (`feature-requests/FR-128-yamlgraphication-of-enforcer.md`): Enforce graph — source of intermediate commits
- **Knowledge Graph**: `audit_as_ritual` trap, `audit_gate` cure
