# Judgement: FR-770 Vision Demo Consumes the Tool Manifest (FR-768 Smoke)

**Prior art:** FR-770-vision-demo-consumes-manifest.md is the FR under judgement (self-hit). FR-768 (manifest mechanism) and FR-769 (demo being migrated) are dispositioned in the FR's own Prior art line and re-examined below — this FR is FR-768's first committed consumer, no mechanism overlap.

**Verdict:** APPROVED — the FR is a clear, minimal demo/documentation consumer of FR-768 with mechanically checkable acceptance criteria and no core-code expansion.

**Reviewed against:** `feature-requests/FR-770-vision-demo-consumes-manifest.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md` as provided in repo doctrine; `reference/getting-started.md`; `ARCHITECTURE.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-769-shared-vision-tool.md`; `feature-requests/FR-769-shared-vision-tool.judgement.md`; `docs/diary/diary-2026-08-04-the-verdict-i-almost-shipped-without-measuring.md`; `yamlgraph/tools/manifest.py`; `tests/unit/test_tool_manifest.py`; `reference/graph-yaml.md`; `examples/demos/shared-vision-tool/graph.yaml`; `examples/demos/shared-vision-tool/README.md`; `examples/demos/shared-vision-tool/nodes/demo.py`; `examples/demos/shared-vision-tool/demo-output.log`; `examples/shared/README.md`; `capabilities/CAP-216-tool-manifests.yaml`; `capabilities/CAP-217-shared-vision-tool.yaml`; current repo search for `manifest:` under `examples/`.

## What is sound

The problem is real and bounded. FR-770 identifies a concrete first consumer/event: FR-768 currently has no committed graph example outside tests when someone asks to see `manifest:` in use (`feature-requests/FR-770-vision-demo-consumes-manifest.md:8-17`, `feature-requests/FR-770-vision-demo-consumes-manifest.md:25-42`). Current evidence supports that claim: the shared-vision demo still declares `describe_image` inline (`examples/demos/shared-vision-tool/graph.yaml:9-19`), and repo search found no `manifest:` key consumers under `examples/` beyond unrelated prose/variable names.

The proposal is minimal. It adds one manifest file, changes one demo graph entry to a manifest reference, updates directly related docs, adds one artifact-backed regression test, and refreshes the existing demo proof (`feature-requests/FR-770-vision-demo-consumes-manifest.md:52-89`, `feature-requests/FR-770-vision-demo-consumes-manifest.md:91-108`). That fits the three-layer architecture: graph YAML declares logic/tool bindings, Python tools keep side effects in `examples/shared`, and no core runtime change is proposed (`ARCHITECTURE.md:36-70`).

The approach is feasible against the implemented manifest contract. `ToolManifest` supports `runtime.type: python` with `module` plus `function`, validates through Pydantic, requires the graph entry to contain only `manifest`, and translates module manifests back to inline Python tool config at graph load (`yamlgraph/tools/manifest.py:33-49`, `yamlgraph/tools/manifest.py:63-70`, `yamlgraph/tools/manifest.py:90-100`, `yamlgraph/tools/manifest.py:143-180`). Unit tests already prove module-manifest translation, graph-relative manifest resolution, name mismatch failures, and extra-key failures (`tests/unit/test_tool_manifest.py:54-102`, `tests/unit/test_tool_manifest.py:172-201`, `tests/unit/test_tool_manifest.py:272-294`).

