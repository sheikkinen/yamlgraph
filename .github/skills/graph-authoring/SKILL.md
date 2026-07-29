---
name: graph-authoring
description: "End-to-end workflow for creating a complete YAMLGraph artifact from a natural-language task. Use when: asked to create a new graph, example, or demo; turning a task description into graph + prompt files; drafting a pipeline that needs local validation before delivery; deciding whether graph work belongs in Chaplain instead. Not a syntax reference — composes author-graph and author-prompt."
argument-hint: "task description, or target directory like examples/demos/<name>/"
---

# Graph Authoring Workflow (discovery wrapper)

The canonical workflow contract lives in the adjacent `doctrine.md` —
that file is the single source of graph-authoring doctrine. This wrapper
tells you where things are and how the skill composes.

## To author a graph

Read `.github/skills/graph-authoring/doctrine.md` and follow its
workflow: research precedent → name the artifact boundary → choose the
smallest pattern → author → validate locally → repair → report the
verified artifact. Honor its input closure: task request + committed
repo artifacts + explicit user-provided files only.

## Composition — do not duplicate syntax references

- `author-graph` — graph YAML syntax: nodes, edges, routing, state keys,
  tools, loop limits, error handling. Consult it; do not restate it here.
- `author-prompt` — prompt YAML syntax: templates, inline schemas,
  Jinja2, system segments. Consult it; do not restate it here.
- `graph-authoring` (this skill) — the process contract around both:
  what to do first, what artifact to produce, how to prove it works.

## What this skill is NOT

- **Not the one-shot generator.** The stale `examples/yamlgraph_gen`
  one-shot generation model is rejected as the default path for repeated
  graph authoring: it collapses pattern selection, assembly, prompt
  generation, validation, and reporting into a single synthesis bet, and
  its ignored `outputs/*` directories caused the
  `workspace_is_not_boundary` phantom-root incident (FR-763).
- **Not FR judgement or PR review.** Substantial work is delegated via
  an artifact-closed delegation brief (see doctrine), which must not
  invoke `judge-fr`, `review-pr`, their adapters, or any judgement/review
  graph, and must not use verdict vocabulary.

## Quick validation loop

```bash
yamlgraph graph lint path/to/graph.yaml
yamlgraph graph run path/to/graph.yaml --var key=value --full   # narrowest smoke
```

If credentials or dependencies block the smoke run, record the exact
blocked command and the reason — never claim success for an unexecuted
validation.
