# Authoring brief: deviant-daily — remove dry_run and force from the graph

**Prior art:** `fr-862-deviant-daily-dispatch-brief.md` added these exact
fields; this brief removes them under FR-863 S-5. Same artifact,
opposite direction — supersession, not duplication.

Operator ruling 2026-08-23: the `dry_run` and `force` flags were
paternalistic ceremony. If the pipeline runs, it publishes. The Python
step functions in the target repo have already had both parameters
removed and their tests updated; the graph must stop passing them.

## Target

Modify the existing graph in the sibling repo
`/Users/sheikki/Documents/src/deviant-daily/graph.yaml`. That repo is a
separate git repository — author in place, do not copy it into this
workspace, do not commit anything there.

Artifact to modify: `/Users/sheikki/Documents/src/deviant-daily/graph.yaml`
No prompt artifacts change.

## Task

Remove from the `state:` block:

- `dry_run: str`
- `force: str`

Keep `date: str` and `model: str`.

Remove these arguments from the `tool_call` node args, leaving every
other argument untouched:

- `draw`: remove `force` and `dry_run` (keep `date`)
- `gate`: remove `dry_run` (keep `slot` and the rest)
- `publish`: remove `dry_run` (keep `slot` and the rest)

The `generate` node keeps `model`. Do not change node types, tool names,
`state_key` values, `on_error` settings, or any edge or condition.

## Validation

Run from this workspace:

```bash
yamlgraph graph lint /Users/sheikki/Documents/src/deviant-daily/graph.yaml
```

The graph publishes to a public DeviantArt gallery through its tools, so
a live full-pipeline smoke would create a real post. Do not run the
graph. Record the lint result and note the smoke as deliberately
withheld; the operator triggers the live run separately.
