# FR-653: Robust reflect prompt schema compliance

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
**Effort:** 0.25 days
**Requested:** 2026-07-02

## Summary

The reflect node fails in 2 of 3 loops because the LLM returns a flat dict instead of the expected `{updated_page, new_entities}` shape from the deepen map node. This causes reflect to error on `'dict object' has no attribute 'updated_page'`, losing red-link expansion opportunities.

## Value Statement

Reliable reflection doubles the world expansion rate per loop by finding concepts mentioned in prose but lacking pages.

## Problem

Evidence from last two pipeline runs:
- `Node _map_deepen_sub failed: 2 validation errors for DeepenedEntity` (missing updated_page, new_entities)
- `Node reflect failed: 'dict object' has no attribute 'updated_page'`

The deepen schema expects `{updated_page: dict, new_entities: list}` but DeepSeek sometimes returns the page directly as a flat dict. The reflect prompt then tries to iterate `deepened` entries and access `.updated_page` which doesn't exist.

## Proposed Solution

Two fixes:

1. **Normalize deepen output in collect_red_links**: If a deepened entry is a dict without `updated_page`, wrap it: `{"updated_page": entry, "new_entities": []}`.

2. **Make reflect prompt tolerant**: Access deepened entries defensively — if `d.updated_page` fails, treat `d` as the page itself.

## Acceptance Criteria

- [ ] collect_red_links handles flat-dict deepened entries without error
- [ ] reflect node completes even when deepen returns non-schema output
- [ ] Test covers flat-dict normalization in collect_red_links
- [ ] Pipeline run shows reflect completing in all loops

## Related

- [nodes/collect_red_links.py](../examples/novel_fandom/nodes/collect_red_links.py)
- [prompts/reflect_canon.yaml](../examples/novel_fandom/prompts/reflect_canon.yaml)

## Judgement

**Verdict: Granted with amendments.**

### What's sound
- The error chain is clear: deepen returns flat dict → reflect fails → red links lost.
- Normalizing in collect_red_links (Python node) is the right boundary.

### Amendments

1. **Fix location is collect_red_links, not reflect prompt.** The reflect prompt accesses `deepened` via Jinja2 (`d.updated_page`). The actual failure is in `collect_red_links` which iterates `result.get("new_entities", [])` — when result IS the page (flat dict), new_entities is missing and red links are silently empty. Fix: if `result` has no `updated_page` key, wrap it. The reflect prompt also needs a guard but the primary fix is in Python.
2. **Also normalize in persist_pages** — `_persist_impl` already accesses `result.get("updated_page", {})`. If result is the flat page, updated_page is empty dict and nothing gets written. Add: if `updated_page` is empty but result has `id` and `type`, use result as the page.

### Scope freeze
Two files: `collect_red_links.py`, `persist_pages.py` (deepened loop normalization). Reflect prompt untouched.
