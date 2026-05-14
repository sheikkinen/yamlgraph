# Feature Request: FR-382 Prompt caching for Chaplain system prompts

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-14

## Summary

Apply Anthropic prompt caching where Chaplain prompts are actually executed through
the `type: llm` runtime path: convert
`.chaplain/graphs/watcher-enforce/prompts/context-planner.yaml` from `system:` to
`system_segments:` with a cached static segment and an uncached dynamic segment.

This FR is intentionally scoped to the currently cache-compatible surface and does
not modify Copilot-node prompt files.

## Value Statement

Watcher enforce runs get immediate, low-risk input-token savings on the
`plan_context` LLM call while avoiding behavior regressions in Copilot-backed nodes.

## Problem

The rough topic asked for blanket conversion of Chaplain prompt files. Research in
this worktree shows that is unsafe with current runtime contracts:

1. Chaplain prompt inventory has 16 files under `.chaplain/graphs/**/prompts/*.yaml`,
   all currently using `system: |`.
2. Only one active Chaplain node executes via `type: llm`:
   `watcher-enforce/enforce-session.yaml` → `plan_context` →
   `prompt: context-planner`.
3. Most Chaplain prompts are consumed by `type: copilot` nodes.
4. `yamlgraph/node_factory/copilot_node.py::_load_and_render_prompt()` reads
   `prompt_config["system"]` and `prompt_config["user"]` only; it does not read
   `system_segments`.

Therefore, converting Copilot-consumed prompts to `system_segments` in this FR would
drop their system instructions at runtime instead of enabling caching.

## Research: Existing Patterns and Prior Art

1. **Prompt-caching primitive already exists (no framework feature gap).**
   `executor_base.py` builds Anthropic `cache_control: {"type":"ephemeral"}` blocks
   from `system_segments` (`cache: true`) and flattens segments for non-Anthropic
   providers.
2. **Architecture traceability already defines this capability.**
   `ARCHITECTURE.md` capability 131 / REQ-YG-287..292, 303..306 documents
   `system_segments` and caching behavior.
3. **Reference syntax is stable.**
   `reference/prompt-yaml.md` defines `system_segments` entries with `content` and
   optional `cache` (not `text`).
4. **Cost mitigation plan remains directionally valid but over-broad for current runtime.**
   `docs/plan-token-cost-mitigation.md` lists prompt caching as priority 1; this FR
   narrows execution to cache-compatible prompts today.
5. **Prompt usage mismatch is measurable.**
   Chaplain graph configs reference 11 prompt names; 4 prompt files (`plan`,
   `research`, `summarize`, `write-acceptance-tests`) are currently unreferenced by
   active graph nodes and should not drive scope.

## Objectives

1. Use existing `system_segments` caching in a live Chaplain `type: llm` node.
2. Preserve current behavior for all `type: copilot` nodes.
3. Add explicit tests that lock this safe scope boundary.

## Constraints

1. **YAML-only change** for FR-382 implementation scope.
2. **No Copilot prompt conversion** until Copilot backend can consume
   `system_segments` (separate FR).
3. Use `system_segments[].content` schema as documented; no custom prompt syntax.
4. Reuse existing requirements (REQ-YG-287/289); no new requirement ID in this FR.

## Proposed Solution

### In scope

1. Convert `.chaplain/graphs/watcher-enforce/prompts/context-planner.yaml`:
   - static instruction corpus in `system_segments[0].content` with `cache: true`
   - runtime-variable lines in `system_segments[1].content` with `cache: false`
2. Keep all Copilot-consumed prompt files on `system:` unchanged.
3. Add focused unit tests to enforce the eligibility boundary.

### Out of scope

1. Converting Copilot-node prompt files (`plan-unified`, `judge`, `enforce-session`,
   `validate-session`, `sanity-check-session`, philosopher prompts, diary/forensic prompts).
2. Any Python runtime changes in `copilot_node.py`.
3. Broad prompt-file cleanup for unreferenced prompt templates.

## Acceptance Criteria

- [x] **AC-01:** `context-planner.yaml` uses `system_segments` and contains at least
  one `cache: true` segment.
- [x] **AC-02:** Cached segment(s) in `context-planner.yaml` contain no runtime
  placeholders (`{...}` or `{{ ... }}` tokens).
- [x] **AC-03:** Copilot-consumed Chaplain prompt files continue to use `system:`
  (no `system_segments` migration in this FR).
- [x] **AC-04:** `yamlgraph graph lint .chaplain/graphs/watcher-enforce/enforce-session.yaml`
  passes after the YAML change.
- [x] **AC-05:** New FR-382 tests are tagged with existing requirement IDs
  (`@pytest.mark.req("REQ-YG-287")` and/or `@pytest.mark.req("REQ-YG-289")`).

## Failing Acceptance Tests (RED plan)

Create:

- `tests/unit/test_fr382_chaplain_prompt_caching_scope_red.py`

Planned RED tests (must fail before implementation):

1. `test_ac01_context_planner_uses_system_segments_with_cached_block`
2. `test_ac02_context_planner_cached_segments_have_no_runtime_placeholders`
3. `test_ac03_copilot_chaplain_prompts_remain_system_field_only`
4. `test_ac03_prompt_inventory_scope_matches_graph_node_types`

RED command:

```bash
pytest tests/unit/test_fr382_chaplain_prompt_caching_scope_red.py -q --no-cov
```

Additional RED evidence command:

```bash
rg -n "^system_segments:|^system:\\s*\\|" .chaplain/graphs/**/prompts/*.yaml
```

## Alternatives Considered

1. **Convert all Chaplain prompt files now (issue rough topic as-is).**
   Rejected for this FR: Copilot runtime currently ignores `system_segments`, so
   this would remove system instructions from Copilot prompts.
2. **Add Copilot support for `system_segments` in the same change.**
   Rejected for single-responsibility scope; that is a Python runtime feature FR,
   not a YAML-only prompt conversion.
3. **Do nothing.**
   Rejected: leaves available LLM-path caching savings unused.

## Related

- Issue #382: <https://github.com/sheikkinen/yamlgraph/issues/382>
- `docs/plan-token-cost-mitigation.md`
- `ARCHITECTURE.md` capability 131 (REQ-YG-287..292, 303..306)
- `reference/prompt-yaml.md`
- `yamlgraph/executor_base.py`
- `yamlgraph/node_factory/copilot_node.py`

## Topic Source Note

Requested source file `.chaplain/processing/gh-382.md` is not present in this
worktree snapshot; planning source used was GitHub issue #382 plus in-repo
graphs/prompts/runtime code.
