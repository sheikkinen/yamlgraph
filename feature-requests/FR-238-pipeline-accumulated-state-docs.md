# Feature Request: Pipeline Accumulated State — Reducer Config & Documentation

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1.5 days
**Requested:** 2026-04-19

## Summary

Enable user-configurable reducers in the YAML `state:` section and document the accumulated state pattern for pipelines in `reference/graph-yaml.md`.

## Value Statement

Graph authors building sequential pipelines where later items depend on earlier items' outputs get a documented, working mechanism for cross-item context sharing — without reading `state_builder.py` source code.

## Problem

Many real pipelines need cross-item context sharing. Example: a translation pipeline processes chapters sequentially, extracting domain-specific terms into a glossary. Later chapters consume the accumulated glossary to maintain terminology consistency.

The pipeline demo (`examples/demos/pipeline/`) shows per-item isolation: each item writes to its own `state_key` and items never read each other's outputs. This is sufficient for embarrassingly parallel workloads but inadequate for sequential accumulation.

### The mechanism is missing

The `add` reducer exists internally (used by `errors`, `messages`, and map `collect` fields via `BASE_FIELDS` in `state_builder.py` line 58), but **users cannot configure reducers in the YAML `state:` section**. `parse_state_config()` (line 105) only accepts simple type strings. Dict syntax like `{type: list, reducer: add}` triggers a warning at line 133 and defaults to `Any` with no reducer applied.

Without reducer support, writing to a shared `state_key` from multiple pipeline stages overwrites rather than accumulates — the second item's output silently replaces the first.

## Proposed Solution

Two changes, tightly coupled:

### 1. Extend `parse_state_config()` to support reducer configuration

Add dict-syntax support to the YAML `state:` section:

```yaml
state:
  concept: str                        # simple type (unchanged)
  glossary:
    type: list
    reducer: add                      # NEW: configurable reducer
```

**Implementation in `yamlgraph/models/state_builder.py`:**

1. Add a `REDUCER_MAP` dict mapping reducer name strings to functions:

```python
REDUCER_MAP: dict[str, Any] = {
    "add": add,
    "last_value": last_value,
    "sorted_add": sorted_add,
}
```

2. Extend `parse_state_config()` to handle dict entries:

```python
elif isinstance(type_spec, dict):
    type_str = type_spec.get("type", "any")
    reducer_name = type_spec.get("reducer")
    python_type = TYPE_MAP.get(type_str.lower(), Any)

    if reducer_name:
        reducer_fn = REDUCER_MAP.get(reducer_name)
        if reducer_fn is None:
            logger.warning(
                f"Unknown reducer '{reducer_name}' for state field "
                f"'{field_name}'. Supported: {', '.join(REDUCER_MAP)}."
            )
        else:
            python_type = Annotated[python_type, reducer_fn]

    fields[field_name] = python_type
```

3. The return type of `parse_state_config()` stays `dict[str, type]` since `Annotated[...]` is a valid type annotation.

### 2. Extend `generate_typeddict_code()` for dict-syntax state entries

`generate_typeddict_code()` (line 300) iterates state config but only handles `isinstance(type_spec, str)` at line 338. Dict-syntax entries would be silently omitted from generated TypedDict code (`yamlgraph codegen` command).

**Implementation:** Extract the type string from dict entries and map via `CODEGEN_TYPE_MAP`:

```python
elif isinstance(type_spec, dict):
    type_str = type_spec.get("type", "any")
    python_type = CODEGEN_TYPE_MAP.get(type_str.lower(), "Any")
    fields[field_name] = python_type
```

This is ~5 lines in the same file, same concern ("enable dict-syntax state definitions"), and prevents silent regression in `yamlgraph codegen`.

### 3. Document accumulated state in pipeline reference docs

Add an "Accumulated State" subsection to the `type: pipeline` section (created by FR-237) in `reference/graph-yaml.md`.

**Content:**

**a) The pattern** — show how a shared state key with the `add` reducer enables cross-item context:

```yaml
state:
  glossary:
    type: list
    reducer: add

nodes:
  chapters:
    type: pipeline
    items:
      - name: ch1
        title: "The Beginning"
      - name: ch2
        title: "The Journey"
      - name: ch3
        title: "The Return"
    stages:
      - name: translate
        type: llm
        prompt: translate_chapter
        variables:
          title: "{item.title}"
          glossary: "{state.glossary}"
        state_key: translated_{item.name}
      - name: extract_terms
        type: llm
        prompt: extract_terms
        variables:
          translation: "{state.translated_{item.name}}"
        state_key: glossary
        skip_if_exists: false
```

**b) Why `{prev_item}` syntax is unnecessary** — the `add` reducer on a shared state key solves cross-item reads without new interpolation syntax. Each stage reads `{state.glossary}`.

**c) Sequential execution constraint** — accumulated state works because pipeline items execute sequentially (ch1 → ch2 → ch3). If pipelines ever support parallel item execution, cross-item dependencies become impossible. Sequential chaining is what makes accumulation work. This is a feature, not a limitation.

