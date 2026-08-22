# Task: Fix stale variable bindings in research-agent demo graph

## Problem

`examples/demos/research-agent/graph.yaml` binds node variables with bare
placeholders that `resolve_template` (yamlgraph/utils/expressions.py) does
not resolve — only `{state.path}` templates resolve; bare `{query}` falls
through as a literal string. The model receives `Research question: {query}`
and hallucinates a topic (verified 2026-08-06 with an XYZZY marker query:
the marker never appeared in the extracted intent; the first run invented
an OAuth2 research topic wholesale).

The documented contract (reference/graph-yaml.md, e.g. `topic:
"{state.topic}"`) uses `{state.X}` throughout. CLI `--var query=...` lands
in `state.query`.

## Change (single file: examples/demos/research-agent/graph.yaml)

Replace the bare-placeholder bindings with state paths:

- `extract_intent.variables.query`: `"{query}"` → `"{state.query}"`
- `plan_research.variables.scope`: `"{scope}"` → `"{state.scope}"`
- `execute_research.variables.scope`: `"{scope}"` → `"{state.scope}"`
- `synthesize_report.variables.query`: `"{query}"` → `"{state.query}"`

The `{state.intent}` / `{state.plan}` / `{state.findings}` /
`{state.validation}` bindings are already correct — do not touch them.
No prompt, node, edge, or tool changes.

## Validation

- `yamlgraph graph lint examples/demos/research-agent/graph.yaml`
- `yamlgraph graph validate examples/demos/research-agent/graph.yaml`

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
