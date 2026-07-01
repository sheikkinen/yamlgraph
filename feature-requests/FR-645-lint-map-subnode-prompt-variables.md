# Feature Request: Lint map sub-node prompt variables against parent state

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-07-02

## Summary

Extend the E002 prompt variable check to recursively validate map (and pipeline) sub-node prompts against the correct variable scope: parent state keys + `as` variable + explicit `variables:` config.

## Value Statement

Graph authors get lint-time errors when a map sub-node prompt references variables not available in its execution scope, preventing the most common map node runtime failure.

## Problem

The linter's `check_state_declarations()` (E002) validates prompt variables against the graph's `state:` section and the node's `variables:` config. But it only checks top-level nodes. Map nodes contain nested sub-nodes whose prompts execute with an augmented scope:

```
sub-node scope = parent_state + {as_variable: item} + node.variables
```

Currently, a map sub-node prompt referencing `{{ canon_pages }}` (a state key) without declaring it in `variables:` passes lint but crashes at runtime:

```
ValueError: Missing required variable(s) for prompt 'deepen_entity': canon_count, canon_pages, synopsis_text
```

The fix was adding explicit `variables:` mappings to the sub-node config:
```yaml
variables:
  canon_pages: "{state.canon_pages}"
  canon_count: "{state.canon_count}"
  synopsis_text: "{state.synopsis_text}"
```

This is non-obvious — the sub-node receives the full parent state via `Send({**state, ...})`, but the prompt variable validator checks `variables:` config, not state presence.

**Provenance:** FR-643v2 worldgen pipeline. The deepen and create_skeletons map nodes both had prompts referencing state keys without explicit variable bindings. Lint passed, runtime crashed on all 4 parallel branches.

## Proposed Solution

Extend E002 to recurse into map sub-nodes. Two approaches:

### Approach A: Warn on unbound state references in map sub-nodes (recommended)

Add a new warning **W027** in `checks_prompts.py`:

1. For each `type: map` node, extract the nested `node:` config
2. Extract the nested node's `prompt:` and load the prompt file
3. Extract prompt variables via `extract_variables()`
4. Compute available scope: `{as_var} ∪ node.variables.keys()`
5. For variables NOT in the available scope but present in `state:` keys: emit **W027** suggesting an explicit `variables:` binding
6. For variables NOT in scope and NOT in state: emit **E002** (truly missing)

```python
def check_map_subnode_variables(graph_path: Path) -> list[LintIssue]:
    """W027/E002: Validate map sub-node prompt variables against scope."""
    issues = []
    graph = load_graph(graph_path)
    state_keys = set(graph.get("state", {}).keys())
    prompts_dir = resolve_prompts_dir(graph, graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("type") != "map":
            continue
        as_var = node_config.get("as", "")
        sub = node_config.get("node", {})
        prompt_name = sub.get("prompt")
        if not prompt_name:
            continue

        prompt_path = get_prompt_path(prompt_name, prompts_dir)
        if not prompt_path:
            continue

        prompt_text = prompt_path.read_text()
        required_vars = extract_variables(prompt_text)

        # Scope: as_var + explicit variables + jinja builtins
        available = {as_var} | set(sub.get("variables", {}).keys())
        available |= {"state", "loop", "range", "true", "false", "none"}

        missing = required_vars - available
        for var in sorted(missing):
            if var in state_keys:
                issues.append(LintIssue(
                    "W027",
                    f"Map sub-node prompt '{prompt_name}' uses '{{{{ {var} }}}}' "
                    f"which is in state but not in node variables. "
                    f"Add: variables: {{ {var}: \"{{{{state.{var}}}}}\" }}",
                    node_name, "warning"
                ))
            else:
                issues.append(LintIssue(
                    "E002",
                    f"Map sub-node prompt '{prompt_name}' references "
                    f"undeclared variable '{var}'",
                    node_name, "error"
                ))
    return issues
```

### Approach B: Auto-inject state variables into map sub-nodes

Make the map compiler auto-inject all parent state keys as variables. This is riskier (may mask legitimate missing-variable errors) and changes runtime behavior.

**Recommendation:** Approach A — explicit is better than implicit. The lint warning teaches authors the correct pattern.

## Acceptance Criteria

- [ ] AC-1: Map sub-node prompt referencing `{{ canon_pages }}` without explicit `variables:` binding emits W027
- [ ] AC-2: W027 message includes the fix: `Add: variables: { canon_pages: "{state.canon_pages}" }`
- [ ] AC-3: Map sub-node prompt referencing a variable not in state or variables emits E002
- [ ] AC-4: Map sub-node prompt referencing only `{{ entity_task }}` (the `as` var) passes cleanly
- [ ] AC-5: Existing graphs lint clean (no false positives) — verify with `yamlgraph graph lint examples/**/*.yaml`
- [ ] AC-6: Tests added with `@pytest.mark.req`
- [ ] AC-7: Pipeline sub-nodes (if any) also checked

## Alternatives Considered

- **Auto-inject all state into map sub-node variables**: Eliminates the need for explicit bindings but loses explicitness. If the prompt has a typo (`cannon_pages`), the error would surface at runtime, not lint time.
- **Treat map sub-nodes as top-level for E002**: Would produce false positives — many state keys are irrelevant to the sub-node, and the `as` variable wouldn't be recognized.
- **Do nothing, document the pattern**: The fix is a 3-line YAML addition, but the failure mode is non-obvious and crashes all parallel branches simultaneously.

## Related

- `yamlgraph/linter/checks.py` — `check_state_declarations()` (E002)
- `yamlgraph/linter/patterns/map.py` — existing map node structural checks
- `yamlgraph/map_compiler.py` — `compile_map_node()` runtime behavior
- `yamlgraph/utils/template.py` — `extract_variables()` and `validate_variables()`
- FR-643v2 — provenance (worldgen deepen + create_skeletons crash)
- FR-644 — sibling FR for schema type validation
