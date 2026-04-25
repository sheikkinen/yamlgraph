# Feature Request: FR-279 Watcher2 CI Resilience — Wait Logic + Remediation Loop

**Priority:** HIGH
**Type:** Bug + Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-04-25

## Summary

Fix two watcher2 CI pipeline bugs and add a copilot-driven CI remediation loop so that recoverable CI failures (syntax errors, missing fragments) are fixed automatically instead of requiring manual intervention.

## Value Statement

Watcher2 operators get a self-healing pipeline that handles transient and recoverable CI failures without manual admin merges or branch fixes.

## Problem

### Bug 1: Premature CI failure (wait_ci.sh)

`wait_ci.sh` checks for FAILURE before checking for IN_PROGRESS. When the status is `FAILURE,IN_PROGRESS,SKIPPED,SUCCESS` (e.g., security scan fails while tests are still running), watcher2 declares the cycle failed immediately — without waiting for remaining checks to finish.

Evidence from logs:
```
CI status (30s): FAILURE,IN_PROGRESS,SKIPPED,SUCCESS
CI failed for PR #214: FAILURE,IN_PROGRESS,SKIPPED,SUCCESS
```

This happened on PRs #184, #189, #214 — every time a fast-failing check (security, changelog gate) completes before the slower test jobs.

**Root cause:** In `wait_ci.sh`, the FAILURE grep (line 26) is evaluated before the IN_PROGRESS check (line 33). The correct priority is: if anything is still IN_PROGRESS, keep waiting.

### Bug 2: No CI remediation loop

When CI fails after push (e.g., IndentationError in a test file, missing changelog fragment), watcher2 gives up entirely (`handle_failure "CI"`). There is no mechanism to:

1. Diagnose the failure (read CI logs)
2. Fix the issue (invoke copilot to correct the code)
3. Push the fix and re-poll CI

This is inconsistent with the existing pre-commit remediation loop (step 4), which already invokes a copilot node after 5 failed attempts. The same pattern should extend to CI failures.

**Evidence:** PR #214 (FR-278) failed CI due to:
- `IndentationError` at line 267 of `test_prompt_caching_fr276.py` — a watcher2-generated syntax error
- Missing changelog fragment in `changelog/unreleased/`

Both were trivially fixable. A copilot node with access to `gh run view --log-failed` output could have diagnosed and fixed them automatically.

## Proposed Solution

### Fix 1: Swap check order in wait_ci.sh

```bash
# Check IN_PROGRESS first — wait for all checks to finish
if echo "$status" | grep -qiE "PENDING|IN_PROGRESS|QUEUED|REQUESTED|WAITING"; then
    sleep "$CI_POLL_INTERVAL"
    elapsed=$((elapsed + CI_POLL_INTERVAL))
    continue
fi

# Only evaluate failure after all checks are complete
if echo "$status" | grep -qiE "FAILURE|ERROR"; then
    CI_RESULT="failure"
    log_error "CI failed for PR #$PR_NUMBER: $status"
    return 1
fi
```

### Fix 2: CI remediation loop in watcher2.sh

After `wait_ci` fails, add a remediation cycle:

```bash
if ! wait_ci; then
    # Attempt CI remediation (max 2 attempts)
    CI_REMEDIATED=false
    for ci_attempt in 1 2; do
        log_warn "CI failed — remediation attempt $ci_attempt/2..."
        
        # Capture failure logs
        gh run view --log-failed ... > tmp/ci-failure.log 2>&1
        
        # Invoke copilot to diagnose and fix
        cd "$WT_DIR"
        if yamlgraph graph run "$ENFORCE_DIR/step-ci-remediate.yaml" \
            --var ci_log_path="tmp/ci-failure.log" \
            --var pr_number="$PR_NUMBER" \
            --import-state "$ENFORCE_STATE" \
            --full; then
            
            # Re-run finalize (pre-commit + push)
            git add -A && ruff check --fix ... && ruff format ...
            pre-commit run --all-files || true
            git add -A
            git commit -m "fix: watcher2 — CI remediation" --no-verify
            git push origin "$WT_BRANCH"
            
            cd "$MAIN_DIR"
            if wait_ci; then
                CI_REMEDIATED=true
                break
            fi
        fi
    done
    
    if [[ "$CI_REMEDIATED" != "true" ]]; then
        handle_failure "CI (after remediation)"
        continue
    fi
fi
```

### Graph: step-ci-remediate.yaml

A new copilot node graph that:
1. Reads CI failure logs from `ci_log_path`
2. Diagnoses the failure type (syntax error, missing file, test failure, etc.)
3. Applies the fix (correct indentation, create changelog fragment, etc.)
4. Returns the fix for the shell script to commit

## Acceptance Criteria

