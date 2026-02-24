# Feature Request: Add Missing Node Types to reference/README.md Index

**Priority:** LOW
**Type:** Bug
**Status:** Implemented
**Effort:** 10 minutes
**Requested:** 2026-02-24

## Summary

The Node Types table in `reference/README.md` is missing entries for `copilot` and `interactive_tool` node types, which are documented in `graph-yaml.md` and implemented in the codebase.

## Value Statement

Documentation readers get a complete node type index, preventing them from missing capabilities that already exist.

## Problem

Two node types are absent from the `reference/README.md` Node Types index table:

| Missing Type | Introduced By | Section in graph-yaml.md |
|---|---|---|
| `copilot` | FR-081 | `### type: copilot - Copilot CLI Delegation` (line 422) |
| `interactive_tool` | FR-075 | `### type: interactive_tool - Multi-Turn Conversation Loop` (line 662) |

Additionally, `reference/getting-started.md` lists `interactive_tool` (line 97) but is also missing `copilot`.

The inbox note claimed `getting-started.md` lists both — verified that only `interactive_tool` is present there.

## Proposed Solution

Add the two missing rows to the Node Types table in `reference/README.md` (after the `subgraph` row):

```markdown
| `copilot` | [§ Copilot nodes](graph-yaml.md#type-copilot---copilot-cli-delegation) | - |
| `interactive_tool` | [§ Interactive tool](graph-yaml.md#type-interactive_tool---multi-turn-conversation-loop) | - |
```

Add the missing `copilot` row to the node type table in `reference/getting-started.md` (after `interactive_tool`):

```markdown
| `copilot` | Delegate task to Copilot CLI |
```

## Acceptance Criteria

- [x] `reference/README.md` Node Types table contains entries for all 12 node types: `llm`, `router`, `agent`, `tool`, `python`, `map`, `interrupt`, `passthrough`, `tool_call`, `subgraph`, `copilot`, `interactive_tool`
- [x] `reference/getting-started.md` node type table contains `copilot`
- [x] Links in README.md entries resolve to correct anchors in `graph-yaml.md`
- [x] `yamlgraph graph lint` still passes on all example graphs (no regression)

## Alternatives Considered

- **Fix only README.md**: Would leave `getting-started.md` incomplete for `copilot`. Both should be fixed together since the effort is trivial.

## Related

- FR-081: Introduced `copilot` node type
- FR-075: Introduced `interactive_tool` node type (FR-049 for original design)
- `reference/graph-yaml.md`: Canonical node type documentation
- `reference/getting-started.md`: AI assistant quick reference
