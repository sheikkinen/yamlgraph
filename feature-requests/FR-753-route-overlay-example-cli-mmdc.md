# Feature Request: FR-753 Separate Example App CLI for Route Overlay Rendering with MMDC

**Priority:** MEDIUM
**Type:** Feature
**Status:** Completed (enforced 2026-07-19)
**Effort:** 1 day
**Requested:** 2026-07-19
**First consumer / first event:** graph authors who already produce route logs and need immediate visual proof; first event is the first local run where they pass graph + route and expect authored and overlay diagrams rendered to image files.

## Summary

Create a standalone example application under `examples/` that provides a CLI for route-overlay visualization with Mermaid CLI (`mmdc`). The app validates required route input, generates authored and overlay Mermaid files, and renders both outputs as SVG or PNG.

## Value Statement

Users get a single, reproducible command path from route log to rendered visualization, reducing route-debug setup from ad hoc shell steps to a deterministic example workflow.

## Problem

Current framework capabilities already provide:

- Authored map export and overlay generation (`yamlgraph graph export --mermaid --overlay ...`)
- Route capture via `YAMLGRAPH_ROUTE_LOG`

But end-to-end visual rendering (Mermaid text -> image) is still a manual process. This creates repeated friction in demos and local debugging:

1. Remembering command sequence and output paths.
2. Failing runs when route input is missing or invalid.
3. Inconsistent render artifacts across users.

A dedicated example app solves this without adding Node toolchain dependencies to the core framework CLI.

## Ideal Result

A user can run one example CLI command with explicit graph and route inputs, and always receive both authored and overlay Mermaid artifacts plus rendered image files in a predictable output folder. Missing route input is rejected at argument validation time with a clear message, and MMDC availability is checked before rendering.

## Proposed Solution

Implement a separate example app at `examples/route_overlay_cli/` with:

1. `cli.py` (argparse-based) with `render` subcommand.
2. Required `--graph` and `--route` arguments for render mode.
3. Validation gates:
   - graph exists and is a file
   - route is defined
   - route exists and is a file
   - route parses to at least one valid route line
   - `mmdc` is discoverable
4. Artifact generation:
   - `graph.authored.mmd`
   - `graph.overlay.mmd`
   - `graph.authored.<fmt>`
   - `graph.overlay.<fmt>`
5. `demo.sh` to run a known graph+route flow and capture demo output.
6. Unit tests that mock subprocess MMDC invocation.

```bash
python examples/route_overlay_cli/cli.py render \
  --graph examples/demos/reflexion/graph.yaml \
  --route tmp/reflexion.route.jsonl \
  --out-dir examples/route_overlay_cli/outputs \
  --format svg
```

Technical reuse boundary:

- `yamlgraph.mermaid_export.render_mermaid`
- `yamlgraph.mermaid_export.parse_route_lines`
- `yamlgraph.mermaid_export.render_overlay`
- existing graph config loading helper(s)

No changes to core `yamlgraph graph export` behavior.

## Acceptance Criteria

- [x] AC-01 New example app exists at `examples/route_overlay_cli/` with README, CLI, demo script, and tests.
- [x] AC-02 `render` command hard-fails when `--route` is omitted.
- [x] AC-03 Existing but invalid route path fails with clear diagnostic.
- [x] AC-04 Successful run always writes authored and overlay `.mmd` files.
- [x] AC-05 Successful run invokes `mmdc` twice and renders both diagrams to selected format (`svg|png`).
- [x] AC-06 CLI prints output artifact paths.
- [x] AC-07 Unit tests pass without requiring real `mmdc` installation (subprocess mocked).
- [x] AC-08 README documents install and usage, including MMDC troubleshooting.

## Alternatives Considered

1. Extend core `yamlgraph graph export` to render images directly.
   - Rejected for this FR: would couple Node-based rendering dependency to core CLI path.

2. Keep workflow as documented shell snippets only.
   - Rejected: does not enforce required route argument checks or deterministic artifact contract.

3. Build a web UI example instead of CLI.
   - Rejected: larger scope and dependency surface for first consumer need.

## Related

- FR-723 execution path visualization (route hook + export + overlay)
- FR-752 route log path-target semantics
- Plan source: `docs/plan-route-overlay-example-cli.md`
- Expected implementation area: `examples/route_overlay_cli/`

