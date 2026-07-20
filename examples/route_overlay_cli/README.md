# Route Overlay CLI Example (FR-753)

A standalone example app that turns a graph YAML + route JSONL into:

- Authored Mermaid text
- Overlay Mermaid text
- Rendered images via Mermaid CLI (`mmdc`)

This example is separate from the core `yamlgraph` CLI and does not modify core behavior.

## Install

Python environment:

```bash
pip install -e ".[dev]"
```

Mermaid CLI:

```bash
npm i -g @mermaid-js/mermaid-cli
```

Verify:

```bash
mmdc --version
```

## Usage

```bash
python examples/route_overlay_cli/cli.py render \
  --graph examples/demos/router/graph.yaml \
  --route outputs/routes/route.jsonl \
  --out-dir examples/route_overlay_cli/outputs \
  --format svg
```

Outputs are written with fixed names:

- `graph.authored.mmd`
- `graph.overlay.mmd`
- `graph.authored.svg` (or `.png`)
- `graph.overlay.svg` (or `.png`)

## Demo Flow

Run the end-to-end demo script:

```bash
bash examples/route_overlay_cli/demo.sh
```

## Troubleshooting

`mmdc not found`:

1. Install Mermaid CLI: `npm i -g @mermaid-js/mermaid-cli`
2. Ensure your npm global bin directory is in `PATH`
3. Re-open terminal and verify with `mmdc --version`

`mmdc` fails with "Could not find Chrome":

1. Install the headless browser used by Mermaid CLI:
  `npx puppeteer browsers install chrome-headless-shell`
2. Re-run the CLI command.
3. If needed, confirm Puppeteer cache path configuration in your shell environment.

`Route file contains no valid route events`:

1. Re-run graph with `YAMLGRAPH_ROUTE_LOG=<path>`
2. Confirm route file has JSON lines with `"event": "route"`
3. Use a graph with routing decisions (router/conditional/map fan-out)
