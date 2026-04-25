# Watcher2 AMEND Retry Loop Demo

This demo simulates the watcher2 AMEND retry loop functionality implemented in FR-286.

## What This Demonstrates

The watcher2 pipeline now handles AMEND verdicts by:
1. Extracting judge feedback from the verdict
2. Running a revision step with that feedback
3. Re-judging the revised feature request
4. Repeating up to 2 times if still AMEND
5. Falling back to handle_failure if retries exhausted

## Demo Flow

This demo simulates the core components:

1. **Judge Step**: Mock judge that issues AMEND verdict with feedback
2. **Revision Step**: Mock revision that incorporates feedback
3. **Retry Logic**: Shows the loop with feedback extraction

## Components

- `graph.yaml` - Main demo graph simulating the judge/revise loop
- `prompts/judge.yaml` - Mock judge that issues AMEND with feedback
- `prompts/revise.yaml` - Mock revision step that uses feedback
- `prompts/final-judge.yaml` - Final judge that approves after revision

## Usage

```bash
yamlgraph graph run examples/demos/watcher2-amend-retry/graph.yaml \
  --var initial_request="Create a simple REST API" \
  --full
```

## Expected Output

The demo will show:
1. Initial judge verdict: AMEND with specific feedback
2. Feedback extraction and revision process
3. Re-judge showing improvement
4. Final APPROVE verdict

This demonstrates that AMEND no longer terminates the pipeline but triggers iterative improvement.
