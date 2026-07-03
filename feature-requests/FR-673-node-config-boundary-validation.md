# Feature Request: Validate node config shape at the node-compiler boundary

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 1-2 days
**Requested:** 2026-07-03

## Summary

Node factories receive raw `dict[str, Any]` node configs. A YAML typo
(`promtp:` instead of `prompt:`) can be ignored by `.get()` callsites or fail
late. The `NodeConfig` Pydantic schema exists in `models/graph_schema.py`,
but `load_graph_config()` currently calls the manual validator in
`utils/validators.py`, not `validate_graph_schema()`. Reject unknown keys at
graph-load time by wiring the schema validator into the load boundary and
forbidding extras where appropriate.

## Value Statement

Graph authors get a load-time error naming the misspelled key instead of a
runtime failure (or silent misbehavior) deep in node execution.

## Problem

- `yamlgraph/node_compiler.py` passes raw dicts to `create_node_function`
- `yamlgraph/node_factory/llm_nodes.py:46`, `copilot_node.py:197` and peers
  extract fields with `.get()` — unknown keys are ignored, missing keys
  default to `None`
- `models/graph_schema.py::NodeConfig` validates known fields but tolerates
   extras
- `graph_loader.py::GraphConfig.__init__` calls `utils.validators.validate_config`,
   so changing `NodeConfig.extra` alone will not affect `load_graph_config()`

This is `the_one_law`: normalize at the boundary where external data (user
YAML) enters, not downstream where the `None` manifests. The linter catches
some cases, but the loader is the enforcement gate — lint is advisory
(`detection_without_enforcement`).

## Proposed Solution

Minimal, two-step:

1. Call `validate_graph_schema(config)` from the graph-load boundary (or make
   `utils.validators.validate_config` delegate to it) after compile-time YAML
   expansions and before storing raw config in `GraphConfig`.
2. Set `model_config = ConfigDict(extra="forbid")` on `NodeConfig` after
   explicitly modeling legitimate node keys. Keep top-level graph extras only
   where existing graph-level extension keys require them.
3. Audit `examples/` and `graphs/` for graphs that rely on tolerated extra
   keys; fix or add the keys to the schema explicitly.

Explicitly out of scope (Purge): rewriting node factories to consume
`NodeConfig` objects instead of dicts — that is a larger migration; the
load-time gate delivers most of the value alone. If factory migration is
wanted later, it is its own FR.

## Acceptance Criteria

- [ ] Failing test first (RED): graph YAML with `promtp:` on an llm node →
   `load_graph_config` raises naming node and unknown key
- [ ] Test proves changing only `NodeConfig.extra` is insufficient without
   loader-boundary schema validation
- [ ] All shipped graphs (`graphs/`, `examples/`) load cleanly
- [ ] `yamlgraph graph validate` surfaces the new error with file context
- [ ] All unit tests green
- [ ] Documentation updated (`reference/graph-yaml.md` — unknown keys rejected)
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

- **New linter check for unknown keys** — rejected as primary fix: linting
  is advisory; the loader is the blocking gate. A lint check may complement.
- **Pass `NodeConfig` objects through to factories** — deferred: large
  mechanical migration touching every node factory; the extra="forbid" gate
  catches the defect class without it.

## Related

- docs/2026-07-03-review-fable.md (Issue 5)
- yamlgraph/models/graph_schema.py (NodeConfig)
- yamlgraph/node_compiler.py, yamlgraph/node_factory/

## Judgement

**APPROVED WITH REQUIRED AMENDMENT.** The boundary problem is real, but the
original proposed fix was incomplete. `NodeConfig` has
`model_config = {"extra": "allow", "populate_by_name": True}`, and
`node_compiler.py` passes raw dicts. However, `load_graph_config()` does not
currently use `GraphConfigSchema`; it calls the manual validator in
`utils/validators.py`. Therefore `extra="forbid"` alone would not reject
`promtp:` at load time.

**Amendments:**
1. Wire Pydantic schema validation into the loader boundary, then forbid
   unknown node keys. The acceptance test must call `load_graph_config()`,
   not `validate_graph_schema()` directly.
2. The `extra="forbid"` change will likely break existing graphs that use
   undocumented fields. The audit step ("scan examples/ and graphs/") is
   critical — do it BEFORE writing the RED test to scope the blast radius.
3. Consider `extra="ignore"` with a deprecation warning as a migration
   step if the audit reveals widespread use of undocumented fields. But
   prefer `forbid` if the blast radius is small.
