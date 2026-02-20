# Feature Request: Contract Violation Lint Rules

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-02-20
**FR:** FR-061

## Summary

Add lint rules to detect common YAML-to-runtime contract violations — configurations that parse successfully but fail or behave incorrectly at runtime.

## Problem

Multiple bugs (FR-053, FR-057, FR-049a) shared a pattern:
- Config parses without error ✓
- Graph compiles without error ✓
- First execution crashes or silently misbehaves ✗

The gap between "valid YAML" and "correct graph" is where implicit contract violations hide. These bugs take 10+ minutes to debug because the error manifests far from the misconfiguration.

### Real Examples

1. **FR-053**: `variables:` on `type: python` node was silently ignored
2. **FR-049a**: `state.field` prefix in `loop_until` evaluated to `None` (prefix not stripped)
3. **Hyphen vs underscore**: `item-var` valid as YAML key, invalid as Python identifier

## Proposed Solution

Add three zero-false-positive lint rules to `yamlgraph/linter/checks.py`:

### L001: Variables on Python Nodes

```python
def check_python_node_variables(graph: dict) -> list[LintIssue]:
    """L001: variables: on type: python is a silent no-op."""
    issues = []
    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("type") == "python" and "variables" in node_config:
            issues.append(LintIssue(
                severity="warning",
                code="W010",
                message=f"Node '{node_name}': 'variables' is ignored on type: python. "
                        "Python tools receive state dict directly via state parameter.",
                fix="Remove 'variables' key or use type: llm if variable substitution needed",
            ))
    return issues
```

### L002: Hyphen Keys as Identifiers

```python
def check_identifier_keys(graph: dict) -> list[LintIssue]:
    """L002: Keys used as Python identifiers must not contain hyphens."""
    issues = []

    # Check state keys
    for key in graph.get("state", {}).keys():
        if "-" in key:
            issues.append(LintIssue(
                severity="error",
                code="E010",
                message=f"State key '{key}' contains hyphen — invalid as Python identifier",
                fix=f"Rename to '{key.replace('-', '_')}'",
            ))

    # Check node state_key values
    for node_name, node_config in graph.get("nodes", {}).items():
        state_key = node_config.get("state_key", "")
        if "-" in state_key:
            issues.append(LintIssue(
                severity="error",
                code="E010",
                message=f"Node '{node_name}' state_key '{state_key}' contains hyphen",
                fix=f"Rename to '{state_key.replace('-', '_')}'",
            ))

    # Check tool names (used as function names)
    for tool_name in graph.get("tools", {}).keys():
        if "-" in tool_name:
            issues.append(LintIssue(
                severity="error",
                code="E010",
                message=f"Tool name '{tool_name}' contains hyphen — invalid as function name",
                fix=f"Rename to '{tool_name.replace('-', '_')}'",
            ))

    return issues
```

### L003: Skip-If-Exists on Add-Reducer Fields

```python
def check_skip_if_exists_add_reducer(graph: dict) -> list[LintIssue]:
    """L003: skip_if_exists on list fields with add reducer is likely wrong."""
    issues = []
    state_def = graph.get("state", {})

    for node_name, node_config in graph.get("nodes", {}).items():
        if not node_config.get("skip_if_exists"):
            continue

        state_key = node_config.get("state_key")
        if not state_key:
            continue

        field_type = state_def.get(state_key, "")
        is_list = (
            isinstance(field_type, str) and field_type.startswith("list") or
            isinstance(field_type, dict) and field_type.get("type", "").startswith("list")
        )

        if is_list:
            issues.append(LintIssue(
                severity="warning",
                code="W011",
                message=f"Node '{node_name}': skip_if_exists on list field '{state_key}' "
                        "— list is truthy after first element, so skip triggers after turn 1",
                fix="Remove skip_if_exists or use a boolean control field instead",
            ))

    return issues
```

## Acceptance Criteria

- [ ] W010 (python node variables) implemented and wired into `run_all_checks()`
- [ ] E010 (hyphen identifiers) implemented with state, state_key, and tool name checks
- [ ] W011 (skip_if_exists + list) implemented
- [ ] All three rules have unit tests with positive and negative cases
- [ ] `yamlgraph graph lint` reports new issues on affected graphs
- [ ] Existing graphs in `graphs/` and `examples/` pass lint (no regressions)

## Implementation Notes

### Code Location

Add to `yamlgraph/linter/checks.py` — these are pure config checks, not semantic analysis.

### Wiring

Add to `run_all_checks()` in `graph_linter.py`:
```python
issues.extend(check_python_node_variables(graph))
issues.extend(check_identifier_keys(graph))
issues.extend(check_skip_if_exists_add_reducer(graph))
```

### Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| E010 | error | Hyphen in identifier position (state key, tool name, state_key value) |
| W010 | warning | variables: on type: python (silent no-op) |
| W011 | warning | skip_if_exists on list field with add reducer |

## Testing

```python
@pytest.mark.req("REQ-YG-025")
class TestContractViolationChecks:
    def test_w010_python_node_variables(self):
        """variables: on type: python should warn."""
        graph = {
            "nodes": {
                "process": {
                    "type": "python",
                    "tool": "my_tool",
                    "variables": {"topic": "{state.topic}"}  # Silent no-op!
                }
            }
        }
        issues = check_python_node_variables(graph)
        assert len(issues) == 1
        assert issues[0].code == "W010"

    def test_e010_hyphen_state_key(self):
        """Hyphen in state key should error."""
        graph = {"state": {"user-name": "str"}}
        issues = check_identifier_keys(graph)
        assert len(issues) == 1
        assert issues[0].code == "E010"
        assert "user_name" in issues[0].fix

    def test_w011_skip_if_exists_list(self):
        """skip_if_exists on list field should warn."""
        graph = {
            "state": {"messages": "list"},
            "nodes": {
                "chat": {
                    "type": "agent",
                    "state_key": "messages",
                    "skip_if_exists": True
                }
            }
        }
        issues = check_skip_if_exists_add_reducer(graph)
        assert len(issues) == 1
        assert issues[0].code == "W011"
```

## Alternatives Considered

### Runtime Validation Only

Could validate at compile time instead of lint time. Rejected because:
- Lint errors show in IDE before running
- `yamlgraph graph lint` can run in CI without API keys
- Earlier feedback is always better

### Strict Mode Flag

Could make warnings into errors with `--strict-contracts`. Deferred — let's see if the warning severity is sufficient first.

## Related

- FR-053: Tavily demo revealed `variables:` no-op bug
- FR-049a: `state.` prefix bug in `loop_until` expressions
- FR-057: Agent message accumulation (related but needs code analysis — deferred)
- Diary 2026-02-20: "Linter rules for common YAML-to-runtime contract violations"
- REQ-YG-025: Graph linting capability
