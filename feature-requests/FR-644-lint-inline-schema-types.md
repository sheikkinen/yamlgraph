# Feature Request: Lint inline schema field types

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-02

## Summary

Add a linter check that validates inline schema field `type:` values against `schema_loader.resolve_type()` supported types at lint time, catching unsupported types like `list[NewEntity]` before runtime.

## Value Statement

Graph authors get immediate lint-time feedback on unsupported schema types, preventing a `ValueError` crash at graph compilation that currently passes `yamlgraph graph lint` silently.

## Problem

The inline schema system supports only basic types: `str`, `int`, `float`, `bool`, `dict`, `Any`, `list[T]`, `dict[K,V]` where T/K/V are basic types. Custom nested types like `list[NewEntity]` are not supported by `schema_loader.resolve_type()`.

Currently this fails only at runtime during `graph.compile()` with:
```
ValueError: Unknown type: 'NewEntity' for field 'new_entities'. Supported types: str, int, float, bool, dict, Any, list[T], dict[K, V]
```

The linter (`yamlgraph graph lint`) reports zero errors for this graph.

**Provenance:** FR-643v2 worldgen pipeline used `list[NewEntity]` with a `nested:` block in `deepen_entity.yaml`. Lint passed, compilation crashed.

## Proposed Solution

Add error code **E008** in `checks_prompts.py`:

1. For each node with a prompt, load the prompt YAML
2. If `schema.fields` exists, iterate fields
3. For each field with a `type:` value, call `resolve_type(type_str, field_name)` inside a try/except
4. On `ValueError`, emit `E008: Unsupported schema type '{type_str}' for field '{field_name}' — supported: str, int, float, bool, dict, Any, list[T], dict[K,V]`

```python
# In checks_prompts.py
def check_schema_field_types(graph_path: Path) -> list[LintIssue]:
    """E008: Validate inline schema field types against resolve_type()."""
    issues = []
    graph = load_graph(graph_path)
    prompts_dir = resolve_prompts_dir(graph, graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        prompt_name = node_config.get("prompt")
        # Also check nested map/pipeline sub-nodes
        if node_config.get("type") == "map":
            sub = node_config.get("node", {})
            prompt_name = sub.get("prompt")
        if not prompt_name:
            continue
        prompt_path = get_prompt_path(prompt_name, prompts_dir)
        if not prompt_path:
            continue
        prompt = yaml.safe_load(open(prompt_path))
        schema = prompt.get("schema", {})
        for field_name, field_def in schema.get("fields", {}).items():
            type_str = field_def.get("type", "")
            try:
                resolve_type(type_str, field_name)
            except ValueError:
                issues.append(LintIssue(
                    "E008", f"Unsupported schema type '{type_str}' for field "
                    f"'{field_name}' in prompt '{prompt_name}'",
                    node_name, "error"
                ))
    return issues
```

## Acceptance Criteria

- [ ] AC-1: `list[NewEntity]` in a prompt schema triggers E008 at lint time
- [ ] AC-2: Valid types (`str`, `list[str]`, `dict[str, Any]`) pass without error
- [ ] AC-3: Error message names the field and prompt
- [ ] AC-4: Map node sub-node prompts are also checked
- [ ] AC-5: Tests added with `@pytest.mark.req`
- [ ] AC-6: Existing graphs lint clean (no false positives)

## Alternatives Considered

- **Support nested types**: Adding `nested:` support to `schema_loader.py` would eliminate the need for this check but is a larger change. The linter check is valuable regardless since authors may typo type names.
- **Runtime-only validation**: Current state. Fails too late — after lint passes, during compilation.

## Related

- `yamlgraph/schema_loader.py` — `resolve_type()` and `TYPE_MAP`
- `yamlgraph/linter/checks_prompts.py` — existing prompt checks
- FR-643v2 — provenance (worldgen `deepen_entity.yaml` crash)
