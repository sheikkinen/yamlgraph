# Feature Request: Watcher2 CI Remediation Crash Fix

**Priority:** HIGH  
**Type:** Bug  
**Status:** Proposed  
**Effort:** 0.5 days  
**Requested:** 2026-04-25  

## Summary

Fix critical bug in watcher2 CI remediation loop that crashes immediately at "remediation attempt 1/2" due to missing run ID in `gh run view --log-failed` command.

## Value Statement

Watcher2 daemon operators get working CI remediation capability, eliminating manual intervention when CI failures can be automatically fixed.

## Problem

The watcher2 CI remediation loop (lines 378-405 in `.chaplain/watcher2.sh`) crashes immediately at "remediation attempt 1/2" due to three cascading bugs:

### Bug 1: `gh run view --log-failed` exits non-zero without run ID (CRASH)
Line 383 runs `gh run view --log-failed --repo "sheikkinen/yamlgraph"` which requires a run ID in non-interactive mode. Without it, `gh` exits with code 1. Since `set -euo pipefail` is active (line 15), the non-zero exit kills the entire script before remediation can execute.

### Bug 2: `ci_log_path` relative path resolves to wrong directory
Line 383 writes `tmp/ci-failure.log` from `$MAIN_DIR`, but line 386 does `cd "$WT_DIR"` before passing `ci_log_path="tmp/ci-failure.log"` to the graph. The relative path resolves to the worktree, not the main dir where the file was written.

### Bug 3: No run ID means no actual CI logs captured
Even with a `|| true` guard, the command would capture `gh`'s usage error text instead of actual CI failure logs, making the remediation graph useless.

**Evidence**: PR #225 (FR-282) — watcher2 printed "CI failed — remediation attempt 1/2..." then exited with code 1. The `tmp/ci-failure.log` contained `gh`'s usage error, not CI logs.

## Proposed Solution

Replace the broken line 383 with a robust CI log capture sequence:

```bash
# Capture failure logs
RUN_ID=$(gh run list --branch "$WT_BRANCH" --status failure --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || echo "")
if [[ -n "$RUN_ID" ]]; then
    gh run view --log-failed --run "$RUN_ID" --repo "sheikkinen/yamlgraph" > "$MAIN_DIR/tmp/ci-failure.log" 2>&1 || true
else
    echo "No failed run found for branch $WT_BRANCH" > "$MAIN_DIR/tmp/ci-failure.log"
fi
```

And fix the path reference on line 388:
```bash
--var ci_log_path="$MAIN_DIR/tmp/ci-failure.log" \
```

## Acceptance Criteria

- [ ] `gh run view --log-failed` gets proper run ID from `gh run list --branch "$WT_BRANCH" --status failure --limit 1`
- [ ] CI log capture uses absolute path `"$MAIN_DIR/tmp/ci-failure.log"` for consistent resolution
- [ ] Command is guarded with `|| true` to prevent `set -e` crash on transient GH API failures  
- [ ] When no failed run exists, creates informative placeholder log instead of crashing
- [ ] Script continues to remediation graph execution instead of exiting with code 1
- [ ] Remediation graph receives actual CI failure logs, not `gh` usage error text
- [ ] Tests added to verify CI remediation pathway doesn't crash
- [ ] Documentation updated if applicable

## Alternatives Considered

### Alternative 1: Disable set -e for the command block
```bash
set +e
gh run view --log-failed --repo "sheikkinen/yamlgraph" > tmp/ci-failure.log 2>&1
set -e
```
**Rejected**: Masks other failures in the block and doesn't fix the missing run ID or path issues.

### Alternative 2: Use `gh pr checks` output instead of `gh run view`
**Rejected**: `gh pr checks` doesn't provide detailed failure logs needed for remediation.

### Alternative 3: Skip CI remediation entirely when `gh run list` fails
**Rejected**: Reduces reliability. Better to provide placeholder logs and let the remediation graph handle the "no logs" case.

## Related

- **Evidence**: PR #225 (FR-282) watcher2 crash  
- **Location**: `.chaplain/watcher2.sh` lines 378-405
- **Dependencies**: `.chaplain/lib/watcher/wait_ci.sh` (provides `$WT_BRANCH` context)
- **Related**: FR-273 (Watcher2 Pipeline) — broader watcher2 stability work

## Research Brief

### Competitive Landscape

- **GitHub Actions**: Native re-run capabilities (`gh run rerun`) but no automatic failure diagnosis/fix
- **GitHub CLI**: Built-in support for `gh run list --status failure` to query failed runs by branch and `gh run view --run $ID --log-failed` for specific run logs (confirmed in GitHub CLI docs)
- **nektos/act**: Local GitHub Actions runner for testing, but no production CI remediation patterns
- **CI automation tools**: Most handle retry/re-run but not intelligent diagnosis and auto-fix of failures

The proposed approach (query run ID then fetch logs) aligns with GitHub CLI's intended usage patterns and is the canonical way to programmatically access failure logs.

### Existing Abstractions

Error handling patterns in YAMLGraph:
- **`|| true` guards**: Used extensively in 52+ files for `set -euo pipefail` compatibility
- **Progressive remediation**: Established pattern in FR-281 with `ruff check --fix` then `--unsafe-fixes` before escalating to copilot
- **GitHub CLI integration**: Wait_ci.sh already uses `gh pr checks` for polling status
- **Path resolution**: `$MAIN_DIR` absolute paths used consistently in `.chaplain/lib/watcher/` modules

### Diary Precedents

Relevant traps and patterns from docs/diary/:
- **quick_confidence trap**: "When I feel certain → Judge instead" - relevant for shell debugging
- **downstream_fix trap**: Fix at boundary where external data enters, not where symptoms manifest  
- **boundary normalization**: External systems (GitHub CLI) require proper input validation and error handling
- **Progressive remediation pattern**: Safe fixes first, then unsafe, then intelligent escalation (established in FR-281)

### Usage Evidence

- Existing graphs using watcher2 remediation: **1 graph** (`examples/demos/watcher2-ci-remediation/`)
- **81 total references** to watcher2 across codebase indicating heavy operational usage
- **13 references** to ci remediation specifically
- Real-world use cases: Production daemon running continuously, handling FR proposals through full lifecycle

### Classification Signal

- **Abstraction level**: primitive (core infrastructure bug affecting daemon reliability)
- **Recommended approach**: build (critical bug fix for existing production system)  
- **Key risk**: This bug prevents the watcher2 CI remediation capability from functioning at all, causing immediate script termination and requiring manual intervention for recoverable failures