# Feature Request: Retire Old Pipeline Scripts (FR-273 Phase 5)

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 2-3 days
**Requested:** 2026-04-23

## Verdict

**APPROVED** - Scope frozen, authority granted to implement.

The FR addresses a single, cohesive concern: consolidating pipeline orchestration to watcher2.sh as the sole entry point. This is a mature cleanup task with clear acceptance criteria, proven abstractions, and measurable outcomes. Research confirms no competing solutions needed.

**Scope frozen as specified:**
1. Delete 3 obsolete scripts
2. Update documentation references  
3. Ensure forensic failure preservation
4. Add orphaned worktree metadata pruning
5. Validate no functional regression

## Summary

Replace obsolete `watch.sh`, `enforce_worktree.sh`, and `bugfix_worktree.sh` with `watcher2.sh` as the sole orchestrator. Implement failure forensics by preserving failed worktrees and topics for inspection rather than destroying evidence.

## Value Statement

Development teams gain reliable failure investigation capabilities, reducing debug time from manual reproduction cycles to direct forensic inspection of preserved worktrees and failure contexts.

## Problem

Current pipeline scripts have fundamental operational issues:

1. **Evidence destruction on failure** — `worktree_teardown + rm topic file` on every failure destroys forensic evidence
2. **Fragmented orchestration** — Three separate scripts (`watch.sh`, `enforce_worktree.sh`, `bugfix_worktree.sh`) duplicate logging, cleanup, and preflight logic
3. **Silent failure suppression** — 20+ `2>/dev/null || true` patterns hide operational issues
4. **Documentation drift** — Multiple entry points confuse users and maintainers

## Proposed Solution

### 1. Script Retirement

Remove these legacy scripts:
- `.chaplain/watch.sh` (monolithic watcher, replaced by watcher2.sh)
- `scripts/enforce_worktree.sh` (enforcement, replaced by watcher2 enforce pipeline)
- `scripts/bugfix_worktree.sh` (bugfix flow, replaced by watcher2 enforce pipeline)

### 2. Failure Path Forensics

Current behavior:
```bash
# On ANY failure → evidence destroyed
worktree_teardown
rm -f "$TOPIC_FILE"
```

New forensic-preserving behavior:
```bash
handle_failure() {
    local reason="${1:-unknown}"
    log_error "Cycle failed: $reason"
    
    # SUCCESS → clean teardown
    if [[ "$reason" == "success" ]]; then
        worktree_teardown
        rm -f "$TOPIC_FILE"
        write_metrics
        return
    fi
    
    # FAILURE → preserve evidence
    if [[ -n "${WT_DIR:-}" && -d "$WT_DIR" ]]; then
        log_warn "Worktree preserved for inspection: $WT_DIR"
    fi
    if [[ -n "${TOPIC_FILE:-}" && -f "$TOPIC_FILE" ]]; then
        local failed_name
        failed_name=$(basename "$TOPIC_FILE")
        mv "$TOPIC_FILE" ".chaplain/failed/$failed_name" 2>/dev/null || true
        log_warn "Topic moved to: .chaplain/failed/$failed_name"
    fi
    write_metrics_with_failure_context
}
```

### 3. Metadata Pruning

Add to `worktree_setup.sh`:
```bash
# Prune orphaned worktree metadata before branch creation
git worktree prune
```

## Acceptance Criteria

- [ ] All three old scripts deleted
- [ ] Any references to them updated (README, docs, CLAUDE.md)
- [ ] `watcher2.sh` documented as the single entry point
- [ ] Failure paths preserve worktree + topic for forensic inspection
- [ ] Success paths clean up normally (teardown worktree, delete topic)
- [ ] Orphaned worktree metadata pruned before branch creation
- [ ] No functional regression (watcher2.sh covers all old capabilities)
- [ ] Tests added validating forensic preservation behavior
- [ ] Documentation updated to reflect single orchestrator pattern

## Implementation Plan

### Phase 1: Update watcher2.sh failure handling

Current `handle_failure()` in watcher2.sh already preserves evidence correctly — no changes needed to failure paths.

### Phase 2: Remove failure handlers from success paths

Ensure `worktree_teardown` and topic deletion only occur on successful completion, not on failure branches.

### Phase 3: Delete obsolete scripts

```bash
rm .chaplain/watch.sh
rm scripts/enforce_worktree.sh  
rm scripts/bugfix_worktree.sh
```

### Phase 4: Update documentation

- Update `CLAUDE.md` to reference only `watcher2.sh`
- Update README and reference docs to remove old script references
- Add forensic workflow documentation

### Phase 5: Add orphaned metadata pruning

Extend `worktree_setup.sh` to call `git worktree prune` before branch creation.

## Dependencies

- FR-273 Phases 1-4 must be complete (watcher2.sh fully functional)
- Current implementation already shows correct forensic preservation in `handle_failure()`

## Alternatives Considered

1. **Gradual deprecation** — Keep old scripts with deprecation warnings
   - Rejected: Maintains confusion and code duplication
   
