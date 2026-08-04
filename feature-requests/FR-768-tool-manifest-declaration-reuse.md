# Feature Request: FR-768 — Tool Manifests: Declaration Reuse Over Existing Runtimes

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved with revisions (judged 2026-08-04 — [FR-768-tool-manifest-declaration-reuse.judgement.md](FR-768-tool-manifest-declaration-reuse.judgement.md))
**Effort:** 2 days
**Requested:** 2026-08-04
**First consumer / first event:** the chaplain planner/enforcer/judge trio
(`examples/demos/planner|enforcer|judge/graph.yaml`), the first time their
shared repo toolkit (`read_file`, `search`, `list_dir`, `git_log`,
`write_file`, `run_tests`) needs an edit — today that edit must be made
three times and the copies drift.

## Summary

Add a `manifest:` key to `tools:` entries so a reusable tool can be described
once in a small YAML file next to its implementation and referenced by many
graphs. The manifest layer performs discovery and translation into the
existing shell/python/graph tool definitions — **no new execution engine**.

## Value Statement

Graph authors declare a shared tool once and reference it everywhere,
eliminating verbatim-duplicated tool blocks (measured: 26 signatures
copy-pasted across example graphs) and the description/binding drift that
comes with them.

## Problem

Example graphs duplicate tool declarations verbatim. Measured 2026-08-04
across all `tools:` blocks in `examples/` (fingerprint per tool:
`type:path:function` / `type:command`):

- **333 tool declarations, 280 unique signatures, 26 signatures declared in
  >1 graph** (~16% of declarations are copies).
- **novel_fandom** (~30 duplicate declarations): the six `create_*.yaml`
  graphs each re-declare the identical `dedup_pre_check`/`persist`/`prefetch`
  trio; `reload_canon` ×6, `list_canon_ids` ×4, `lookup_canon_page` ×3,
  `create_*` graph-tools ×2–3 in worldgen/genesis/world_pressure/event_revision.
- **Chaplain agent trio** (`examples/demos/planner|enforcer|judge/graph.yaml`):
  a byte-identical repo toolkit copy-pasted across all three — production
  agents, not pedagogical demos. Descriptions drift independently when edited.
- **examples/shared re-wrapped per project**: `replicate_tool.py` is consumed
  by four example families (image_pipeline, npc, storyboard, style_convert),
  each writing its own wrapper node module because a tool cannot be declared
  once and referenced.

## Ideal Result

A shared tool is one file. Any graph consumes it with one line. Editing the
tool's description, binding, or inputs happens in exactly one place and every
consumer graph sees the change on next load. Inline declarations remain fully
supported; a manifest-declared tool is byte-for-byte indistinguishable at
runtime from the same tool declared inline.

## Proposed Solution

A manifest is a small YAML file next to the implementation:

```yaml
# nodes/reload_canon.tool.yaml
name: reload_canon
description: Reload canon pages from disk into state.
runtime:
  type: python
  path: reload_canon.py       # resolved relative to the manifest file
  function: reload_canon
```

Graphs reference it instead of re-declaring the binding:

```yaml
tools:
  reload_canon:
    manifest: nodes/reload_canon.tool.yaml   # resolved relative to the graph
```

Resolution flow: read manifest → inspect `runtime.type` → translate into the
existing shell/python/graph tool definition → register with the existing
runtime. Manifest-relative path resolution mirrors FR-658's
parent-graph-relative resolution. Draft design:
`docs/tmp/yamlgraph-manifest-resolution-proposal.md`.

## Manifest Schema (folded from judgement R-1, R-2)

Top-level fields:

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Must match the graph-local tool key; mismatch fails graph load |
| `description` | yes | Tool description surfaced to agent LLMs |
| `runtime` | yes | Runtime binding block, per-type fields below |

- `runtime.type: shell` — required `command`; optional `parse` (`text`/`json`,
  default `text`) and `timeout`. Same semantics as inline shell tools.
- `runtime.type: python` — required `function` plus exactly one of `path`
  (resolved relative to the manifest file) or `module`; declaring both fails
  graph load.
