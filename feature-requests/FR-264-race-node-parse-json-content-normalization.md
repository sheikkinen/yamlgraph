# Feature Request: Race Node parse_json and Content Normalization

**Priority:** HIGH
**Type:** Bug / Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-21

## Summary

Add content normalization and `parse_json` support to race nodes, aligning them with the LLM node contract.

## Value Statement

Race nodes silently return provider-specific content types (Anthropic: `list[dict]`, OpenAI: `str`) instead of normalized strings. This violates the "normalize at the boundary" principle (FR-059) and causes downstream breakage when graphs switch between providers. Additionally, `parse_json: true` — supported by LLM nodes — is silently ignored by race nodes, forcing users to add a separate JSON extraction step.

## Problem

1. **Content normalization missing**: `_invoke_candidate()` in `race_node.py` returns `response.content` raw. Anthropic Claude returns content as `[{"type": "text", "text": "..."}]` (list of blocks), while OpenAI returns a plain `str`. The normalization pattern from FR-059 (`_normalize_content` in `agent.py`) is not applied.

2. **`parse_json` not supported**: LLM nodes support `parse_json: true` to extract JSON from LLM responses via `extract_json()`. Race nodes don't read this config at all — the JSON response comes back as a raw string.

Both issues violate the One Law: "Normalize at the boundary where external data enters, not downstream where it manifests."

## Proposed Solution

1. Extract `_normalize_content()` from `yamlgraph/tools/agent.py` into a shared utility `yamlgraph/utils/content.py` so both Layer 2 (node_factory) and Layer 3 (tools) can import it.

2. Apply `normalize_content()` in `_invoke_candidate()` for unstructured responses.

3. Add `parse_json` support to `create_race_node()`:
   - When `parse_json=true`, skip `output_model` resolution (same as `llm_nodes.py`)
   - After normalization, apply `extract_json()` to the result

4. Add `parse_json: bool = False` field to `NodeConfig` in `graph_schema.py` for type safety.

### Integration Points

| Component | Change |
|-----------|--------|
| `yamlgraph/utils/content.py` | New: shared `normalize_content()` |
| `yamlgraph/node_factory/race_node.py` | Apply normalization + parse_json |
| `yamlgraph/tools/agent.py` | Import from shared utility |
| `yamlgraph/models/graph_schema.py` | Add `parse_json` field to `NodeConfig` |
| `reference/graph-yaml.md` | Document `parse_json` in race node table |

## Acceptance Criteria

- [x] Race node normalizes `response.content` to string (handles list/str/None)
- [x] Race node supports `parse_json: true` config
- [x] `parse_json` skips `output_model` resolution at factory time
- [x] Content normalization extracted to shared `yamlgraph/utils/content.py`
- [x] `agent.py` imports from shared utility (no duplication)
- [x] `NodeConfig` has explicit `parse_json: bool` field
- [x] Reference docs updated with `parse_json` in race node table
- [x] Unit tests cover: list content, string content, parse_json extraction, parse_json with list content

## Related

- **FR-059**: Provider content normalization (original fix in agent.py)
- **FR-232**: Race node type (original implementation)
- **Knowledge Graph**: `the_one_law` — normalize at boundary
- **Knowledge Graph**: `boundaries.provider` — API responses differ

## Judgement

**Verdict: APPROVE** — Scope frozen. Two-gap fix, well-bounded, single FR.

**Date:** 2026-04-21
