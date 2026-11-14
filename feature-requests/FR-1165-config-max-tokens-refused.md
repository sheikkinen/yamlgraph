# Feature Request: FR-1165 Refuse the graph-level config.max_tokens that was never applied

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced (judged APPROVED WITH REVISIONS; R-1..R-3 folded)
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
   The refusal is by key presence, so `config.max_tokens: null` and a graph
   that sets both `config.max_tokens` and `defaults.max_tokens` also fail.
2. Remove `max_tokens` from the `config` properties of
   `yamlgraph/schemas/graph-v1.json` (the schema stays permissive for other
   keys, `additionalProperties: true`; the loader owns the refusal), from
   `reference/graph-yaml.md` (the config example and table row; the node
   property table's `max_tokens` default changes from "from config" to
   "from defaults"; `defaults.max_tokens` is named as the graph-wide
   setting), and from CAP-17 REQ-YG-060's description (it becomes "node
   config or defaults"). The changelog fragment names the refusal and
   `defaults.max_tokens`.
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

(Revised per judgement R-3.)

- [ ] AC-01: Parameterized `load_graph_config` tests reject
  `config.max_tokens: 4096` and `config.max_tokens: null` with `ValueError`
  naming both `config.max_tokens` and `defaults.max_tokens`. A graph with
  both config and defaults token values also fails.
- [ ] AC-02: with `yamlgraph.node_factory.llm_nodes.execute_prompt` patched
  and no network, load, compile and invoke a minimal LLM graph with
  `defaults.max_tokens: 123`; the executor receives `max_tokens=123`. A node
  override of `456` receives `456`; neither set receives `None`.
- [ ] AC-03: parsed `graph-v1.json` has no `max_tokens` in
  `properties.config.properties`; `reference/graph-yaml.md` has no config
  token example or row, the node default says "from defaults", and the
  graph-wide replacement is documented. Schema permissiveness for other keys
  is unchanged.
- [ ] AC-04: a loaded graph without the key has no `max_tokens` attribute;
  CAP-17 REQ-YG-060 describes node/default propagation only.
- [ ] AC-05: RED before GREEN; the forbidden-key and schema tests fail for
  the defect in RED. Every new test carries `@pytest.mark.req("REQ-YG-060")`.
- [ ] AC-06: recorded passes: the two targeted test files, `pytest
  tests/unit/ -q --no-cov`, `python scripts/req_coverage.py --strict`, ruff
  on changed files; scoped vulture/radon as context.
- [ ] AC-07: FR records status, decisions and deviations; changelog
  fragment names the refusal and `defaults.max_tokens`; diary entry has a
  **Seed:**; the repo-user scan result is recorded.

## Alternatives Considered

(Revised per judgement R-1.) The research record's `convergent x5` label
counts persona rows, not solution classes; three personas proposed wiring,
one deletion with a linter rule, one a Pydantic-level prohibition. The
solution classes:

| # | Alternative | Decision | Precedent | Addresses silent acceptance at load? |
|---|---|---|---|---|
| A | Wire `config.max_tokens` as a precedence level (node > defaults > config > provider) — os-infra, data-process, yamlgraph-native | reject | `llm_nodes.py:156` already resolves node then defaults; `node_compiler.py:342-346` copies `config.defaults` | Yes, but adds a second graph-wide key for the job `defaults.max_tokens` does, plus a precedence rule to document and test, with no consumer (no repo graph sets it) |
| B | Delete the key, enforce with a new linter rule — subtractionist | reject | CAP-172 W026 (linter precedent) | No: `graph run` without `lint` still accepts it silently |
| C | Delete the key, refuse it at load by presence | **pursue** | `graph_loader.py` already raises `ValueError` for invalid config at load | Yes, on every entry path (run, lint, compile) |
| D | Pydantic `extra="forbid"` on the graph config — librarian | park | `graph_schema.py:112` permits extra fields today | Yes, but changes behavior for every unknown key; broader than this defect |

C differs from B only in where enforcement lives: the loader is the
boundary every graph crosses (`the_one_law`), the linter is optional.

## Implementation Status

Enforced on branch `fix/fr1165-config-max-tokens-refused`.

- Probes: the `graph-v1.json` `config` block is hand-written (no generator
  owns it; `graph_schema.py` has no `config` model), so the property was
  removed in place. Repo-user scan: 1102 tracked YAML files parsed, 0 graphs
  set `config.max_tokens`; no graph migration.
- RED `065bd4e3`: 6 defect witnesses failed (refusal x3, attribute, schema,
  docs); 3 defaults-propagation witnesses passed, as allowed by AC-05.
- GREEN: loader refusal by presence; schema property, docs example and row
  removed; node row says "from defaults"; REQ-YG-060 narrowed; the three
  parse/schema tests in `test_fr027_execution_safety.py` deleted.
- Deviation (D-1 location): the refusal lives in
  `yamlgraph/utils/validators.py::validate_config`, which `GraphConfig`
  calls first, not inline in `graph_loader.py`: the inline form put
  `graph_loader.py` at 454 lines and the file-size gate (max 450) refused
  the commit. Same boundary, and `graph lint` now reports the key too. The
  `GraphConfig.max_tokens` assignment is removed as planned.
- Deviation (docs): the replacement note lives in the node-table row, not
  the `config` section, so the docs witness can require that section be
  free of `max_tokens`.
- Local unit suite on Windows: 328 failures, all in shell/hook-script test
  files; the files that could touch loading were re-run on `main`
  (`c91e862d`) with the identical 40-failure set. CI is the authority.

| AC | Witness | Result |
|---|---|---|
| AC-01 | `test_config_max_tokens_refused_at_load[value,null,with-defaults]` | pass |
| AC-02 | `test_defaults_max_tokens_reaches_executor[defaults,node-override,neither]` | pass |
| AC-03 | `test_schema_does_not_advertise_config_max_tokens`, `test_reference_documents_defaults_max_tokens_only` | pass |
| AC-04 | `test_loaded_graph_has_no_max_tokens_attribute`; CAP-17 wording | pass |
| AC-05 | RED `065bd4e3` before GREEN; all tests tagged REQ-YG-060 | pass |
| AC-06 | targeted files, unit suite, `req_coverage --strict`, ruff | see PR |
| AC-07 | this section; changelog fragment; diary entry with **Seed:** | pass |

## Related

- [FR-1165-config-max-tokens-refused.judgement.md](FR-1165-config-max-tokens-refused.judgement.md)
- [FR-1165.research.md](FR-1165.research.md)
- `capabilities/CAP-17-execution-safety-guards.yaml` (REQ-YG-060)
