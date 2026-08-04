# Feature Request: FR-772 — tool_call Inline Dict Args with Per-Value Resolution

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved with revisions (judged 2026-08-04) — R-1 folded as option 2 (inline-branch validation), R-2 folded (REQ-YG-576 under CAP-05)
**Effort:** 0.5 days
**Requested:** 2026-08-04
**Prior art:** FR-658 (Enforced) created the `tool_call` node with `args: "{state.X}"` — a single state-dict reference, LLM-orchestration shaped; this FR adds the deterministic-invocation shape it lacks. FR-252 (python node `variables:`) already established per-key template resolution via `resolve_node_variables` — this FR reuses that exact mechanism, honoring existing patterns rather than inventing a resolver. FR-771 (Approved with revisions, blocked) is the judged first consumer whose judgement (R-1/C-2) mandated this FR instead of an in-scope core patch.
**First consumer / first event:** FR-771 — the shared-vision demo's `describe` node, the moment it invokes the manifest-declared `describe_image` with `{image: "{state.image}", instruction: <literal>, provider: google}`. Without this FR, no graph can call a kwargs tool deterministically with mixed literal/templated args; every such call site needs a Python wrapper (the registry-bypass class FR-771 exists to delete).

## Summary

Support an inline YAML mapping as `tool_call.args`, resolving each value
through the existing template resolver:

```yaml
nodes:
  describe:
    type: tool_call
    tool: describe_image
    args:
      image: "{state.image}"        # templated — resolved per value
      instruction: "Title, 2-sentence description, and 8 DeviantArt tags."
      provider: google              # literal — passed through
    state_key: described
```

Current behavior: `create_tool_call_node()` calls
`resolve_template(args_expr, state)` once; `resolve_template` returns
non-string values unchanged, so an inline dict passes through with
`"{state.image}"` as a literal string — then dispatched as garbage kwargs.
The existing `args: "{state.tool_arguments}"` (whole dict from state) form
keeps working unchanged.

## Value Statement

Graph authors get deterministic tool invocation with mixed literal and
templated kwargs in pure YAML — no Python wrapper per call site — completing
the manifest pipeline (declare once, invoke anywhere) that FR-768/770/771
build.

## Ideal Result

`tool_call.args` accepts either form: a string template resolving to a
state dict (existing), or an inline mapping whose values are each resolved
(new). A graph author cannot tell from behavior which resolver ran — values
resolve exactly as python-node `variables:` do (FR-252 semantics). Unresolved
garbage kwargs are impossible: an inline dict never reaches the tool with a
literal `"{state...}"` string inside.

## Proposed Solution

In `yamlgraph/node_factory/tool_nodes.py::create_tool_call_node`, branch on
the YAML shape of `args`:

```python
if isinstance(args_expr, dict):
    from yamlgraph.utils.expressions import resolve_node_variables
    args = resolve_node_variables(args_expr, state)   # FR-252 semantics
else:
    args = resolve_template(args_expr, state)          # existing form
```

- `resolve_node_variables` resolves each value; literals pass through.
- Nested dicts inside values: whatever `resolve_node_variables` does today
  is the contract (FR-252 semantics, no new resolver) — document it.
- **Inline-branch validation (judgement R-1, option 2):** after resolution,
  the inline-dict branch rejects any resolved arg value that still contains
  the substring `"{state."` by raising `ValueError` naming the node, key,
  and offending value — covering embedded interpolation of missing paths
  (`"prefix {state.missing}"`), which `resolve_template` leaves unchanged.
  This validation applies ONLY to the new inline-dict branch; global
  `resolve_template()` behavior and the string-form `args` path are
  untouched. (Simple missing paths resolve to `None` per existing FR-252
  semantics — passed through, not rejected.)
- The existing silent `args = {}` fallback for non-dict resolution results
  is unchanged for the string form but must never trigger for the inline
  form (an inline mapping is already a dict).
- Docs: `reference/graph-yaml.md` tool_call section gains the inline form.

## Acceptance Criteria

- [ ] AC-01: Inline dict args: templated values resolve from state, literal
      values pass through, and the tool receives the resolved kwargs
      (unit test with a recording callable).
- [ ] AC-02: A templated value that resolves to a non-string (int, list,
      dict from state) is passed with its type intact.
- [ ] AC-03: The existing string form `args: "{state.tool_arguments}"`
      behaves exactly as before (regression test alongside existing
      test_tool_call_node tests).
- [ ] AC-04: The inline-dict branch raises `ValueError` (naming node, key,
      value) when a resolved value still contains `"{state."` — test with
      embedded interpolation of a missing path (`"prefix {state.missing}"`).
      Simple missing paths (`"{state.missing}"`) resolve to `None` per
      existing FR-252 semantics — regression test pins this. Global
      `resolve_template()` is unchanged.
- [ ] AC-05: `reference/graph-yaml.md` documents both forms with the
      deterministic-invocation example.
- [ ] AC-06: New requirement REQ-YG-576 under **CAP-05 Tool & Agent
      Integration** (owns `node_factory/tool_nodes` and REQ-YG-017);
      all new tests marked.
- [ ] AC-07: Changelog fragment with the new `req:`.

## Alternatives Considered

- **Patch under FR-771**: forbidden by its judgement C-2 — core surface
  needs its own judged authority.
- **New `variables:` key on tool_call instead of overloading `args:`**:
  rejected — two arg channels on one node invites precedence ambiguity;
  the YAML shape (string vs mapping) is an unambiguous discriminator.
- **Recursive deep resolution of arbitrarily nested dicts**: rejected —
  reuse FR-252 semantics as-is; a deeper resolver is a separate need with
  no named consumer.

## Related

- [FR-771-vision-demo-executes-manifest-tool.md](FR-771-vision-demo-executes-manifest-tool.md) — blocked consumer
- [FR-658-graph-as-tool.md](FR-658-graph-as-tool.md) — tool_call origin
- yamlgraph/node_factory/tool_nodes.py — dispatch site
- yamlgraph/utils/expressions.py — `resolve_node_variables` (FR-252)
