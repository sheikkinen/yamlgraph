# Enforcer - TDD Implementation + Demo Pipeline

**FR-105 Demo** | Copilot Session Continuation

This example demonstrates the session continuation feature from FR-105.
Two sequential copilot nodes share the same CLI session:

1. **Enforce**: TDD implementation of a feature request
2. **Demo**: Create working example using the same session context

## Why Session Continuation?

Without session continuation, the `demo` node would start fresh with no knowledge of what was implemented. With `resume: "{state.enforce_result.session_id}"`, the demo phase has full context:

- Which files were created/modified
- What tests were written
- The implementation approach taken
- Any decisions made during enforcement

## Usage

```bash
# Run the enforcer pipeline for a feature request
yamlgraph graph run examples/enforcer/graph.yaml \
  --var fr_path="feature-requests/105-copilot-session-continuations.md" \
  --var examples_dir="examples/demos/fr105-demo" \
  --full
```

## Graph Structure

```
START → enforce → demo → END
           │         │
           │         └─ resumes enforce's session
           │
           └─ TDD: test → implement → refactor
```

## State Flow

| Node | Input | Output |
|------|-------|--------|
| `enforce` | `fr_path` | `enforce_result.session_id`, `enforce_result.output` |
| `demo` | `examples_dir`, `enforce_result.session_id` | `demo_result.output` |

## Related

- [FR-105](../../feature-requests/105-copilot-session-continuations.md) - Session continuation spec
- [copilot example](../copilot/) - Original Plan→Judge workflow
- [reference/graph-yaml.md](../../reference/graph-yaml.md#type-copilot---copilot-cli-delegation) - Copilot node docs
