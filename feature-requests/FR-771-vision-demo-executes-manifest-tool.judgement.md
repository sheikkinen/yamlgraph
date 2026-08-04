# Judgement: FR-771 Vision Demo Executes the Manifest-Declared Tool

**Prior art:** FR-771-vision-demo-executes-manifest-tool.md is the FR under judgement (self-hit). FR-770 (declaration boundary), FR-768 (manifest mechanism), FR-658 (tool_call), FR-769 (wrapper origin) are dispositioned in the FR's Prior art line and re-examined below.

**Verdict:** APPROVED WITH REVISIONS — the problem is real and the scope is correctly small, but authority activates only after the FR replaces its currently infeasible inline `tool_call.args` plan with a mechanically proven args strategy.

**Reviewed against:** `feature-requests/FR-771-vision-demo-executes-manifest-tool.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-770-vision-demo-consumes-manifest.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-658-graph-as-tool.md`; `feature-requests/FR-769-shared-vision-tool.md`; `examples/demos/shared-vision-tool/graph.yaml`; `examples/demos/shared-vision-tool/nodes/demo.py`; `examples/demos/shared-vision-tool/README.md`; `examples/demos/shared-vision-tool/demo-output.log`; `examples/shared/describe_image.tool.yaml`; `yamlgraph/node_factory/tool_nodes.py`; `yamlgraph/utils/expressions.py`; `yamlgraph/node_factory/control_nodes.py`; `reference/graph-yaml.md`; `reference/passthrough-nodes.md`; `reference/expressions.md`; `tests/unit/test_fr770_demo_manifest.py`; `tests/unit/test_tool_call_node.py`; `tests/unit/test_tool_call_integration.py`; `tests/unit/test_passthrough_node.py`.

## What is sound

The FR identifies a genuine declaration/invocation gap: the current demo declares `describe_image` through a manifest but still declares and executes `describe_demo_image` as a local Python wrapper (`examples/demos/shared-vision-tool/graph.yaml:9-22`), and the wrapper imports and calls `describe_image` directly (`examples/demos/shared-vision-tool/nodes/demo.py:5-13`). The committed smoke output confirms that execution path by logging two parsed Python tools and a `type=python` `describe` node, not a `tool_call` node (`examples/demos/shared-vision-tool/demo-output.log:1-4`, `15-17`).

The proposed direction aligns with existing architecture. FR-768 intentionally made manifests a declaration-translation layer, not a new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:16-20`, `78-83`), and FR-658 already authorized direct `tool_call` invocation (`feature-requests/FR-658-graph-as-tool.md:28-30`, `73-75`). The change is single-purpose and example-scoped: make the existing shared-vision demo exercise manifest registration through invocation, delete one wrapper, and refresh documentation/evidence (`feature-requests/FR-771-vision-demo-executes-manifest-tool.md:13-18`, `71-76`).

The acceptance shape is mostly measurable. The FR demands exact graph structure, zero lint warnings, live smoke evidence that includes `success: true`, and updated artifact tests (`feature-requests/FR-771-vision-demo-executes-manifest-tool.md:91-106`). It also correctly notices that `tool_call` catches tool exceptions into `success: false`, so exit code alone is not proof (`feature-requests/FR-771-vision-demo-executes-manifest-tool.md:80-87`; `yamlgraph/node_factory/tool_nodes.py:79-89`).

The strategic classification is **Contrib/example**: this is one committed demo consumer proving an existing framework primitive at the execution boundary. It is not a new framework primitive, and it is not merely documentation because the current committed demo path demonstrably bypasses the registry.

## Required revisions

### R-1: Replace the unsupported inline args plan with a proven args strategy

Revise the Proposed Solution before enforcement. The target YAML in the FR currently proposes:

```yaml
args:
  image: "{state.image}"
  instruction: "Title, 2-sentence description, and 8 DeviantArt tags."
  provider: google
