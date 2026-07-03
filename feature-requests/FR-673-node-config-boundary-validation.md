# Feature Request: Validate node config shape at the node-compiler boundary

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 1-2 days
**Requested:** 2026-07-03

## Summary

Node factories receive raw `dict[str, Any]` node configs. A YAML typo
(`promtp:` instead of `prompt:`) defaults to `None` via `.get()` and only
fails at node execution time — or worse, silently changes behavior. The
`NodeConfig` Pydantic schema exists in `models/graph_schema.py` but is used
for validation only; it is not the object handed to factories. Reject
unknown keys at graph-load time.

## Value Statement

Graph authors get a load-time error naming the misspelled key instead of a
runtime failure (or silent misbehavior) deep in node execution.

## Problem

- `yamlgraph/node_compiler.py` passes raw dicts to `create_node_function`
- `yamlgraph/node_factory/llm_nodes.py:46`, `copilot_node.py:197` and peers
  extract fields with `.get()` — unknown keys are ignored, missing keys
  default to `None`
- `models/graph_schema.py::NodeConfig` validates known fields but tolerates
  extras (or its validation result is discarded rather than passed on)

This is `the_one_law`: normalize at the boundary where external data (user
YAML) enters, not downstream where the `None` manifests. The linter catches
some cases, but the loader is the enforcement gate — lint is advisory
(`detection_without_enforcement`).

## Proposed Solution

Minimal, two-step:

1. Set `model_config = ConfigDict(extra="forbid")` on `NodeConfig` (and the
   per-type config models) in `models/graph_schema.py`, so unknown keys fail
   schema validation at `load_graph_config()` with a message naming the key
   and the node.
2. Audit `examples/` and `graphs/` for graphs that rely on tolerated extra
   keys; fix or add the keys to the schema explicitly.

Explicitly out of scope (Purge): rewriting node factories to consume
`NodeConfig` objects instead of dicts — that is a larger migration; the
load-time gate delivers most of the value alone. If factory migration is
wanted later, it is its own FR.

## Acceptance Criteria

- [ ] Failing test first (RED): graph YAML with `promtp:` on an llm node →
      `load_graph_config` raises naming node and unknown key
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

**APPROVED.** NodeConfig confirmed: `model_config = {"extra": "allow"}`
at graph_schema.py:255. node_compiler.py passes raw dicts at line 358.
The fix is mechanical: change `allow` to `forbid`.

**Amendments:**
1. `graph_schema.py` is already at ~610 lines — far over the 450 ceiling.
   Land FR-674 (module splits) first, or at minimum split guard configs
   out before adding validation logic.
2. The `extra="forbid"` change will likely break existing graphs that use
   undocumented fields. The audit step ("scan examples/ and graphs/") is
   critical — do it BEFORE writing the RED test to scope the blast radius.
3. Consider `extra="ignore"` with a deprecation warning as a migration
   step if the audit reveals widespread use of undocumented fields. But
   prefer `forbid` if the blast radius is small.
