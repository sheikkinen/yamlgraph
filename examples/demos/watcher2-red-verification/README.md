# Watcher2 RED Verification Timestamp Fix Demo

**Feature:** FR-280 Watcher2 RED Verification Timestamp Fix

This demo proves that the timestamp coordination bug in watcher2.sh has been fixed.

## Problem Demonstrated

The watcher2 pipeline had a timing bug where the RED verification step would never detect new test files because:

1. Acceptance step writes test files at time T1
2. Pipeline state is exported at time T2 (T2 > T1)  
3. `find tests/ -name "*.py" -newer "$PIPELINE_STATE"` finds nothing because state file is newer

This violated **Commandment 7** (TDD Red-Green-Refactor) by allowing trivially-passing tests to slip through undetected.

## Solution Implemented

The fix uses a marker file approach:

1. Create `tmp/pre-acceptance-marker` BEFORE running acceptance step
2. Use `find tests/ -name "*.py" -newer "$ACCEPTANCE_MARKER"` for RED verification
3. Clean up marker file after verification

## Demo Structure

- `graph.yaml` - Simulates the timestamp scenarios using shell commands
- `prompts/` - Contains prompts that demonstrate the fix
- `demo-output.log` - Proof that the fix works correctly

## Running the Demo

```bash
yamlgraph graph run examples/demos/watcher2-red-verification/graph.yaml \
  --var scenario=fixed --full
```

## Expected Output

The demo shows:
1. **Buggy scenario**: `find -newer pipeline_state` finds no files (broken)
2. **Fixed scenario**: `find -newer marker_file` finds test files correctly (working)
3. **Verification**: The marker file approach detects new tests as expected

This proves that RED verification now works correctly and will catch trivially-passing tests.