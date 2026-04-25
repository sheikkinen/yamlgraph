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

## Research Brief

### Competitive Landscape

This is a system-specific bug fix rather than a competitive feature, but investigation revealed:

- **GitHub Actions**: Uses `actions-cache` to manage timestamp-based file detection, but internal runners have similar timestamp coordination challenges (see [actions/runner#659](https://github.com/actions/runner/issues/659) discussing path prefixes for monorepos with asynchronous build steps)
- **CI/CD Systems**: Jenkins, CircleCI, and GitLab CI all face similar issues with file modification timestamps vs. state persistence timing — most solve with explicit marker files or git-based change detection
- **LangChain/LangGraph**: No equivalent RED verification pattern found — they rely on standard test frameworks without custom timestamp-based test file discovery
- **Testing Frameworks**: Pytest, Jest, and similar tools use explicit file patterns, not filesystem timestamps, avoiding this entire class of issues

**Finding**: The marker file approach is a well-established pattern in CI/CD systems for coordinating between asynchronous steps.

### Existing Abstractions

Search revealed YAMLGraph has extensive state chaining infrastructure that this bug affects:

- **CLI State Chain Pattern** (FR-269): `--export-state` / `--import-state` used in 67+ locations across the codebase
- **Pipeline State Persistence**: `yamlgraph/storage/export.py` handles state serialization/deserialization
- **Watcher2 Integration**: 15 occurrences of state chaining in `watcher2.sh` alone
- **`find -newer` Usage**: Only 2 total usages in codebase - the buggy one in `watcher2.sh:176` and the FR-280 documentation

**No existing timestamp coordination patterns** were found - this is the first case where yamlgraph needs to coordinate filesystem timestamps with state export timing.

### Diary Precedents

Key diary patterns relevant to this bug:

- **`partial_remediation` trap** (audit-180): "renumber touched ARCHITECTURE.md and tests but skipped the changelog boundary entirely" — similar pattern where the state file update didn't account for all affected boundaries
- **`state_boundary` normalization** (reflection-fr-238): "Adding reducer logic at the TypedDict generation layer (downstream) rather than normalizing at `parse_state_config()` (the boundary)" — demonstrates the Scripture principle of fixing at the boundary where external data enters
- **TDD Red-Green discipline violations** (reflection-fr-229): Several diary entries about "test-after-fix" being "trap-prone" because "absence of a RED phase makes verification feel trivially performative"

**Pattern Match**: This bug exemplifies the `downstream_fix` trap - the state export happens downstream from where test files are created, causing the verification step to fail silently.

### Usage Evidence

- **Existing graphs using state chaining**: 24 files use `--import/export-state` extensively
- **Watcher2 pipeline dependents**: The bug affects all current and future watcher2 operations (100% impact on automation pipeline)
- **Real-world use cases beyond the proposal**: This is core to the watcher2 TDD enforcement pipeline - no alternative use cases, but critical to the entire .chaplain automation system

**Test verification is currently broken** for all watcher2 cycles, making this a systemic infrastructure bug rather than an edge case.

### Classification Signal

- **Abstraction level**: primitive (affects core infrastructure)
- **Recommended approach**: build (surgical fix to existing pattern)  
- **Key risk**: The fix is straightforward but validates a previously unnoticed infrastructure assumption that could affect other timestamp-dependent operations in the codebase.