2. **Symlink aliases** — Point old script names to watcher2.sh
   - Rejected: Doesn't solve argument compatibility issues

3. **Migration period** — Run both systems in parallel
   - Rejected: Increases complexity without clear benefit

## Related

- FR-273: Watcher2 Pipeline (parent feature)
- FR-139: Worktree bare corruption guard
- FR-174: Worktree venv corruption guard
- FR-241: Complete worktree teardown self-heal

## Technical Notes

### Current Forensic Implementation

The `watcher2.sh` already implements correct forensic preservation:

```bash
handle_failure() {
    local reason="${1:-unknown}"
    log_error "Cycle failed: $reason"
    if [[ -n "${WT_DIR:-}" && -d "$WT_DIR" ]]; then
        log_warn "Worktree preserved for inspection: $WT_DIR"
    fi
    if [[ -n "${TOPIC_FILE:-}" && -f "$TOPIC_FILE" ]]; then
        local failed_name
        failed_name=$(basename "$TOPIC_FILE")
        mv "$TOPIC_FILE" ".chaplain/failed/$failed_name" 2>/dev/null || true
        log_warn "Topic moved to: .chaplain/failed/$failed_name"
    fi
    cd "$MAIN_DIR" 2>/dev/null || cd "$(dirname "$0")/.."
    write_cycle_metrics
}
```

The main task is ensuring this pattern is consistently used and the old destructive scripts are removed.

### Documentation Update Requirements

Files requiring updates:
- `CLAUDE.md` — Remove references to old scripts
- `README.md` — Update development workflow
- `reference/getting-started.md` — Update any pipeline references
- `.github/copilot-instructions.md` — Update any script references
- `docs/diary/` — Any procedural references

### Script Location Analysis

Current references found in:
- Multiple feature requests mention the old scripts
- Development documentation  
- Diary entries discussing pipeline evolution
- Changelog entries documenting the transition

All should be updated to reflect the single `watcher2.sh` orchestrator pattern.

## Research Brief

### Competitive Landscape

**DevOps/CI Pipeline Management:**
- **GitHub Actions** — Uses workflow_dispatch events for manual triggers, but no forensic preservation of failed runs (logs expire after 90 days)
- **LangGraph** — Low-level orchestration framework with [durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution) that automatically resumes from failures, but focused on agent workflows not DevOps pipelines
- **CrewAI** — Multi-agent automation framework independent of LangChain, but oriented toward AI agent orchestration rather than development pipeline management
- **AutoGen/Microsoft Agent Framework** — Now in maintenance mode, successor MAF focuses on multi-agent orchestration but not DevOps automation

**Key insight:** No competing LLM frameworks provide specialized DevOps pipeline forensics. Most CI/CD systems destroy failure context rather than preserving it for investigation. This is an internal tooling concern specific to YAMLGraph's development methodology.

### Existing Abstractions

**YAMLGraph Pipeline Components:**
- `/.chaplain/watcher2.sh` — Current orchestrator with forensic failure handling already implemented
- `/.chaplain/lib/watcher/` — 9 shell libraries handling worktree lifecycle, PR management, CI polling
- `/tests/unit/test_*worktree*.py` — 7 test files covering worktree integration patterns
- `/capabilities/CAP-33-worktree-pipeline.yaml` — Existing capability definition for worktree-based enforcement

**Overlap Assessment:** watcher2.sh already implements the desired forensic behavior — the task is removing legacy scripts, not building new abstractions.

### Diary Precedents

**Evidence Destruction Patterns:**
- **2026-04-21 audit-232**: `mixed_commits_erode_auditability: "One concern per commit → clear blame, clear revert"` — Evidence preservation principle already established
- **2026-03-09 audit-73**: `audit_as_ritual` trap — "3+ audits without fix → ritual, not process" — Detection without enforcement decays

**Pipeline Consolidation Wins:**
- **2026-04-22 FR-273 Phase 1**: "Test infrastructure from its deployment context" — watcher2 successfully replaced fragmented pipeline logic
- **2025-04-23 FR-273 Phase 4**: Pre-commit failure handling split between mechanical (shell) and semantic (LLM) boundaries — proper separation of concerns

**Working System Inertia Risk:**
- **2025-04-23 reflection**: "Working system inertia — The old `enforce_worktree.sh` was a monolithic 400+ line bash script that 'worked.' Breaking it into composable steps felt like unnecessary complexity until I mapped the retry semantics"

### Usage Evidence

- **Existing graphs using related abstractions:** 0 — This is pure infrastructure/DevOps tooling
- **Real-world use cases:** Internal development pipeline only (Chaplain watch daemon, enforce workflows)
- **Script references in codebase:** Only 1 direct reference found in CLAUDE.md/README.md
- **Test coverage:** 17 test files cover worktree/pipeline patterns, proving abstractions are well-established

### Classification Signal

- **Abstraction level:** pattern (consolidation/cleanup task, not framework primitive)
- **Recommended approach:** build (complete the FR-273 Phase 5 cleanup)
- **Key risk:** Working system inertia causing hesitation to remove "functional" legacy scripts despite superior replacement being proven in production