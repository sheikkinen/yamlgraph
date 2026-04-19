# Feature Request: Document Race and Pipeline Node Types

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-19

## Summary

Add reference documentation for `type: race` (FR-232) and `type: pipeline` (FR-235) node types to `reference/graph-yaml.md` and update the node type table in `reference/getting-started.md`.

## Value Statement

Graph authors discovering node types through the reference docs can find and use `race` and `pipeline` without reverse-engineering demos or capability files.

## Problem

Both `type: race` (FR-232, CAP-91) and `type: pipeline` (FR-235, CAP-94) shipped with full implementations, demos, tests, diary reflections, and capability files — but neither appears in the two canonical reference documents:

1. **`reference/getting-started.md`** — The Node Types table (line ~84) lists 12 types. `race` and `pipeline` are absent.
2. **`reference/graph-yaml.md`** — Contains no dedicated section for either node type. The Parallel Fan-Out Edge section (line ~895) is the closest neighbor but covers a different concept (FR-234).

A user reading the reference docs has no way to discover these node types exist.

## Proposed Solution

### 1. Update node type table in `reference/getting-started.md`

Add two rows after the existing table entries:

| Type | Purpose |
|------|---------|
| `race` | Race multiple providers, return fastest |
| `pipeline` | Compile-time items × stages expansion |

### 2. Add `type: race` section to `reference/graph-yaml.md`

Insert a new section in the Node Types area covering:

- **Purpose**: Fire the same prompt to multiple LLM provider/model candidates concurrently; return the fastest successful response.
- **Configuration keys**: `candidates` (list of `{provider, model}` pairs, minimum 2), `timeout` (per-candidate, default 30s), `prompt`, `state_key`, `temperature`.
- **State output**: `state_key` receives the winning response; `_race_winner` is set to a string identifying which candidate won.
- **Error handling**: When all candidates fail, the node's `on_error` policy applies.
- **Example**: Reference or inline from `examples/demos/race/graph.yaml`.

```yaml
nodes:
  fastest_answer:
    type: race
    prompt: answer
    state_key: answer
    timeout: 15
    candidates:
      - provider: mistral
        model: mistral-small-latest
      - provider: openai
        model: gpt-4o-mini
      - provider: google
        model: gemini-2.0-flash
```

### 3. Add `type: pipeline` section to `reference/graph-yaml.md`

Insert a new section covering:

- **Purpose**: Compile-time expansion of `items × stages` into concrete nodes. This is a meta-node — it does not exist at runtime, only its expanded concrete nodes do.
- **Configuration keys**: `items` (list of dicts, each must have `name` plus arbitrary fields), `stages` (list of node configs supporting `{item.field}` and `{state.field}` interpolation).
- **Expansion semantics**: `N items × M stages = N×M` concrete nodes, chained sequentially per item. External edges (START→pipeline, pipeline→END) are rewritten to the first/last expanded node.
- **Interpolation**: `{item.field}` in `prompt`, `variables`, `state_key`; non-string fields copied verbatim.
- **Example**: Reference or inline from `examples/demos/pipeline/graph.yaml`.

```yaml
nodes:
  topics:
    type: pipeline
    items:
      - name: sun
        subject: "the Sun"
      - name: moon
        subject: "the Moon"
    stages:
      - name: draft
        type: llm
        prompt: draft
        variables:
          subject: "{item.subject}"
        state_key: draft_{item.name}
      - name: polish
        type: llm
        prompt: polish
        variables:
          draft: "{state.draft_{item.name}}"
        state_key: polished_{item.name}
```

## Acceptance Criteria

- [x] `reference/getting-started.md` node type table includes `race` and `pipeline` rows
- [x] `reference/graph-yaml.md` has a dedicated `type: race` section with purpose, config keys, state output, error handling, and example
- [x] `reference/graph-yaml.md` has a dedicated `type: pipeline` section with purpose, config keys, expansion semantics, interpolation, and example
- [x] Examples in the docs match the actual demo graph YAMLs (`examples/demos/race/graph.yaml`, `examples/demos/pipeline/graph.yaml`)
- [x] No code changes — documentation only
- [x] `yamlgraph graph lint` passes on any example YAML referenced in the new docs

## Alternatives Considered

1. **Add to README instead of reference docs** — Rejected. The README is an overview; detailed node type documentation belongs in the reference.
2. **Auto-generate docs from capability files** — Over-engineering for two sections. Manual docs are clearer and match the existing pattern.
3. **Link to demos instead of documenting** — Demos show usage but don't explain semantics (timeout behavior, expansion rules, error handling). Reference docs need both.

## Related

- FR-232: Race Node Type (implementation)
- FR-235: Compile-Time Pipeline Templates (implementation)
- FR-234: Parallel Fan-Out Edges (neighboring concept, already documented)
- CAP-91: Race Node Type capability
- CAP-94: Pipeline Templates capability
- REQ-YG-233: Race node requirement
- REQ-YG-236: Pipeline node requirement