```

That is not supported by the cited implementation. `create_tool_call_node()` calls `resolve_template(args_expr, state)` once and then requires the result to be a dict (`yamlgraph/node_factory/tool_nodes.py:40-68`). `resolve_template()` returns non-string values unchanged (`yamlgraph/utils/expressions.py:192-193`), so an inline YAML dict is passed through with the literal `"{state.image}"` string still inside it. The documented `tool_call` pattern is `args: "{state.tool_arguments}"`, with args coming from state (`reference/graph-yaml.md:696-706`). Passthrough nodes do not cure this for a multi-key dict: they resolve each top-level output through the same single-value resolver (`yamlgraph/node_factory/control_nodes.py:149-156`), and their own tests document that complex dict transformations belong in Python nodes (`tests/unit/test_passthrough_node.py:42-57`) — the exact wrapper class this FR intends to delete.

Fold one of these outcomes into the FR, mechanically:

1. A YAML-only configuration using existing supported behavior, with a cited test or fixture proving `tool_call.args` becomes a dict containing the real image path, instruction, and `provider: google`; or
2. A stop condition stating that no implementation authority is granted until a separate judged FR authorizes recursive dict arg resolution or another core `tool_call` capability.

Do not implement core `tool_nodes.py`, expression-language, or passthrough changes under FR-771 unless the FR is revised and rejudged to authorize that exact core surface.

### R-2: Add an args-resolution acceptance test, not just smoke-output proof

Add or revise an acceptance criterion requiring a unit/artifact test that proves the final demo `tool_call` configuration passes a real dict to the manifest-registered callable: `image` must equal the graph input image path, `instruction` must equal the fixed demo instruction, and `provider` must equal `google`. The test must fail if args collapse to `{}` or if any value remains the literal string `"{state.image}"`. This is necessary because `tool_call` silently replaces non-dict args with `{}` (`yamlgraph/node_factory/tool_nodes.py:65-68`) and catches invocation errors into the result envelope (`yamlgraph/node_factory/tool_nodes.py:79-89`).

### R-3: Make the smoke evidence prove the registry path

Revise AC-04 so the committed `demo-output.log` proves both success and the path taken. It must show `success: true` with a populated `ImageDescription` payload and must also show evidence that the `describe` node compiled/executed as `type=tool_call`, not `type=python`. The current log proves the opposite path (`examples/demos/shared-vision-tool/demo-output.log:1-4`, `15-17`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-771-vision-demo-executes-manifest-tool.md` revised to fold R-1..R-3 |
| D-2 | `examples/demos/shared-vision-tool/graph.yaml` edited only through the graph-authoring route required for governed graph artifacts (`.github/copilot-instructions.md:15`) |
| D-3 | `examples/demos/shared-vision-tool/nodes/demo.py` deleted only if the graph no longer references it |
| D-4 | `examples/demos/shared-vision-tool/README.md` updated to show the final `tool_call` pattern and result envelope |
| D-5 | `examples/demos/shared-vision-tool/demo-output.log` refreshed from a live smoke run that proves `tool_call` execution and `success: true` |
| D-6 | `tests/unit/test_fr770_demo_manifest.py` or a tightly scoped successor test extended for invocation-boundary artifact assertions |
| D-7 | One changelog fragment under `changelog/unreleased/` |

Not authorized: changes to `yamlgraph/node_factory/tool_nodes.py`, `yamlgraph/utils/expressions.py`, passthrough semantics, manifest parsing/loading, `examples/shared/vision_tool.py` provider behavior, FR-768 chaplain trio migration, websearch/replicate migrations, image-pipeline/storyboard/npc/DeviantArt consumer wiring, CI/hook/doctrine changes, or any fallback wrapper that preserves the registry bypass.

## Revised acceptance criteria

- [ ] AC-01: The revised FR records a feasible args strategy per R-1 before implementation proceeds.
- [ ] AC-02: The demo graph's `tools:` section contains exactly one entry: `describe_image` with only the `manifest:` key.
- [ ] AC-03: The `describe` node is `type: tool_call`, targets `describe_image`, and uses an args configuration proven to resolve to a dict with the real image path, fixed instruction, and `provider: google`.
- [ ] AC-04: `examples/demos/shared-vision-tool/nodes/demo.py` is deleted and no graph/tool declaration references `describe_demo_image`.
- [ ] AC-05: A unit/artifact test fails if the final `tool_call.args` value is `{}`, non-dict, or contains the literal unresolved string `"{state.image}"`.
- [ ] AC-06: `yamlgraph graph lint examples/demos/shared-vision-tool/graph.yaml` passes with zero warnings, including no W001 unused-tool warning.
- [ ] AC-07: A live smoke run exits 0 and the committed `demo-output.log` shows the `describe` node executing as `type=tool_call`, the result envelope containing `success: true`, and a populated `ImageDescription` payload under `result`.
- [ ] AC-08: FR-770's artifact tests are updated or extended to assert no Python wrapper tool remains, the node type is `tool_call`, and manifest translation assertions still pass with `REQ-YG-574` markers.
- [ ] AC-09: The demo README shows the final `tool_call` pattern and result envelope shape.
- [ ] AC-10: A changelog fragment is added; if it omits `req:`, the body must cite the reused FR-768/REQ-YG-574 requirement rationale.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1..R-3 are folded into the FR. | GATE |
| C-2 | If no YAML-only args strategy works with existing `tool_call` behavior, stop and return for a new judgement; do not patch core under this FR. | GATE |
| C-3 | The graph edit must use the graph-authoring route and retain its validation artifact; manual governed-path edits are not authorized. | GATE |
| C-4 | Smoke success must be judged by the `described.success` envelope and payload, not by process exit alone. | GATE |
| C-5 | Any implementation that keeps a local Python wrapper or calls `examples.shared.vision_tool.describe_image` outside the registry fails the FR. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may migrate the shared-vision demo from the wrapper path to a manifest-backed `tool_call` path, delete the wrapper, and refresh the directly related tests, README, smoke log, and changelog only.
