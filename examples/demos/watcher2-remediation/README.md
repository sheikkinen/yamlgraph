# Watcher2 Remediation Demo

Demonstrates the enhanced watcher2 remediation loop that can automatically fix ruff SIM117 (nested with statements) errors using progressive `--unsafe-fixes`.

## What This Demonstrates

This demo shows how the watcher2 pipeline now handles SIM117 violations automatically:

1. **Progressive Ruff Strategy**: Safe fixes first (`ruff check --fix`), then unsafe fixes (`ruff check --fix --unsafe-fixes`) for remaining issues
2. **SIM117 Auto-Fixing**: Nested `with` statements are automatically combined into single statements
3. **Enhanced Copilot Context**: Remediation prompts now include specific ruff error codes for better diagnosis

## Problem Before FR-281

Previously, watcher2 would crash when encountering SIM117 violations because:
- `ruff check --fix` cannot fix SIM117 (requires `--unsafe-fixes`)
- Copilot remediation lacked specific error code context
- 5-attempt remediation loop failed entirely instead of partial success

## Solution After FR-281

The enhanced remediation pipeline:
1. Runs `ruff check --fix` for safe auto-fixes
2. Runs `ruff check --fix --unsafe-fixes` for remaining issues like SIM117
3. Falls back to copilot with specific error code guidance if needed
4. Validates changelog fragment FR numbers match branch names

## Demo Files

- `nested_with_example.py`: Sample file with SIM117 violations
- `graph.yaml`: Simple graph that processes files (simulates code generation)
- `demo-script.sh`: Shows the progressive remediation in action

## How to Run

```bash
# Lint the demo graph
yamlgraph graph lint examples/demos/watcher2-remediation/graph.yaml

# Run the demo
yamlgraph graph run examples/demos/watcher2-remediation/graph.yaml \
  --var topic="file processing" \
  --full 2>&1 | tee examples/demos/watcher2-remediation/demo-output.log

# Show the remediation script in action
./examples/demos/watcher2-remediation/demo-script.sh
```

## Expected Behavior

1. The graph runs successfully
2. The demo script shows SIM117 violations being fixed automatically
3. Progressive ruff commands demonstrate the FR-281 enhancement
4. Output shows before/after code transformation
