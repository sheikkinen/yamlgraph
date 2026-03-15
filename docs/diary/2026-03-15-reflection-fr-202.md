# 2026-03-15 — FR-202 Image Generation Pipeline

## Context
Implementing an end-to-end image generation pipeline that chains LLM concept generation, subgraph prompt decomposition, file I/O, and Replicate image generation.

## Cognitive Process
The FR was well-structured with clear acceptance criteria and all Judge amendments already resolved. The main challenge was conforming to the existing patterns: `type: python` tool registration, subgraph node configuration, and the storyboard prior art for Replicate integration.

## Trap Avoided
**intent_drift** — The FR specified `_embed_exif()` with try/except/pass, but ruff's SIM105 flagged this. Refactored to `contextlib.suppress()` which is both cleaner and lint-compliant. The semantic intent (best-effort, silent skip) is preserved.

## Insight
The `examples/README.md` audit test (`test_all_toplevel_examples_listed_in_readme`) caught a missing index entry. This is a good example of **detection_without_enforcement** graduating to **enforcement_at_merge_boundary** — the test would have blocked the PR.

## Heuristic
When adding a new example directory, always check: (1) examples/README.md index, (2) ARCHITECTURE.md capability table, (3) capabilities/ registry YAML. These three are coupled by CI gates.

## Seed
Could the req_coverage script auto-detect when a new example directory appears without a corresponding CAP-XX.yaml entry, rather than waiting for a phantom-requirement failure?
