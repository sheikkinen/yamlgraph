# Skills Export

Export YAMLGraph graphs as portable filesystem skill bundles.

## Command

```bash
yamlgraph skill export <graph_path_or_dir> --format {skill-md,copilot,cursor,agent-md} [--output-dir PATH]
```

## Bundle Contents

Each exported skill includes:

- `SKILL.md`
- `scripts/run.sh`
- `references/`
- `assets/schema.json`

`scripts/run.sh` runs:

```bash
yamlgraph graph run <graph_path> --var <key>=<example> ...
```

`references/` contains one markdown file per referenced prompt (`<prompt-name>.md`) with at least:

- `## Description`
- `## Template`

## Output Layout by Format

| Format | Target path |
|--------|-------------|
| `skill-md` | `<output-dir>/<skill-name>/...` |
| `copilot` | `<output-dir>/.copilot/skills/<skill-name>/...` |
| `cursor` | `<output-dir>/.cursor/skills/<skill-name>/...` |
| `agent-md` | `<output-dir>/.github/agents/<skill-name>.agent.md` |

## Examples

```bash
# Standard portable directory
yamlgraph skill export examples/demos/hello/graph.yaml --format skill-md

# Copilot Skills layout
yamlgraph skill export examples/demos/hello/graph.yaml --format copilot --output-dir .

# Cursor Skills layout
yamlgraph skill export examples/demos/hello/graph.yaml --format cursor --output-dir .

# Copilot agent mode file with YAMLGraph tool scoping
yamlgraph skill export examples/demos/hello/graph.yaml --format agent-md --output-dir .
```
