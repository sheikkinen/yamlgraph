# Feature Request: FR-086 Add "When NOT to Use YAMLGraph" Section to README

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-24

## Summary

Add an honest "When NOT to Use YAMLGraph" section to the README immediately after the "What is YAMLGraph?" section, setting clear expectations about the framework's trade-offs and boundaries.

## Problem

The README opens with "Build production AI pipelines in minutes, not days" but never explains limitations. This creates a trust gap: users who discover limitations mid-project feel misled. Honest boundary-setting attracts the right users and reduces frustration-driven churn.

The "What is YAMLGraph?" paragraph already hints at the trade-off ("trades some flexibility for dramatically faster prototyping") but doesn't enumerate specific scenarios where the trade fails.

## Proposed Solution

Add a new `## When NOT to Use YAMLGraph` section at README line 36, between "What is YAMLGraph?" and "## Installation".

```markdown
## When NOT to Use YAMLGraph

YAMLGraph trades flexibility for simplicity. Consider raw LangGraph or other tools when:

| Scenario | Why YAMLGraph isn't ideal |
|----------|--------------------------|
| **Dynamic graph topology** | Graph structure is compiled from YAML at load time; edges cannot be added or removed at runtime |
| **Complex state transformations** | YAML expressions support basic arithmetic and list operations; multi-step logic belongs in Python |
| **Custom node types per-invoke** | Node types are fixed at compile time (though model and provider can vary per-invoke) |
| **Native multi-modal pipelines** | Text is the only native modality; image/audio requires custom Python nodes via `type: python` |

**Rule of thumb:** If you're fighting the YAML to express your logic, use Python — either via `type: python` nodes within YAMLGraph, or raw LangGraph for full control.
```

### Content decisions

1. **Removed "Real-time streaming agents"** from the original proposal — YAMLGraph *does* support token-level streaming via `run_graph_streaming_native()` (FR-029). The original claim was inaccurate.
2. **Softened "struggles" to "isn't ideal"** — more precise; YAMLGraph has escape hatches (Python nodes, custom tools) for most limitations.
3. **Added the escape hatch** in the rule-of-thumb — `type: python` nodes let users stay in YAMLGraph while using Python for complex parts. This is more helpful than a flat "don't use YAMLGraph."
4. **Table format** — matches existing README patterns (Environment Variables, Documentation tables).

## Acceptance Criteria

- [x] New section exists in README.md between "What is YAMLGraph?" and "## Installation"
- [x] Section heading is `## When NOT to Use YAMLGraph`
- [x] Table lists exactly 4 scenarios (dynamic topology, complex state, custom node types, multi-modal)
- [x] No scenario is technically inaccurate (verified against current codebase capabilities)
- [x] "Rule of thumb" mentions both `type: python` escape hatch and raw LangGraph
- [x] Streaming is NOT listed as a limitation (token-level streaming exists via FR-029)
- [x] README lints cleanly (no broken markdown)
- [x] No changes to any non-documentation files

## Alternatives Considered

1. **Separate "Limitations" page in `reference/`** — Rejected. Limitations belong in the first document users read (README), not buried in reference docs.
2. **FAQ format instead of table** — Rejected. Table is scannable and matches existing README style.
3. **Include streaming as a limitation** — Rejected after research. `run_graph_streaming_native()` provides token-level streaming. The original inbox proposal was based on stale information.

## Related

- Original proposal: `.chaplain/inbox/readme-when-not-to-use.md`
- FR-029: Native LangGraph streaming (proves streaming claim was inaccurate)
- README.md line 35: "trades some flexibility for dramatically faster prototyping"
- `reference/streaming.md`: Token-level streaming documentation