**Prior art:** FR-723 and FR-752 are direct prerequisites reused by this example-only layer (no core CLI changes); FR-541/544/470 are domain-specific overlay features in Dungeon Master flows and are out of scope for this standalone route-to-image example CLI.

## Judgement (2026-07-19)

**Verdict: AUTHORITY GRANTED** -- scope frozen with the pins below.

Claims verified against source before judging: reusable seams already exist in
`yamlgraph/mermaid_export.py` (`render_mermaid`, `parse_route_lines`,
`render_overlay`) and the FR-723 reflexion demo proves the operational route:
route JSONL -> overlay Mermaid -> export. Core docs currently stop at Mermaid
text export and do not provide an image-rendering CLI workflow; this FR's
example-app scope is therefore additive and non-duplicative.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | The FR is correct to stay out of core CLI, but the implementation seam must be explicit or enforce will drift into shelling out to `yamlgraph graph export` and reparsing text. | `examples/route_overlay_cli/cli.py` must call Python APIs directly: graph load helper + `render_mermaid` + `parse_route_lines` + `render_overlay`; no subprocess call to `yamlgraph graph export` inside the app. |
| F2 | "route parses to at least one valid route line" is load-bearing, but parse semantics are tolerant by design (non-route lines skipped). Without a pinned rule, empty-effective files can pass superficial checks. | Validation is frozen to `parse_route_lines(route_file_lines)` and requires `len(parsed) >= 1`; failure is exit code 2 with actionable message naming the route file. |
| F3 | MMDC dependency boundary is right, but availability check and failure phase must be pinned to avoid half-produced artifacts and ambiguous errors. | Preflight must verify `mmdc` discoverability before render subprocess calls. Missing binary is a hard fail (exit 2) with install hint; runtime `mmdc` failure after preflight is exit 1. |
| F4 | AC-05 says "invokes mmdc twice" but does not pin invocation contract; enforce could render one file twice or overwrite outputs. | Invocation contract is frozen: authored and overlay each have unique input `.mmd` and unique output image path; tests assert exactly two `subprocess.run` calls with distinct `-i/-o` pairs. |
| F5 | Output naming has unresolved options in the FR; ambiguity here creates needless churn in tests and docs. | Pin option A: fixed basenames `graph.authored.*` and `graph.overlay.*` in the selected output directory. |
| F6 | Test location in `examples/` can be missed by default fast test commands; AC-07 must name the witness command to avoid false confidence. | AC-07 witness is explicit: run `pytest examples/route_overlay_cli/tests -q` in addition to normal unit suite; tests must not require a real `mmdc` binary. |

**Purge list:**

- No core CLI behavior changes.
- No framework-level MMDC dependency requirement.
- No GUI/web layer.

**Scope frozen:** Separate example app CLI only, with explicit route-param validation and MMDC rendering.

### Questions for the human (as options, or 'none')

None -- judgement pins A for all three: default `svg`, fixed output names,
and missing MMDC hard-fails with install hint.

## Enforcement Notes (2026-07-19)

- Added standalone example app under `examples/route_overlay_cli/`:
   - `cli.py` (`render` subcommand, required `--graph` and `--route`, fixed artifact names)
   - `README.md` (install, usage, troubleshooting)
   - `demo.sh` (route-capture + render flow)
   - `tests/test_cli.py` (argparse hard-fail, route validation, mmdc preflight, two-call render contract)
- Binding-pin compliance:
   - Direct Python APIs used (`load_graph_config` + `render_mermaid` + `parse_route_lines` + `render_overlay`); no subprocess call to `yamlgraph graph export`.
   - Route parse gate enforces `len(parsed) >= 1` and exits with code 2 on failure.
   - MMDC preflight (`shutil.which`) fails fast with install hint (exit 2); runtime mmdc failure is exit 1.
   - Subprocess invocation contract tested with exactly two calls and distinct `-i/-o` pairs.
   - Output basenames pinned to `graph.authored.*` and `graph.overlay.*`.
- Test evidence:
   - `pytest examples/route_overlay_cli/tests -q --no-cov` -> `5 passed`
   - `pytest examples/route_overlay_cli/tests -q` exercises same tests but fails repository-global coverage gate when run in isolation.
- Demo script smoke:
   - `bash examples/route_overlay_cli/demo.sh` executed the route-capture step successfully and invoked the CLI render step.
   - In this local environment, Mermaid CLI failed at runtime due missing Puppeteer Chrome runtime (`chrome-headless-shell`), which is documented in README troubleshooting.
