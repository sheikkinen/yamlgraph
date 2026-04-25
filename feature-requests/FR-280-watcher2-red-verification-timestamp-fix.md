# Feature Request: FR-280 Watcher2 RED Verification Timestamp Fix

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-25

## Summary

The RED verification step in watcher2.sh never detects new test files because `find -newer` compares against the pipeline state file, which is always updated *after* the test files are written during the acceptance step.

## Value Statement

Watcher2 operators get proper TDD validation by ensuring RED verification actually runs and detects trivially-passing tests, preventing invalid acceptance tests from merging to main.

## Problem

In `watcher2.sh` line 176, the RED verification uses:

```bash
TEST_FILES=$(find tests/ -name "*.py" -newer "$PIPELINE_STATE" -type f 2>/dev/null)
```

The acceptance step (step 3) sequence is:
1. Run `step-acceptance.yaml` which writes test files to `tests/`
2. Export state to `$PIPELINE_STATE` via `--export-state` 
3. RED verification runs `find -newer "$PIPELINE_STATE"`

Since the state file is updated **after** test files are written, its mtime is always newer than the test files. The `find -newer` command finds nothing, causing the log message "No new test files found" and skipping RED verification entirely.

**Evidence from the processing file:**
- `pipeline-state.json` mtime: `1777098510`
- Newest test file `test_fr279_watcher2_ci_resilience.py` mtime: `1777098369`
- State file is 141 seconds newer, so `find -newer` returns empty

This violates **Commandment 7** (TDD Red-Green-Refactor): copilot-generated tests that pass trivially on unmodified code slip through undetected.

## Proposed Solution

Create a marker file **before** the acceptance step runs, then use it as the timestamp reference for RED verification:

```bash
# Before acceptance step (line 164)
ACCEPTANCE_MARKER="tmp/pre-acceptance-marker"
touch "$ACCEPTANCE_MARKER"

# After acceptance step, in RED verification (line 176)
TEST_FILES=$(find tests/ -name "*.py" -newer "$ACCEPTANCE_MARKER" -type f 2>/dev/null)

# Clean up marker after use
rm -f "$ACCEPTANCE_MARKER"
```

### Implementation Details

1. Create marker file at line 164 (before step 3 execution)
2. Update line 176 to reference marker file instead of `$PIPELINE_STATE`
3. Add cleanup in the RED verification section after test execution
4. Use `tmp/` directory for marker file (already created by watcher2.sh)

## Acceptance Criteria

- [ ] Marker file `tmp/pre-acceptance-marker` created before acceptance step runs
- [ ] `find -newer` references marker file, not pipeline state file
- [ ] RED verification correctly detects new test files written by acceptance step
- [ ] Trivially-passing tests produce warning (existing behavior, now actually triggered)
- [ ] Marker file cleaned up after RED verification
- [ ] Integration test verifies RED verification runs for new test files
- [ ] No regression in existing watcher2 functionality

## Alternatives Considered

1. **Use git timestamps**: Check `git log --since` instead of filesystem timestamps
   - **Rejected**: More complex, requires git state consistency checks

2. **Store acceptance step start time**: Capture timestamp before acceptance, use for comparison
   - **Rejected**: Race conditions with filesystem clock resolution

3. **Modify yamlgraph state export timing**: Delay state export until after RED verification
   - **Rejected**: Breaks state chaining contract and complicates error recovery

## Related

- `.chaplain/watcher2.sh` lines 165-191 (acceptance step and RED verification)
- FR-273 (Watcher2 Pipeline): Base implementation containing this bug
- FR-277 (Baseline checkpointing): Separate enhancement, same pipeline
- **Commandment 7**: TDD Red-Green-Refactor doctrine
- `lib/watcher/preflight.sh`: Uses similar `find -newer` patterns correctly
- Pipeline state contract: `--import-state` / `--export-state` in yamlgraph CLI

## Test Plan

### Unit Test
- Mock acceptance step writing test files
- Verify marker file exists and has correct timestamp
- Verify `find -newer marker` detects the new files

### Integration Test
- Run watcher2 with a topic that generates trivially-passing tests
- Verify RED verification runs and logs warning about trivial tests
- Verify marker file cleanup

### Regression Test
- Verify existing watcher2 functionality unchanged
- Verify state chaining still works correctly