- `runtime.type: graph` — required `path` (resolved relative to the manifest
  file); optional `input_mapping`, `output_key` — identical semantics to
  FR-658 inline `type: graph` declarations; invocation behavior unchanged.

Manifest YAML is parsed into typed Pydantic validation models **before**
translation (normalize at the boundary). Unknown fields, conflicting fields,
unknown `runtime.type`, missing manifest files, invalid YAML, and unresolved
paths all fail during graph load — never at invocation, never silently.

## Enforcement Gates (folded from judgement R-5, C-4/C-5)

The chaplain planner/enforcer/judge graphs are production enforcement
infrastructure: their migration to shared manifests must follow the
graph-authoring route (validation record required) and the migrated diff
requires human review before merge.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `tools.<name>.manifest` is accepted in graph YAML and resolved
      relative to the referencing graph.
- [ ] AC-02: Paths inside a manifest are resolved relative to the manifest
      file, with tests proving sibling and nested manifest locations.
- [ ] AC-03: Manifest YAML is validated through typed models at graph load;
      missing manifest, invalid YAML, unknown runtime type, missing required
      runtime fields, unsupported field combinations, and unresolved paths
      fail before invocation.
- [ ] AC-04: A shell manifest translates to the same effective tool config
      and runtime output as the equivalent inline shell declaration,
      including `command`, `description`, and `parse`.
- [ ] AC-05: A Python `path` manifest translates to the same effective tool
      config and runtime output as the equivalent inline Python `path`
      declaration, including manifest-relative path resolution.
- [ ] AC-06: A Python `module` manifest translates to the same effective tool
      config and runtime output as the equivalent inline Python `module`
      declaration.
- [ ] AC-07: A graph manifest translates to the same effective tool config
      and runtime output as the equivalent inline `type: graph` declaration
      without changing FR-658 invocation behavior.
- [ ] AC-08: Existing inline shell, Python, graph, and other tool
      declarations continue to load and run unchanged.
- [ ] AC-09: The chaplain planner/enforcer/judge graphs consume one shared
      manifest set for their duplicated repo toolkit, with graph lint/smoke
      evidence recorded by the graph-authoring validation artifact.
- [ ] AC-10: `reference/graph-yaml.md` documents manifest syntax, schema,
      path semantics, examples for each supported runtime, and load-time
      error behavior.
- [ ] AC-11: A capability/requirement entry is created for manifest-declared
      tools, all new tests are tagged with the new `REQ-YG-XXX`, and
      requirement coverage passes for the new mapping.
- [ ] AC-12: A changelog fragment is added.

## Alternatives Considered

- **Full capability model** (registry/resolver/invoker tiers,
  `docs/tmp/yamlgraph-capability-model.md`): rejected — no consumer for the
  third abstraction tier; the translation layer delivers the value.
- **YAML anchors/includes**: anchors don't cross files; a custom include
  mechanism is a bigger, more general hammer than a tool-scoped manifest.
- **Do nothing**: the duplication is verbatim today but drifts on every edit;
  the chaplain trio already shows description divergence risk.

## Prior Art (dispositioned)

- **FR-658 (graph-as-tool, Enforced)**: `type: graph` tools exist; this FR
  does not touch invocation, only declaration reuse. Complementary.
- **CAP-111 / `shared:` graphs (FR-255)**: established declare-once,
  reference-many for graphs; tools have no analog.
- **FR-044 (contrib libraries)**: contrib.io deferred ("patterns too
  varied"), FR-044c slugify rejected ("unified API more complex than
  inline") — those concerned *Python code* abstraction where implementations
  diverged. Here the duplicated declarations are verbatim identical, so the
  unified-API complexity objection does not apply.
- **docs/tmp/yamlgraph-graph-as-tool-mvp.md**: its `interface:`/import ideas
  are out of scope here; the shipped FR-658 covers invocation.

## Related

- FR-769 (shared vision tool) — intended early manifest-declared capability
  alongside `websearch` and `replicate_tool` in `examples/shared/`.
- `docs/tmp/yamlgraph-manifest-resolution-proposal.md` — design draft.
