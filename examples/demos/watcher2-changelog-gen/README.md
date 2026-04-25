# Watcher2 Changelog Fragment Auto-Generation Demo

This demo demonstrates the FR-283 feature that automatically generates changelog fragments in the watcher2 pipeline, eliminating the #1 cause of manual intervention in PRs.

## Problem Solved

Before FR-283, every watcher2 PR required manual changelog fragment creation, causing 100% failure rate (5/5 recent PRs needed manual intervention).

## Solution

Defense-in-depth changelog fragment auto-generation at 4 layers:
1. **Shell Step**: Primary generation between critique and finalize
2. **Critique Prompt**: Part 3 instructions for changelog creation
3. **Finalize Prompt**: Part 0 verification before pre-commit
4. **CI Remediation**: FR context for correct fragment naming

## Demo

This demo simulates the watcher2 environment and shows how changelog fragments are automatically generated with:
- Correct FR number extraction from FR_PATH
- Descriptive filename generation (max 40 chars)
- REQ-YG-XXX lookup from capabilities registry
- Proper YAML frontmatter structure
- Cross-wiring prevention

## Running the Demo

```bash
yamlgraph graph run examples/demos/watcher2-changelog-gen/graph.yaml \
  --var fr_path="feature-requests/FR-283-auto-generate-changelog-fragments-watcher2.md" \
  --full
```

The demo will show the changelog generation logic in action and create a sample fragment.