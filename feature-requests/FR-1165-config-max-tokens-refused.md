# Feature Request: FR-1165 Refuse the graph-level config.max_tokens that was never applied

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Requested:** 2026-11-14
**First consumer / first event:** the next graph author who writes
`config: {max_tokens: N}` as `reference/graph-yaml.md` tells them to. Today
the load accepts it and every LLM call runs at the provider default; after
this FR the load fails and names `defaults.max_tokens`.
**Research:** [FR-1165.research.md](FR-1165.research.md)
(brief: `research-briefs/fr1165-config-max-tokens-ignored-brief.md`)
**Prior art:** `feature-requests/027-execution-safety-guards.md` (added the
`config.max_tokens` parse and REQ-YG-060; never wired it, so this FR retires
its unapplied half). FR-223 (moved node `max_tokens` resolution to
`node_config` then `defaults`; this FR keeps that chain as the only one).
FR-984 (`config.max_concurrency`, a graph-level key that is applied; not
touched). Retrieval hits FR-779, FR-983, FR-1048 and draft-56 share only
vocabulary (`config`, `max`, `ignored`) and are dismissed.

## Summary

`config.max_tokens` is documented as the default output-token limit for all
LLM calls, is parsed into `GraphConfig.max_tokens`, and is read by nothing.
Remove it and make the loader refuse it with a message that points at
`defaults.max_tokens`, which already does what the docs promise.

## Value Statement

Graph authors who set a token limit get either the limit or an error, never
a silent provider default.

## Problem

- `yamlgraph/compile/graph_loader.py` stores
  `self.max_tokens = graph_level_config.get("max_tokens")`. A workspace grep
  at `c91e862d` finds no reader outside tests.
- LLM nodes resolve `node_config.get("max_tokens", defaults.get("max_tokens"))`
  (`yamlgraph/node_factory/llm_nodes.py`); `node_compiler.py` builds the
  effective defaults from `config.defaults` only.
- `git show c96d9e69` (feature request 027) shows the parse was the only
  loader change; FR-223's refactor never consumed it. The tests
  `test_graph_config_max_tokens` and `test_json_schema_has_max_tokens_in_config`
  check that the value parses, not that it reaches a call
  (`gate_checks_shape_not_substance`).
- CAP-17 REQ-YG-060 states "max_tokens wired from YAML config/node config";
  half of that claim is false.
- No graph in the repo sets `config.max_tokens` (git grep at `c91e862d`);
  `examples/dungeon_master/*.yaml` use `defaults.max_tokens`.

## Ideal Result

There is one graph-wide way to set the output-token limit
(`defaults.max_tokens`), and every place that documents or validates graph
config agrees with it. A key that does nothing cannot be written without an
error.

## Planned Operations

```yaml
probes:
  - "git grep 'max_tokens' in graph-v1.json and the linter schema — decides which schema surfaces drop the key"
  - "git grep -n 'config:' -A8 in examples/ graphs/ .github/ for a config.max_tokens user — any hit is migrated to defaults.max_tokens in the same commit"
branches:
  - "a repo graph sets config.max_tokens → move it to defaults.max_tokens in the GREEN commit"
  - "the published schema is generated, not hand-written → change the generator input, regenerate"
delegations:
  - "research.sh: 1 run (done)"
  - "judge.sh: 1 run"
waits:
  - "judge"
commands:
  - scripts/judge.sh
  - pytest tests/unit/test_fr027_execution_safety.py tests/unit/test_fr1165_config_max_tokens_refused.py
  - python scripts/req_coverage.py --strict
```

## Proposed Solution

1. `GraphConfig.__init__`: if `"max_tokens" in graph_level_config`, raise
   `ValueError("config.max_tokens is not applied to any LLM call; set defaults.max_tokens (graph-wide) or max_tokens on the node")`.
   Delete the `self.max_tokens` attribute.
2. Remove `max_tokens` from the `config` block of the published graph JSON
   schema, from `reference/graph-yaml.md` (the example and the table row),
   and from CAP-17 REQ-YG-060's description (it becomes "node config or
   defaults").
3. Tests: replace `test_graph_config_max_tokens`,
   `test_graph_config_max_tokens_default_none` and
   `test_json_schema_has_max_tokens_in_config` with
   `tests/unit/test_fr1165_config_max_tokens_refused.py`:
   - loading a graph with `config.max_tokens` raises and the message names
     `defaults.max_tokens`;
   - a graph with `defaults.max_tokens: 123` and an LLM node calls the
     executor with `max_tokens=123` (no network; patch `execute_prompt`);
   - the published schema has no `config.max_tokens`.

Out of scope (parked): prompt YAML files carrying an undocumented top-level
`max_tokens` (`examples/book_translator/prompts/identify_chapters.yaml`),
which is also unread. Separate FR if wanted.

## Acceptance Criteria

- [ ] AC-01: `load_graph_config` on a graph with `config: {max_tokens: 4096}`
  raises `ValueError` whose message contains `defaults.max_tokens`.
- [ ] AC-02: a graph with `defaults: {max_tokens: 123}` passes `123` to the
  executor for an LLM node without its own `max_tokens`.
- [ ] AC-03: `git grep -n "max_tokens" reference/graph-yaml.md` shows no row
  or example under the `config:` block; the published schema's `config`
  properties have no `max_tokens`.
- [ ] AC-04: `GraphConfig` has no `max_tokens` attribute (vulture clean).
- [ ] AC-05: RED commit (AC-01/AC-03 tests fail) precedes GREEN; unit suite
  and `req_coverage --strict` pass.

## Alternatives Considered

From the research record: four of five personas proposed wiring the key
into the defaults chain (node → defaults → config → provider). Rejected:
`defaults.max_tokens` already gives a graph-wide default, so wiring adds a
second key for the same job and a precedence rule to document and test,
with no consumer (no graph uses it). The subtractionist's deletion is
chosen, with a load-time refusal instead of a new linter rule, so an
external graph that sets the key learns at load, not only when linted. The
librarian's Pydantic `extra="forbid"` for the whole config block is broader
than this defect and would change behavior for every unknown key; parked.

## Related

- [FR-1165.research.md](FR-1165.research.md)
- `capabilities/CAP-17-execution-safety-guards.yaml` (REQ-YG-060)
