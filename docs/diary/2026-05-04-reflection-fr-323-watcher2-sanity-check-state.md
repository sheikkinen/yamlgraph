# Reflection: FR-323 Watcher2 Sanity Check

**Date:** 2026-05-04
**FR:** FR-323 Vertex Gemini 3.1 hello smoke coverage
**Reviewer:** watcher2 (post-validate)

## Trap

`demo_vs_test` — demo-output.log committed as gate evidence without verifying
the run succeeded. The log shows an ERROR (missing Anthropic API key, not even
Vertex), yet the file satisfies the demo-gate CI check mechanically.

## What Happened

The implementation is proportional: 5 files, 255 lines, all additions.
Test file covers AC-01 through AC-04 with correct skipif guards. AC-03 is
tautological — it either skips (no key) or trivially asserts the key exists —
but is non-harmful.

The `demo-output.log` records a failed execution:

```
[ERROR] yamlgraph.error_handlers: Node greet failed: "Could not resolve authentication method."
```

The graph ran with `anthropic/claude-haiku-4-5` (not Vertex) and failed due to
a missing Anthropic key. No Vertex Gemini 3.1 execution is evidenced in the log.
The demo-gate only checks file presence, not success — so CI will pass, but the
artifact is misleading.

## Root Cause

The demo was run in an environment without any configured API key. The provider
defaulted to Anthropic instead of Vertex (PROVIDER/VERTEX_API_KEY not exported
before running the CLI smoke command). The resulting error log was committed
without inspection.

## What Worked

- FR/code alignment: AC-01, AC-02, AC-04, AC-05 are genuinely covered.
- Test assertions check behavior (greeting contains "World"), not just
  invocation shape.
- Changelog fragment and README updates are clean and accurate.
- No changes to existing provider code — scope constraint respected.

## Seed

If demo-gate only validates file presence, could a lightweight log-linter
(checking for absence of `[ERROR]` on the final node) be added as a
post-demo-gate step without requiring live API access in CI?
