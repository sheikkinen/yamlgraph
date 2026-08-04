# Feature Request: FR-771 — Vision Demo Executes the Manifest-Declared Tool

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced 2026-08-04 — unblocked by FR-772 (enforced same day). AC-01..AC-10 delivered: demo migrated to `type: tool_call` with inline args via the authoring route (lint zero warnings — W001 gone; live smoke showing `type=tool_call` + `success: True` + populated ImageDescription), wrapper `nodes/demo.py` deleted, 5 invocation-boundary artifact tests, README, changelog.
**Effort:** 0.5 days
**Requested:** 2026-08-04
**Prior art:** FR-770 (Enforced) made the demo *declare* `describe_image` via manifest — this FR makes it *execute* that declaration; same artifact, next boundary. FR-768 (manifest mechanism) untouched. FR-658 (graph-as-tool) supplied the `tool_call` node this FR routes through (AC-6: direct tool invocation). FR-769 shipped the wrapper (`nodes/demo.py`) this FR deletes.
**First consumer / first event:** the FR-768 regression surface — today a defect in how a *translated* tool executes (registry wiring, kwargs dispatch) passes the demo smoke, because the executed path goes through `nodes/demo.py`'s direct Python import, not the tool registry. First event: the next manifest-runtime regression that the demo should have caught and didn't.

## Summary

Close the declaration/invocation gap found in the FR-770 reflection: the
demo's manifest-declared `describe_image` is registered but never invoked —
the node calls a wrapper that imports the function directly, bypassing the
registry (the standing lint W001 says exactly this). Replace the wrapper
node with a `tool_call` node that executes the manifest-declared tool
through the registry, and delete the wrapper.

## Value Statement

The demo becomes a true end-to-end smoke for FR-768: manifest → load →
validate → translate → register → **execute**. One less file, one less
W001-as-accepted-noise, and the "committed consumer" claim becomes true at
the invocation boundary, not just the load boundary.

## Problem

Coverage as of FR-770 (from the reflection):

| Manifest pipeline stage | Exercised by the demo? |
|---|---|
| Reference resolution / validation / translation / registration | ✅ every run |
| **Execution through the manifest-declared tool** | ❌ only tmp_path unit fixtures |

The wrapper exists because `type: python` nodes pass the whole state dict
(`func(effective_state)`), while `describe_image(image, instruction, *,
provider, model)` has a kwargs tool signature. The framework already has the
right seam: `tool_call` nodes invoke registry callables as
`tool_func(**args)` (`yamlgraph/node_factory/tool_nodes.py`).

A warning accepted as "expected" in two authoring briefs (W001 unused tool)
was flagging this gap the whole time.

## Ideal Result

The demo graph declares exactly one tool — the manifest reference — and its
single node executes that tool through the registry. `nodes/demo.py` no
longer exists. The demo run fails if any stage of the manifest pipeline,
including kwargs dispatch of the translated callable, regresses.

## Proposed Solution

```yaml
# examples/demos/shared-vision-tool/graph.yaml (target state)
tools:
  describe_image:
    manifest: ../../shared/describe_image.tool.yaml

nodes:
  describe:
    type: tool_call
    tool: describe_image
    args:
      image: "{state.image}"
      instruction: "Title, 2-sentence description, and 8 DeviantArt tags."
      provider: google          # pins past ambient PROVIDER (azure incident, FR-769)
    state_key: described
```

- Delete `examples/demos/shared-vision-tool/nodes/demo.py` and the
  `describe_demo_image` tool declaration.
- `described` now holds the `tool_call` result envelope
  (`{task_id, tool, success, result, error}`); update the demo README and
  refresh `demo-output.log`. The envelope's `success: true` plus the
  `ImageDescription` payload in `result` is the new evidence shape.
- State: `described: dict` unchanged.
- Graph edit via the graph-authoring sole route (`scripts/author.sh`).

**Known risk (resolved by judgement R-1, verified against source):** inline
dict args are NOT supported by current `tool_call` — `resolve_template()`
returns non-string values unchanged, so `"{state.image}"` would pass through
as a literal string and `tool_call` would silently dispatch garbage kwargs.
No YAML-only strategy exists (state dicts require a python node — the
wrapper class this FR deletes; passthrough uses the same single-value
resolver; CLI vars are strings). **Stop condition (R-1 outcome 2):** no
implementation authority until FR-772 (recursive per-value resolution of
inline `tool_call.args` dicts) is judged and enforced. Core `tool_nodes.py`
is not patched under this FR (C-2). The `tool_call` envelope also swallows
tool exceptions into `success: false` — evidence must assert `success:
true`, not merely exit 0 (folded into AC-07).

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: The FR records a feasible args strategy (R-1): inline dict args
      per FR-772, enforced only after FR-772 lands.
- [ ] AC-02: The demo graph's `tools:` section contains exactly one entry —
      `describe_image` with only the `manifest:` key.
- [ ] AC-03: The `describe` node is `type: tool_call`, targets
      `describe_image`, with args proven to resolve to a dict containing the
      real image path, the fixed instruction, and `provider: google`.
- [ ] AC-04: `nodes/demo.py` is deleted; no declaration references
      `describe_demo_image`.
- [ ] AC-05: A unit/artifact test fails if the final `tool_call.args` value
      is `{}`, non-dict, or contains the literal unresolved string
      `"{state.image}"` (R-2 — guards the silent `args={}` fallback).
- [ ] AC-06: `graph lint` passes with zero warnings (W001 gone).
- [ ] AC-07: Live smoke exits 0 AND committed `demo-output.log` shows the
      `describe` node executing as `type=tool_call` (not `type=python`),
      `success: true`, and a populated `ImageDescription` payload (R-3).
- [ ] AC-08: FR-770's artifact tests extended: no python wrapper tool
      remains, node type is `tool_call`, manifest translation assertions
      still pass (REQ-YG-574 markers).
- [ ] AC-09: Demo README shows the `tool_call` pattern and result envelope.
- [ ] AC-10: Changelog fragment added; `req:` omitted with the FR-768/
      REQ-YG-574 reuse cited in prose.

## Alternatives Considered

- **Keep the wrapper, call through the registry from Python**: rejected —
  the graph still wouldn't exercise the registry path; the bypass just
  moves.
- **`type: python` node with `variables:`**: rejected — python nodes pass
  the merged state dict, not kwargs; the tool signature doesn't fit without
  the wrapper this FR deletes.
- **Accept the load-boundary-only smoke**: rejected by the reflection —
  W001 marked a real gap twice; leaving it institutionalizes
  warning-as-noise.

## Related

- [FR-770-vision-demo-consumes-manifest.md](FR-770-vision-demo-consumes-manifest.md) — declaration boundary (done)
- [FR-768-tool-manifest-declaration-reuse.md](FR-768-tool-manifest-declaration-reuse.md) — the feature under smoke
- [FR-658-graph-as-tool.md](FR-658-graph-as-tool.md) — `tool_call` direct invocation (AC-6)
- yamlgraph/node_factory/tool_nodes.py — `tool_func(**args)` dispatch
