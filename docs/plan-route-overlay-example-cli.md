# Plan: Separate Example App CLI for Route Overlay (MMDC)

## Objective

Create a standalone example app under `examples/` with a CLI that:

1. Validates required route input (`--route`) for overlay rendering.
2. Generates authored Mermaid (`.mmd`) and overlay Mermaid (`.mmd`) from a graph and route log.
3. Renders both diagrams to images via `mmdc`.
4. Produces deterministic output files for demo and CI verification.

This is an example app, not a core CLI change.

## Why Separate App

- Keeps framework CLI (`yamlgraph graph ...`) focused on core behaviors.
- Demonstrates complete end-user route-visualization workflow including image rendering.
- Avoids coupling node-based `mmdc` dependency to core package runtime.

## Scope

In scope:
- New example app directory with `README`, CLI script, and demo runner.
- Validation that route input is explicitly provided for overlay mode.
- Rendering authored and overlay diagrams via `mmdc`.
- Minimal tests for CLI validation and output artifacts.

Out of scope:
- Changes to `yamlgraph graph export` behavior.
- GUI/web app.
- Auto-installing Node/npm dependencies.

## Target Structure

```text
examples/route_overlay_cli/
  README.md
  demo.sh
  cli.py
  sample/
    graph.yaml
    route.jsonl
  outputs/                      # gitignored or demo-generated artifacts
  tests/
    test_cli_validation.py
    test_cli_smoke.py
```

## CLI Contract

Command:

```bash
python examples/route_overlay_cli/cli.py render \
  --graph examples/demos/reflexion/graph.yaml \
  --route tmp/route.jsonl \
  --out-dir examples/route_overlay_cli/outputs \
  --format svg
```

Arguments:
- `render` subcommand: generate and render authored+overlay diagrams.
- `--graph` (required): graph YAML path.
- `--route` (required for `render`): route JSONL path.
- `--out-dir` (optional, default `./outputs`).
- `--format` (optional: `svg|png`, default `svg`).
- `--mmdc` (optional, default `mmdc`): override binary path.
- `--theme` (optional, passed through to mmdc).

Validation rules (load-bearing):
1. `--graph` must exist and be a file.
2. `--route` must be defined for `render` (hard fail if missing).
3. `--route` must exist and be a file.
4. `--route` must parse to at least one valid route line (using `parse_route_lines`).
5. `mmdc` must be discoverable (`command -v mmdc` equivalent); otherwise clear install hint.

Exit codes:
- `0`: success.
- `2`: argument/validation error.
- `1`: runtime/render failure.

## Rendering Pipeline

For each run:

1. Load graph YAML config.
2. Build authored Mermaid text via `render_mermaid(config)`.
3. Parse route lines via `parse_route_lines(...)`.
4. Build overlay Mermaid via `render_overlay(config, route)`.
5. Write:
   - `<out-dir>/graph.authored.mmd`
   - `<out-dir>/graph.overlay.mmd`
6. Run `mmdc` twice:
   - authored `.mmd` -> `.svg/.png`
   - overlay `.mmd` -> `.svg/.png`
7. Print artifact summary paths.

Output file set:
- `graph.authored.mmd`
- `graph.overlay.mmd`
- `graph.authored.<fmt>`
- `graph.overlay.<fmt>`

## Implementation Steps

1. Scaffold app
- Add `examples/route_overlay_cli/` with `README.md`, `cli.py`, `demo.sh`, `tests/`.

2. Implement CLI in `cli.py`
- Use `argparse` (repo-consistent for example scripts).
- Implement `render` command and validations.
- Reuse framework functions:
  - `yamlgraph.cli.helpers.load_graph_config` (or graph loader helper)
  - `yamlgraph.mermaid_export.render_mermaid`
  - `yamlgraph.mermaid_export.parse_route_lines`
  - `yamlgraph.mermaid_export.render_overlay`
- Shell out to `mmdc` with `subprocess.run(..., check=True)`.

3. Add demo runner `demo.sh`
- Runs with a known graph + route sample.
- Writes outputs to app `outputs/`.
- Captures command output in `demo-output.log`.

4. Add tests
- `test_cli_validation.py`
  - missing `--route` fails with exit 2.
  - missing route file fails with clear message.
- `test_cli_smoke.py`
  - monkeypatch `subprocess.run` to avoid real `mmdc` dependency in unit tests.
  - verifies both `.mmd` files are created and `mmdc` invoked twice.

5. Documentation
- `README.md` includes:
  - install `mmdc` (`npm i -g @mermaid-js/mermaid-cli`)
  - usage examples
  - troubleshooting (`mmdc` not found, empty route file)

## Example README Usage

```bash
# 1) Produce route log from a real run
YAMLGRAPH_ROUTE_LOG=tmp/reflexion.route.jsonl \
  yamlgraph graph run examples/demos/reflexion/graph.yaml --var topic=AI

# 2) Render authored + overlay images
python examples/route_overlay_cli/cli.py render \
  --graph examples/demos/reflexion/graph.yaml \
  --route tmp/reflexion.route.jsonl \
  --out-dir examples/route_overlay_cli/outputs \
  --format svg
```

## Acceptance Criteria

- [ ] Separate app exists under `examples/route_overlay_cli/`.
- [ ] `render` command requires `--route` and fails clearly when omitted.
- [ ] `.mmd` authored and overlay files are generated every successful run.
- [ ] `mmdc` renders both diagrams to selected format.
- [ ] CLI prints final artifact paths.
- [ ] Unit tests pass without requiring global `mmdc` (via subprocess mocking).
- [ ] Demo script runs end-to-end when `mmdc` is installed.

## Risks and Mitigations

1. `mmdc` unavailable in environment
- Mitigation: explicit preflight check + install instructions.

2. Route file contains no valid lines
- Mitigation: parse check and actionable error before render.

3. Mermaid syntax mismatch from custom graphs
- Mitigation: keep authored and overlay `.mmd` artifacts for debugging even on image render failure.

## Suggested Next Action

Implement this plan as `FR-753` (example app deliverable) so it can pass through judge/enforce with explicit tests and demo proof.
