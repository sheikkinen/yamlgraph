# Reflection: FR-277 Baseline Checkpointing Implementation

**Context:** Implementing baseline checkpointing for the Chaplain watcher2 daemon to prevent redundant processing of unchanged source files through deterministic hash-based caching.

**Trap:** **quick_confidence** - Initially felt certain about hash determinism without considering content normalization edge cases (line endings, whitespace, encoding differences). The first hash implementation would have failed in cross-platform scenarios.

**Heuristic:** When implementing content-addressed caching, always normalize at the boundary where external files enter the system. Test hash determinism explicitly across different environments, not just within a single test run. The one law: "Normalize at the boundary where external data enters, not downstream where it manifests."

**Seed:** Could baseline checkpointing be generalized beyond watcher2? What if every YAMLGraph execution had optional content-addressed caching to avoid re-running unchanged graph definitions? The pattern of manifest → hash → cache → symlink might apply to graph compilation itself.

**Learning:** TDD discipline proved essential - the 13 failing tests provided a clear contract that prevented scope creep and ensured all edge cases were covered. Starting with comprehensive test failures made implementation focused and complete.

**Architecture Victory:** The isolated `yamlgraph.chaplain.baseline` namespace prevented contamination of the core framework while enabling sophisticated caching behavior. This demonstrates the power of the 3-layer pattern for complex features.