**d) The `skip_if_exists: false` requirement** — reference W021: list-typed state keys with the `add` reducer are truthy after the first append. The default `skip_if_exists: true` on LLM nodes causes stages 2+ to skip. Document that accumulated state keys require explicit `skip_if_exists: false`.

## Acceptance Criteria

- [ ] `parse_state_config()` handles dict-syntax state definitions: `{type: str, reducer: str}`
- [ ] `REDUCER_MAP` maps `"add"`, `"last_value"`, and `"sorted_add"` to their functions
- [ ] Unknown reducer names log a warning (same pattern as unknown types)
- [ ] Simple string syntax remains unchanged (no regression)
- [ ] Dict syntax without `reducer` key works as type-only (equivalent to simple string)
- [ ] `generate_typeddict_code()` handles dict-syntax entries (extracts type string, maps via `CODEGEN_TYPE_MAP`)
- [ ] `reference/graph-yaml.md` pipeline section includes an "Accumulated State" subsection
- [ ] Subsection contains the glossary accumulation YAML example
- [ ] Subsection explains why `{prev_item}` syntax is unnecessary
- [ ] Subsection documents the sequential execution constraint
- [ ] Subsection references W021 and the `skip_if_exists: false` requirement
- [ ] Unit tests for `parse_state_config()` dict-syntax with each supported reducer
- [ ] Unit test verifying unknown reducer logs a warning
- [ ] Unit test for `generate_typeddict_code()` with dict-syntax state entries
- [ ] The YAML example in the docs passes `yamlgraph graph lint` (prompt files may be stubs)
- [ ] Diary reflection added

## Design Decisions

### Use `list` not `list[str]` in examples

`TYPE_MAP` (line 91) supports `list` but not parameterized types like `list[str]`. Extending TYPE_MAP for parameterized generics is a separate concern (and may not be needed — LangGraph state fields are typed at the Python level, not the YAML level). The examples use `list` throughout.

### W021 already handles dict-syntax state definitions

The W021 lint check (`check_skip_if_exists_add_reducer` in `checks_contracts.py`, lines 137-139) already inspects dict-syntax state defs:

```python
isinstance(field_type, dict)
and field_type.get("type", "").startswith("list")
```

No changes needed to W021. It will fire correctly for the documented pattern once dict-syntax state definitions are used.

### Three built-in reducers, no custom functions

Only the three existing reducers (`add`, `last_value`, `sorted_add`) are exposed. Arbitrary Python callables would require `eval()` or import resolution — security and complexity concerns that belong in a separate FR if ever needed.

### `generate_typeddict_code()` handles dict-syntax (Judgement amendment)

The Judgement identified that `generate_typeddict_code()` (line 300) silently skips dict-syntax entries. Since this is a second consumer of the same state config format in the same file, handling it here prevents a silent regression in `yamlgraph codegen`. ~5 lines of code, same concern.

## Alternatives Considered

1. **Documentation only (no code change)** — Rejected. The mechanism does not exist in `parse_state_config()`. Documenting a non-functional pattern violates Commandment 2 ("Code that has not been tested must not be trusted").

2. **Add `{prev_item}` interpolation syntax** — Rejected. Adds compile-time complexity for a pattern already solved by shared state keys with `add` reducer. Speculative complexity.

3. **Split into two FRs (reducer impl + docs)** — Considered but rejected. The documentation cannot exist without the mechanism, and the mechanism has no value without documentation. Single-responsibility here is "enable accumulated state for pipelines."

4. **Add a pipeline-specific `accumulate` keyword** — Rejected. The existing `state_key` + `reducer` mechanism is general-purpose and works for all node types, not just pipelines. A pipeline-specific keyword would duplicate existing semantics.

5. **Support parameterized types (`list[str]`, `dict[str, int]`)** — Deferred. Not needed for the accumulated state pattern. Would require parsing generic type syntax, which is a separate concern.

6. **Defer `generate_typeddict_code()` to separate FR** — Rejected per Judgement. Same file, same concern, ~5 lines. Deferring would leave a silent regression in `yamlgraph codegen`.

## Dependencies

- **FR-237** (Document Race and Pipeline Node Types): Creates the pipeline section in `reference/graph-yaml.md` that this FR extends. Must be completed first.

## Related

- FR-235: Compile-Time Pipeline Templates (pipeline implementation)
- FR-237: Document Race and Pipeline Node Types (pipeline docs — this FR extends that section)
- FR-057: Agent Node Messages Quadratic Growth (precedent for `add` reducer pitfalls)
- W021 lint check: `skip_if_exists` on list fields with `add` reducer (`yamlgraph/linter/checks_contracts.py`)
- `yamlgraph/models/state_builder.py`: State builder with `add`, `last_value`, `sorted_add` reducers
- `examples/demos/pipeline/graph.yaml`: Existing demo showing per-item isolation
