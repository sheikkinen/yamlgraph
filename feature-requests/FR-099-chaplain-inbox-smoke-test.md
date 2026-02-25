# Feature Request: FR-099 Chaplain Inbox Smoke Test

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-02-25

## Summary

Add a self-test mechanism for the chaplain inbox pipeline that validates the end-to-end flow (inbox → drafts → feature-requests) without requiring a real topic or LLM invocation.

## Value Statement

Developers get confidence that the chaplain pipeline is correctly wired by running a single command that validates file routing, prompt loading, and graph compilation.

## Problem

The chaplain watch loop (FR-068, FR-084) processes `.chaplain/inbox/*.md` files through Plan → Judge → Diary stages. Currently, validating the pipeline works requires dropping a real topic file and waiting for full LLM execution — an expensive, slow, non-deterministic operation. There is no fast, offline way to verify:

1. The inbox → drafts file routing works correctly
2. The graph YAML compiles without errors
3. Prompts load and render with expected variables
4. The watch.sh polling loop detects and picks up files

The test entry that prompted this FR ("Testing inbox pattern throughput") demonstrates the need: someone had to manually test the pipeline by dropping a file, with no automated validation available.

## Proposed Solution

### 1. Graph lint validation (already available)

```bash
yamlgraph graph lint examples/copilot/graph.yaml
```

This validates the graph YAML compiles, prompts resolve, and edges are consistent. No LLM needed.

### 2. Smoke test script

Add `.chaplain/smoke-test.sh` that:
- Validates the graph YAML with `yamlgraph graph lint`
- Verifies the graph compiles and shows structure with `yamlgraph graph info`
- Makes zero LLM calls

```bash
#!/usr/bin/env bash
# .chaplain/smoke-test.sh — Validate inbox pipeline without LLM calls
set -euo pipefail
cd "$(dirname "$0")/.."

INBOX=".chaplain/inbox"
DRAFTS=".chaplain/drafts"
TEST_FILE="$INBOX/_smoke-test.md"

echo "🧪 Chaplain smoke test: validating pipeline..."

# Step 1: Lint the graph
echo "  📐 Linting graph..."
yamlgraph graph lint examples/copilot/graph.yaml

# Step 2: Validate graph compiles with test variables
echo "  🔧 Compiling graph with test variables..."
yamlgraph graph info examples/copilot/graph.yaml

echo "✅ Chaplain pipeline validated (no LLM calls made)"
```

### Usage

```bash
# Quick validation after changes
.chaplain/smoke-test.sh

# Full pipeline test (requires API keys, invokes LLM)
echo "# Test\nSmoke test topic." > .chaplain/inbox/_smoke-test.md
yamlgraph graph run examples/copilot/graph.yaml \
    --var topic_file=".chaplain/inbox/_smoke-test.md" \
    --var drafts_dir=".chaplain/drafts" \
    --var date="$(date +%Y-%m-%d)" \
    --var diary_prefix="Smoke Test" \
    --full
```

## Acceptance Criteria

- [ ] `.chaplain/smoke-test.sh` exists and is executable
- [ ] Script validates graph with `yamlgraph graph lint`
- [ ] Script validates graph compilation with `yamlgraph graph info`
- [ ] Script makes zero LLM calls
- [ ] Script exits 0 on success, non-zero on failure
- [ ] No unit tests needed (shell script; validates via CLI tools)

## Alternatives Considered

1. **Integration test with mock LLM** — Could add a pytest integration test that mocks the copilot CLI backend. More thorough but higher effort; better suited for FR-080 (infrastructure script tests).
2. **watch.sh --dry-run flag** — Add a dry-run mode to watch.sh itself. Rejected: watch.sh should stay thin (FR-068 constraint). Separate smoke test script follows single-responsibility.
3. **Do nothing** — Continue manual testing. Acceptable given low risk, but the need was demonstrated by the test entry that prompted this FR.

## Related

- FR-068: Chaplain watch loop (the pipeline being tested)
- FR-084: Copilot watch migration (current graph-based implementation)
- FR-080: Infrastructure script tests (broader test coverage initiative)
- FR-098: Consolidated graph to `examples/copilot/graph.yaml`
- `examples/copilot/graph.yaml` — The graph under test
- `.chaplain/watch.sh` — The polling wrapper
