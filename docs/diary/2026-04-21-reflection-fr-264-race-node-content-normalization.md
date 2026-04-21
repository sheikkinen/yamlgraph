# FR-264: Race Node parse_json & Content Normalization

**Date:** 2026-04-21
**FR:** FR-264
**Trap encountered:** `downstream_fix` — the symptom (wrong content type) manifests in race node consumers, but the root cause was at the provider boundary in `_invoke_candidate()`.

## Insight

The race node was born from FR-232 with a clean design — concurrent provider hedging. But it copied the *structure* of `_invoke_candidate` from a simpler time when only OpenAI was tested. Anthropic's list-of-blocks content format was already handled in `agent.py` via `_normalize_content()` (FR-059), but that knowledge didn't flow to the new race node module.

The One Law applies: normalize at the boundary where external data enters. For LLM responses, that boundary is where `.content` is read — not downstream where a consumer tries to JSON-parse a list instead of a string.

## Process

The fix was small (add normalization + parse_json), but the architectural decision to extract `_normalize_content` to `yamlgraph/utils/content.py` was the real value. Now every module that reads `.content` can import from one place. DRY enforced at the import-linter layer boundary.

The rubber-duck critique caught a blind spot: testing `parse_json` with only `str` content would miss the exact failure path (Anthropic list + JSON). Added a test for that combination.

## Heuristic

When adding a new node type that reads `response.content`, always apply `normalize_content()`. The provider boundary is the most common source of type lies.

**Seed:** Could we lint for raw `.content` access in node_factory modules and flag missing normalization calls?