The FR correctly redeems prior scope without reopening it. FR-768 explicitly left AC-09 chaplain migration pending and implemented core manifest support, tests, capability, docs, and changelog (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:5`, `feature-requests/FR-768-tool-manifest-declaration-reuse.md:115-148`); FR-769 explicitly said the vision tool would become manifest-declared once FR-768 landed (`feature-requests/FR-769-shared-vision-tool.md:70-75`, `feature-requests/FR-769-shared-vision-tool.md:163-166`). FR-770 performs that deferred example migration only.

Strategic classification: **Contrib/example**. This is not a new framework primitive; it is one committed example and documentation consumer of an already-enforced primitive, with an artifact-backed test to keep the example from drifting.

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/shared/describe_image.tool.yaml` declaring `describe_image` as a `runtime.type: python` module manifest for `examples.shared.vision_tool.describe_image` |
| D-2 | `examples/demos/shared-vision-tool/graph.yaml`, changed only so `tools.describe_image` contains exactly `manifest: ../../shared/describe_image.tool.yaml`; `describe_demo_image` remains graph-local inline glue |
| D-3 | A unit test that loads the committed shared-vision demo graph and asserts the expanded `describe_image` config matches the previous inline module/function/description shape under `REQ-YG-574` |
| D-4 | Refreshed `examples/demos/shared-vision-tool/demo-output.log` from a successful smoke run of the migrated graph |
| D-5 | `examples/shared/README.md` vision section updated to show the manifest declaration as the graph-facing shared-tool form |
| D-6 | `reference/graph-yaml.md` Tool Manifests section updated to point to the shared-vision demo as a committed manifest example |
| D-7 | One changelog fragment under `changelog/unreleased/` |
| D-8 | Graph-authoring validation artifact/report required by the governed demo graph edit |

Not authorized: changes to `yamlgraph/tools/manifest.py`, graph loader semantics, tool runtime semantics, `examples/shared/vision_tool.py`, the provider/model contract, new dependencies, chaplain planner/enforcer/judge migration, websearch/replicate migrations, image_pipeline/storyboard/npc/style_convert wiring, DeviantArt posting, CI/hooks/judge/review doctrine, or any generic registry/include/capability system.

## Revised acceptance criteria

- [ ] AC-01: `examples/shared/describe_image.tool.yaml` exists and validates as a `ToolManifest` with `name: describe_image`, the existing description, and `runtime.type: python` using `module: examples.shared.vision_tool` plus `function: describe_image`.
- [ ] AC-02: `examples/demos/shared-vision-tool/graph.yaml` has `tools.describe_image` containing exactly `manifest: ../../shared/describe_image.tool.yaml`; no other keys are present beside `manifest`, and `tools.describe_demo_image` remains the graph-local `type: python` wrapper.
- [ ] AC-03: `yamlgraph graph lint examples/demos/shared-vision-tool/graph.yaml` passes after the migration.
- [ ] AC-04: A smoke run of `yamlgraph graph run examples/demos/shared-vision-tool/graph.yaml --var image=examples/demos/shared-vision-tool/fixture.png --full` succeeds against the live supported provider used by the existing wrapper, and `examples/demos/shared-vision-tool/demo-output.log` is refreshed with the successful result marker.
- [ ] AC-05: A unit test loads the committed demo graph and asserts the expanded `describe_image` tool config has `type: python`, `module: examples.shared.vision_tool`, `function: describe_image`, no `path`, and the expected description; the test carries `@pytest.mark.req("REQ-YG-574")`.
- [ ] AC-06: `examples/shared/README.md` documents the manifest declaration for `describe_image`, and `reference/graph-yaml.md` links or names `examples/demos/shared-vision-tool/graph.yaml` as a committed manifest example.
- [ ] AC-07: A changelog fragment is added under `changelog/unreleased/` with `req: REQ-YG-574`.
- [ ] AC-08: The graph-authoring route validation report exists and records lint plus smoke evidence for the governed demo graph edit.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | The graph edit is a governed graph artifact change; enforcement must use the graph-authoring route and must preserve its validation report as evidence. | GATE |
| C-2 | The implementation must not change manifest core behavior, graph loading, Python tool execution, provider selection, or the shared vision tool implementation. | GATE |
| C-3 | `describe_demo_image` is local wrapper glue and must not be converted to a manifest under this FR. | GATE |
| C-4 | The chaplain trio and all other duplicated tool consumers remain out of scope; any such migration requires its own authority and, for enforcement infrastructure, human review. | GATE |
| C-5 | If the live smoke cannot be run because provider credentials are unavailable, enforcement must stop and return with the missing evidence rather than substituting a mocked or stale `demo-output.log`. | GATE |

Authority granted: enforcement may add the shared vision manifest, migrate only the shared-vision demo's `describe_image` declaration to consume it, add the artifact-backed test, refresh directly related docs/demo proof/changelog, and nothing else.
