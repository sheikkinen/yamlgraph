# Feature Request: FR-327 reference doc for LLM-as-gate pattern

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-05

## Summary

Add `reference/patterns/llm-as-gate.md` as a focused pattern reference showing how to implement semantic pass/fail gating with existing YAMLGraph primitives (`type: router` + structured schema + routing edges), with no new node/action type.

## Value Statement

Graph authors get a discoverable, reusable semantic-gate pattern that closes a documentation gap without increasing framework surface area.

## Problem

GitHub issue #327 requests a first-class reference for “LLM-as-gate.” The framework already supports this composition, but current docs do not isolate it as a dedicated pattern.

Requested topic file `.chaplain/processing/gh-327.md` is not present in this worktree, so canonical topic input was taken from issue #327.

## Research Findings

1. **Router contract already exists.** `reference/graph-yaml.md` documents `type: router`, `route_field`, and `routes`.
2. **Related patterns exist, but not this exact one.** `reference/patterns.md` has conditional routing (Pattern 2) and map-output quality gate (Pattern 12), but not a dedicated binary semantic gate reference.
3. **In-repo prior art proves semantic + mechanical gates can coexist.** `.chaplain/config/watcher-pipeline-v2.yaml` routes semantic `PASS`/`WARN` outcomes separately from deterministic `validate_gate`.
4. **No runtime implementation gap found.** This is a documentation/discoverability gap only; existing primitives are sufficient.

## Objectives

1. Publish one dedicated pattern doc for binary semantic gating (`verdict: pass|fail`, `reason: str`).
2. Clarify when semantic LLM gates are appropriate versus deterministic checks.
3. Keep scope to docs and directly coupled docs-tests.

## Constraints

1. No new framework runtime behavior, node types, or action types.
2. Pattern examples must align with current router contract and conditional edge wiring.
3. Keep single responsibility: semantic gate composition pattern documentation.

## Proposed Solution

### In scope

1. Create `reference/patterns/llm-as-gate.md` containing:
   - problem framing (shape/status checks vs semantic meaning checks),
   - router-based solution pattern,
   - graph snippet (`type: router`, `route_field: verdict`, `pass`/`fail` routes),
   - prompt schema snippet (`verdict` + `reason`),
   - guidance for semantic vs deterministic checks,
   - composition guidance (chaining, fail-branch fallback, retry semantics).
2. Add a link in `reference/README.md` to the new pattern doc.
3. Add acceptance tests for the docs contract.

### Out of scope

1. Introducing any `semantic_gate` node/action primitive.
2. Refactoring watcher runtime behavior.
3. Broad restructuring of existing reference docs.

## Acceptance Criteria

- [x] **AC-01:** `reference/patterns/llm-as-gate.md` exists.
- [x] **AC-02:** The doc states that deterministic/mechanical gates validate shape/status, not semantic meaning.
- [x] **AC-03:** The doc includes a YAML graph example with `type: router`, `route_field: verdict`, and `pass`/`fail` routes.
- [x] **AC-04:** The doc includes a prompt schema example with binary `verdict` (`pass|fail`) and `reason: str`.
- [x] **AC-05:** The doc explains when to prefer semantic LLM gates vs deterministic checks (`grep`, file existence, exit code).
- [x] **AC-06:** The doc covers composition guidance: chaining gates, fail-path fallback, retry behavior.
- [x] **AC-07:** The doc explicitly states no new framework node/action type is required.
- [x] **AC-08:** `reference/README.md` links to `reference/patterns/llm-as-gate.md`.
- [x] **AC-09:** Unit tests exist to enforce AC-01..AC-08.

## Failing Acceptance Tests (RED)

Planned RED test file:

- `tests/unit/test_fr327_llm_as_gate_pattern_docs.py`

RED command:

```bash
pytest tests/unit/test_fr327_llm_as_gate_pattern_docs.py -q --no-cov
```

Additional RED evidence (expected before implementation):

```bash
test -f reference/patterns/llm-as-gate.md
rg -n "llm-as-gate\\.md" reference/README.md
```

## Alternatives Considered

1. **Add a new `semantic_gate` primitive** — rejected; duplicates existing router+schema+edges behavior.
2. **Only add a short paragraph to `reference/patterns.md`** — rejected; weak discoverability for a reusable core pattern.
3. **Document only deterministic checks** — rejected; semantic and deterministic checks solve different risks and both need explicit guidance.

## Related

- GitHub issue #327: <https://github.com/sheikkinen/yamlgraph/issues/327>
- `reference/graph-yaml.md`
- `reference/patterns.md` (Pattern 2, Pattern 12)
- `examples/demos/router/graph.yaml`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml`
- Requested topic file: `.chaplain/processing/gh-327.md` (not present in this worktree)
