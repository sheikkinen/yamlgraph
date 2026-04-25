# 2026-04-25 Reflection: FR-219 Anthropic Prompt Caching Demo

**Context:** Implementing a demonstration of Anthropic prompt caching using system_segments to validate FR-276's implementation and educate graph authors on cost optimization patterns.

**Trap:** **intent_drift** — Initially wrote tests expecting `config.nodes` to be a list of objects with `.type` attributes, but the actual GraphConfig uses dict-based node structure. Plan said "follow existing patterns" but code diverged from established dict access patterns used throughout the codebase.

**Heuristic:** When writing acceptance tests for existing interfaces, examine multiple usage examples in the codebase before writing test logic. The pattern `config.nodes["node_name"]["type"]` appears in 10+ existing tests, while the assumed list pattern appears in none. **Trace the interfaces before testing the interfaces.**

**Solution Applied:**
- Fixed test to use `[(name, cfg) for name, cfg in config.nodes.items() if cfg.get("type") == "llm"]`
- Added missing `provider` field to GraphConfig with fallback to `defaults.provider`
- Both changes follow established codebase patterns

**Secondary Discovery:** The linter correctly identified that top-level `provider:` should be in `defaults:` block, but this broke tests expecting top-level access. The GraphConfig needed to resolve provider from both locations to maintain contract while following best practices.

**Seed:** How can TDD acceptance tests automatically validate against established interface patterns to prevent **intent_drift** from assumed interfaces? Could we generate interface compliance tests from existing usage patterns in the codebase?