- [ ] `wait_ci.sh` waits for all IN_PROGRESS checks to complete before evaluating FAILURE
- [ ] CI remediation loop invokes copilot node on first CI failure
- [ ] Copilot node can read `gh run view --log-failed` output and apply fixes
- [ ] Maximum 2 remediation attempts before giving up
- [ ] Remediation covers: syntax errors, missing changelog fragments, missing diary entries
- [ ] Existing passing pipelines are unaffected (no behavioral change when CI passes first try)
- [ ] Tests added for wait_ci.sh check ordering
- [ ] step-ci-remediate.yaml graph created and tested
- [ ] step-ci-remediate prompt template created in enforce/prompts/

## Out of Scope

- Fixing CVE-related security scan failures (these require infrastructure changes, not code fixes)
- Fixing test logic failures (only structural/mechanical issues are remediable)

## Alternatives Considered

1. **Just fix wait_ci.sh ordering** — Solves the premature failure but doesn't address the missing remediation loop. Next copilot-generated syntax error will still require manual fix.
2. **Retry the entire enforce cycle** — Too expensive. Re-running implement+test+critique wastes API calls for issues that only need a small fix.
3. **Pre-CI validation step** — Run `python -c "import ast; ast.parse(...)"` on all test files before push. Catches syntax errors but not changelog/diary gate failures.

## Related

- `.chaplain/lib/watcher/wait_ci.sh` — CI polling logic
- `.chaplain/watcher2.sh` lines 360-363 — Current `handle_failure "CI"` with no remediation
- `.chaplain/graphs/watcher-enforce/step-finalize.yaml` — Existing remediation pattern for pre-commit failures
- PR #214 — Example of manual fix required for watcher2-generated syntax error
- PRs #184, #189 — Earlier instances of premature CI failure

## Research Brief

### Competitive Landscape

**No direct equivalents found.** Major LLM frameworks (LangGraph, CrewAI, AutoGen) focus on agent orchestration, not CI pipeline resilience:

- **LangGraph**: Provides checkpointing and human-in-the-loop but no CI failure remediation patterns
- **CrewAI**: Has error handling and retries but no specialized CI integration  
- **AutoGen** (maintenance mode): Agent coordination patterns only, no CI self-healing
- **GitHub Actions**: Native re-run capabilities (`gh run rerun`) but no automatic failure diagnosis/fix

**Key insight**: CI self-healing pipelines are not a common abstraction in existing frameworks. Most rely on manual intervention or simple retry logic without content analysis of failure logs.

### Existing Abstractions

YAMLGraph already has the core building blocks:

- **Copilot Node** (`CAP-30`): Proven abstraction for delegating to Copilot CLI with session continuity via `--resume`
- **Pre-commit Remediation Loop** (`.chaplain/watcher2.sh:313-337`): Existing 5-attempt loop with copilot fallback in `step-finalize.yaml`
- **CI Polling Logic** (`.chaplain/lib/watcher/wait_ci.sh`): Shell functions for `gh pr checks` status monitoring
- **Shell Remediation Pattern**: 23 existing copilot node usages across enforce pipeline graphs

**Gap**: No CI-specific remediation graph; existing `step-finalize.yaml` only handles pre-commit failures.

### Diary Precedents

**Relevant patterns from docs/diary/:**

- **"Normalize at the boundary"** (2026-04-22): Copilot CLI outputs can contain invalid UTF-8 — need `errors='replace'` at serialization
- **"Model name drift"** (2026-04-22): Copilot CLI model namespace differs from LLM factory; validate availability  
- **"Test infrastructure from deployment context"** (2026-04-22): Infrastructure scripts must be tested in their actual environment
- **"Pre-commit remediation cascades"** (2026-04-24): Auto-fixes trigger new failures; finalize step needs multiple retry attempts
- **"Audit-as-ritual"** trap: Repeated findings with no fixes become theater — remediation loops prevent this

**No negative precedents found** — no diary entries warn against automated CI remediation.

### Usage Evidence

- **Existing graphs using copilot nodes:** 23 (across chaplain pipeline, ebook examples, enforce steps)
- **Real-world use cases beyond watcher2:** 
  - Ebook authoring pipeline (automatic chapter generation + fixes)
  - Philosopher daemon (automatic diary reflection)
  - Bug fixing demos (syntax error correction)
- **Proven remediation pattern:** `step-finalize.yaml` successfully handles pre-commit failures with 5-attempt loop + copilot fallback

### Classification Signal

- **Abstraction level:** integration (extends existing copilot node + shell patterns)
- **Recommended approach:** build (fills genuine gap in watcher2 pipeline robustness)
- **Key risk:** Over-engineering simple CI failures that humans should diagnose manually.