# Feature Request: Watcher2 Forensic Failure Diary

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-04-25

## Summary

Add a forensic analysis phase to watcher2's `handle_failure` function that generates diagnostic diary entries for every failed cycle before moving topics to the failed queue.

## Value Statement

Watcher2 operators get root cause analysis for every failure instead of silent moves to failed queue, reducing debug time and creating institutional learning artifacts.

## Problem

Currently when watcher2 cycles fail, they are silently moved to `.chaplain/failed/` with minimal context. Failed cycles become "black holes" with no diagnostic information about why they failed, what logs were relevant, or what state the worktree was in. This pattern prevents learning from failures and makes debugging challenging.

The current `handle_failure` function only:
1. Logs the failure reason
2. Preserves the worktree directory
3. Moves the topic file to `.chaplain/failed/`
4. Writes cycle metrics

There's no analysis of the failure context, no capture of relevant logs, and no structured diagnosis of root causes.

## Proposed Solution

Extend the `handle_failure` function to add a forensic analysis phase that invokes a Copilot session to:

1. **Read failure context**: Topic content, failure reason, and relevant logs
2. **Analyze logs**: Parse `tmp/watcher2-*.log` files for error patterns
3. **Inspect worktree state**: Check git status, file modifications, CI output
4. **Generate diagnosis**: Write a structured diary entry with root cause analysis
5. **Preserve evidence**: Move enhanced failure record to failed queue

The forensic analysis should produce diary entries following the established pattern:

```yaml
# Example forensic diary entry structure
title: "Forensic: watcher2-{topic-name}-{reason}"
failure_reason: "implement step"  # From handle_failure parameter
root_cause: "TDD test compilation error in test_new_feature.py:15"
evidence:
  - logs: ["tmp/watcher2-implement.log"]
  - worktree_state: "Modified files: yamlgraph/new_feature.py, tests/unit/test_new_feature.py"
  - git_status: "uncommitted changes present"
recommendations: 
  - "Add syntax validation before test execution"
  - "Check import statements in TDD red phase"
seed: "Could watcher2 pre-validate test syntax before running pytest?"
```

## Acceptance Criteria

- [ ] `handle_failure` function includes forensic analysis phase before topic archival
- [ ] Forensic analysis reads failure reason, topic content, and relevant logs
- [ ] Analysis generates structured diary entry in `docs/diary/` with forensic prefix
- [ ] Diary entry includes root cause, evidence summary, and recommendations
- [ ] Enhanced failure record preserved in `.chaplain/failed/` with diary reference
- [ ] Forensic phase only runs if Copilot session available (fail gracefully)
- [ ] Tests added for forensic diary generation
- [ ] Documentation updated for new failure handling workflow

## Alternatives Considered

**Option 1: Log aggregation only**
- Collect all logs into failed directory without analysis
- Pros: Simple, fast, preserves evidence
- Cons: No structured analysis, still requires manual diagnosis

**Option 2: External forensic script**
- Separate script runs forensic analysis on failed queue
- Pros: Decoupled from watcher2, can batch process
- Cons: Delayed analysis, context may be lost, not integrated

**Option 3: Minimal context capture**
- Just capture git diff and last log entries
- Pros: Lightweight, automated evidence collection
- Cons: No intelligent analysis, pattern recognition, or recommendations

**Chosen solution provides**: Real-time analysis while context is fresh, structured learning artifacts, and integration with existing diary workflow.

## Related

- `.chaplain/watcher2.sh` - Current failure handling implementation
- `docs/diary/` - Existing diary patterns and forensic precedents  
- `.chaplain/graphs/watcher-diary/` - Diary generation infrastructure
- `.chaplain/lib/diary.py` - Diary writing utilities
- FR-273 - Watcher2 pipeline implementation (phases 1-4)
- FR-284 - CI remediation crash fix (recent failure handling improvement)