# Feature Request: Verification as a First-Class DSL Construct

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged
**Effort:** 3 days
**Requested:** 2026-07-04

## Summary

Close the three gaps that keep verification a bolt-on instead of a first-class DSL construct: (1) `guards:` declared on unsupported node types are silently ignored, (2) there is no graph-level verification block for final-state assertions, and (3) lint findings never gate execution — `graph run` happily runs a graph that `graph lint` condemns.

## Value Statement

Graph authors get declarative, enforced correctness constraints in YAML — silent fallbacks are blocked at the boundary instead of discovered downstream in output artifacts.

## Problem

Four recent diary seeds (2026-06-03, 2026-07-01, 2026-07-02, 2026-07-03) converge on one theme: as model cost collapses, correctness enforcement becomes the dominant constraint, and it must live in the DSL, not in extra tooling. The current state violates that in three concrete ways:

### Gap 1 — Silent guard ignore (the worst kind of fallback)

`NodeConfig.guards` ([graph_schema.py:128](../yamlgraph/models/graph_schema.py)) accepts `guards:` on **any** node type, but only `llm_nodes.py` and `copilot_node.py` import `guard_runtime` and evaluate them. A `tool`, `python`, `agent`, `map`, `race`, `subgraph`, `tool_call`, `passthrough`, or `interrupt` node with declared guards can pass schema validation and run with **zero enforcement**. This is precisely the `plausible_wrong_answer` trap: the YAML looks protected; nothing protects it.

```yaml
nodes:
  write_report:
    type: python
    module: nodes.writer
    state_key: report
    guards:
      post:
        - check: "output | length > 100"   # ← never evaluated today
          on_fail: halt
```

### Gap 2 — No graph-level verification

`GraphConfigSchema` ([graph_schema.py:345](../yamlgraph/models/graph_schema.py)) has `nodes`, `edges`, `tools`, `loop_limits`, `data_files` — but no way to assert final-state invariants before END. `GraphConfig` likewise stores no graph-level verification config. Since top-level graph schema still allows extras, an unmodeled `verify:` key would be the same failure class as ignored node guards: accepted shape, ignored substance. Authors currently fake final-state checks with a trailing python node or leave the exit unverified.

### Gap 3 — Lint and run are disconnected

W022 (`on_error: skip` without verification question), W025 (non-executable guard expressions), and W026 (prompt monolith) exist only in the offline `graph lint` path. `graph run` executes graphs those rules condemn. Detection without enforcement is advisory — the Scripture's `detection_without_enforcement` process rule says: add the gate or remove the claim.

## Proposed Solution

Three moves, ordered by enforcement value per line of code.

### Move 1 — Guards evaluated on all node types (or rejected at compile)

Normalize at the boundary (`the_one_law`):

1. **Compile-time support matrix**: `node_compiler.py` raises `GraphConfigError` when `guards:` is declared on a node type whose factory does not wire `guard_runtime`. No silent ignore survives compilation.
2. **Supported in this FR**: `llm`, `router`, `copilot`, shell `tool`, `python`, and `agent` nodes. `llm`/`router`/`copilot` already evaluate guards; this FR adds parity for shell `tool`, `python`, and `agent` nodes.
3. **Rejected in this FR**: `map`, `race`, `subgraph`, `tool_call`, `passthrough`, and `interrupt` nodes fail compilation when they declare `guards:`. Composite and control-flow semantics need their own judgement.
4. **Runtime extension**: wire `guard_runtime.extract_guard_rules` and `evaluate_guards_once` into `tools/nodes.py`, `tools/python_tool.py`, and `tools/agent.py` — the three supported node types where deterministic pre/post conditions are most valuable at side-effect boundaries.

### Move 2 — Graph-level `verify:` block

```yaml
name: worldgen
verify:                              # evaluated once, before END
  - check: "state.entities | length > 0"
    on_fail: halt
    message: "worldgen produced no entities"
  - check: "state.errors | length == 0"
    on_fail: warn
```

- Reuses the existing guard expression language (`state.*`, filters: `length`, `file_exists`, `dir_exists`, `type`, `keys`) — **no new expression syntax**.
- Adds a graph-level verify rule model that shares the guard base shape (`check`, optional `message`) but permits only `on_fail: warn|halt`. Do not reuse `PostGuardRule` directly, because it permits `retry`.
- Adds `verify` to `GraphConfigSchema` and stores it on `GraphConfig`; malformed graph-level verify blocks fail at the loader boundary.
- Compiled as a terminal deterministic node inserted before END by `graph_loader.py`. `on_fail: halt` raises with the guard message; `warn` logs and appends a `PipelineError` to `state.errors`.
- Terminal-node insertion preserves existing explicit END edges and map / interrupt routing semantics. Direct END and conditional/router END paths are covered by tests.
- `retry` is **not** valid at graph level (nothing to re-execute).

### Move 3 — Run-time lint gate

```bash
yamlgraph graph run graph.yaml --gate        # lint first; refuse to run on any E-level finding
```

- Opt-in flag in this FR; flip-to-default is a follow-up FR once examples are clean.
- E-level lint findings block execution with a non-zero exit and the lint report; W-level findings print but do not block.
- Uses the existing linter entry point — the linter stays LLM-free (import-linter contract holds; `cli` may import `linter`).
- Output contract is explicit: human mode may print the lint report to stdout/stderr as today; `--json` mode emits machine-readable failure output without decorative text on stdout.

## Constraints

- No new expression language — graph-level `verify:` reuses `guard_evaluator` semantics, but not `PostGuardRule`'s retry-capable schema.
- Three-layer architecture: lint gate lives in `cli/graph_commands.py`; guard insertion in `graph_loader.py`/`node_compiler.py`; zero Layer-3 → Layer-2 imports.
- `guard_evaluator` is a security boundary at 73% coverage (FR-659); every new call path added here must bring its edge cases to coverage.
- Module caps: `node_compiler.py` is at 447/450 lines and `graph_schema.py` is at 443/450 lines — Move 1 and Move 2 likely force FR-674 behavior-preserving splits as prerequisite or companion chore commits. Keep those commits separate from behavior changes.

## Acceptance Criteria

- [x] Guard support matrix enforced: `llm`, `router`, `copilot`, shell `tool`, `python`, and `agent` accept/evaluate guards; `map`, `race`, `subgraph`, `tool_call`, `passthrough`, and `interrupt` reject `guards:` at compilation with an actionable error naming node and type
- [x] `guards.post` with `on_fail: halt` on a shell `type: tool` node raises when the check fails; passing check returns tool output unchanged
- [x] `guards.pre`/`guards.post` evaluated for `python` and `agent` nodes (parity tests mirroring existing llm-node guard tests)
- [x] Graph-level `verify:` block with `on_fail: halt` stops the run before END and surfaces `message`
- [x] Graph-level `verify:` with `on_fail: retry` fails schema validation
- [x] Graph-level `verify:` is represented in `GraphConfigSchema` and stored on `GraphConfig`; malformed blocks fail at load time
- [x] Inserted terminal verification node preserves explicit direct END and conditional/router END paths
- [x] `graph run --gate` exits non-zero without executing when lint reports an E-level finding; W-level findings do not block
- [x] `graph run --gate --json` returns machine-readable lint-gate failure output without decorative text on stdout
- [x] Lint rule: graph-level `verify:` expressions validated by W025 (same executable-expression check as node guards)
- [x] All tests tagged `@pytest.mark.req(...)` against a new REQ-YG-XXX; `capabilities/CAP-XXX-first-class-verification.yaml` added
- [ ] `reference/graph-yaml.md` documents `verify:` block and `--gate`; changelog fragment in `changelog/unreleased/`
- [ ] Demo: `examples/demos/` graph exercising node guards on a tool node + graph-level `verify:` + `--gate`, with `demo-output.log`

## Alternatives Considered

1. **LLM-based verification questions everywhere** — rejected: the existing `verify.question` pattern is LLM-adjacent and probabilistic; the seeds ask for *deterministic* gates. Deterministic guards are cheaper and falsifiable.
2. **Lint-gate as pre-commit hook only** — rejected: graphs are also run by the chaplain, MCP server, and A2A server; the gate must sit at the execution boundary, not the commit boundary.
3. **New `assert` node type** — rejected: a trailing python node already emulates this; the value is *declarative* verification without a node, reusing existing guard schema. A new node type adds surface without adding enforcement.
4. **Silently evaluating guards on composite/control-flow nodes** — deferred: `map`, `race`, `subgraph`, `tool_call`, `passthrough`, and `interrupt` each need explicit semantics. Compile-time rejection is honest until judged.

## Related

- FR-344 — deterministic node guards (foundation being extended)
- FR-164 — verification questions + W022
- FR-659 — guard_evaluator coverage gaps (security boundary)
- FR-673 — node config boundary validation (same normalize-at-boundary doctrine)
- FR-674 — proactive module splits (node_compiler.py prerequisite)
- Diary seeds: [2026-07-03](../docs/diary/2026-07-03-world-digest.md), [2026-07-02](../docs/diary/2026-07-02-world-digest.md), [2026-07-01](../docs/diary/2026-07-01-world-digest.md), [2026-06-03](../docs/diary/2026-06-03-world-digest.md)
- Scripture: `detection_without_enforcement`, `substance_over_presence`, `the_one_law`

## Judgement

**APPROVED WITH REQUIRED AMENDMENTS.** The three gaps are real and worth
fixing as one coherent enforcement feature: guards are schema-visible but only
LLM/router and Copilot nodes evaluate them; there is no graph-level final-state
verification construct; and `graph run` has no lint gate. This FR correctly
targets the DSL boundary rather than adding another advisory tool.

**Verified facts:**

- `guard_runtime.evaluate_guards_once` is currently called only from
  `node_factory/llm_nodes.py` and `node_factory/copilot_node.py`.
- `tools/nodes.py`, `tools/python_tool.py`, `tools/agent.py`, and
  `node_factory/tool_nodes.py` do not evaluate `guards`.
- `GraphConfigSchema` has no `verify` field, and `GraphConfig` stores no
  graph-level verification config. Because top-level graph schema still allows
  extras, an unmodeled `verify:` key would be especially dangerous: accepted
  shape, ignored substance.
- `cmd_graph_run` has no `--gate` path today; lint exists only through the
  separate `graph lint` command.

**Required amendments folded into the FR:**

1. Define an explicit guard support matrix for every node type. In this FR,
  support guards on `llm`, `router`, `copilot`, `tool` (shell), `python`, and
  `agent`. Reject `map`, `race`, `subgraph`, `tool_call`, `passthrough`, and
  `interrupt` when they declare `guards:` unless this FR deliberately adds
  runtime semantics for them.
2. Be precise about `tool`: acceptance criteria must say shell `type: tool`.
  Dynamic `type: tool_call` is a separate node factory and should be rejected
  for guards in this FR unless explicitly implemented.
3. Do not literally reuse `PostGuardRule` for graph-level `verify`, because it
  allows `on_fail: retry`. Add a graph-level rule model that shares the base
  `check`/`message` shape and evaluator, but permits only `warn` and `halt`.
4. Add `verify` to `GraphConfigSchema` and `GraphConfig`, not just runtime
  insertion. The loader boundary must reject malformed graph-level verify
  blocks; this avoids recreating the silent-ignore bug at graph scope.
5. Terminal-node insertion must preserve existing explicit END edges and map /
  interrupt routing semantics. Add tests for at least direct END and one
  conditional/router END path so the inserted verification node cannot become
  a control-flow regression.
6. `graph run --gate` should call the same linter path as `graph lint`, but
  the output contract must be tested in both human and `--json` modes. In
  JSON mode, lint-gate failures must not print decorative text to stdout.
7. Module-cap pressure is real: `node_compiler.py` is 447 lines and
  `graph_schema.py` is 443 lines. Land behavior-preserving splits from
  FR-674 before or inside this work as separate commits, not mixed with the
  enforcement change.

**Verdict:** Approved with these amendments folded into the body. The scope is large but coherent:
all three moves convert verification from advisory/partial DSL shape into an
execution-boundary contract. Do not split the lint gate away unless the
implementation shows the graph-level insertion is larger than expected; the
three parts reinforce the same invariant.

## Implementation Log

**Move 1 — node guards (committed 34a1c21c).** `guard_runtime` moved from
`node_factory/` to `utils/` (bottom side-effect tier) so Layer-3 tool factories
can share the guard contract without a Layer-3 → Layer-2 import. `GraphConfigError`
(subclass of `ValueError`) raised in `node_compiler.compile_node` when `guards:`
is declared on a type outside `GUARD_SUPPORTED_TYPES`. Guards wired into
`tools/nodes.py`, `tools/python_tool.py`, `tools/agent.py`. 19 tests in
`tests/unit/test_fr677_node_guards.py`.

**Move 2 — graph-level `verify:` (this commit).** Decisions:

- **No new node_compiler/graph_schema bloat.** The verify node factory
  (`create_verify_node`) lives in `utils/guard_runtime.py`, reusing
  `evaluate_guards_once` with a new `"verify"` phase — so graph-level verify
  shares the exact node-guard evaluation path (no second expression engine).
  `GuardViolation.phase` Literal extended to `"pre" | "post" | "verify"`.
- **Config-level rewrite, not runtime patching.** A new `verify_insert.py`
  transform (`insert_verify_node`) mirrors `expand_pipeline_templates`: it runs
  in `load_graph_config` after pipeline expansion, inserts a `__verify__` node
  `{type: verify}`, redirects every explicit `END` destination (scalar edges,
  list fan-out/router edges, router `routes`/`default_route`, and `loop_exits`)
  through it, then appends `__verify__ → END`. Deep-copies input (no mutation).
- **Router `routes`/`default_route` redirected too.** The LLM router stores the
  *resolved target node* in `state._route`; a `routes: {done: END}` mapping had
  to be rewritten to `__verify__` as well, else the router would fall through to
  `targets[0]` after edge redirection.
- **Delta-only error return.** `state.errors` uses an `add` reducer, so the
  verify node returns only new `PipelineError` deltas, never the merged list.
- **Schema at the loader boundary.** `GraphVerifyRule(GuardRuleBase)` permits
  only `on_fail: warn|halt` (inherits `extra: forbid`, so `retry` and
  `max_retries` are rejected). `verify: list[GraphVerifyRule]` added to
  `GraphConfigSchema`; `GraphConfig.verify` stores the raw list. Malformed
  blocks raise `ValueError` at load.
- **Known limitation (accepted).** `routing.make_expr_router_fn` has an implicit
  `return END` fallthrough when no condition matches ("shouldn't happen with
  well-formed graphs"). That error path bypasses verify; it is not an explicit
  END edge, so it is out of scope.

**Move 3 — `graph run --gate` lint gate (this commit).** Decisions:

- **Lint-first, opt-in.** `--gate` (default off) added to `graph_run_parser`.
  When set, `cmd_graph_run` calls `_run_lint_gate` immediately after the
  file-existence check, before any config load / compile / invoke. The gate
  reuses the existing `lint_graph(path, WORKING_DIR)` path — one linter, no
  second implementation (satisfies the Judgement's "same linter path").
- **Error blocks, warning reports.** Only `severity == "error"` findings abort
  (exit 1); warnings print but do not block. In `--json` mode the gate emits
  `result.model_dump_json()` to stdout *only when blocking* — no decorative text
  on success (empty stdout), so the machine-readable contract holds.
- **W025 extended to graph-level `verify:`.** `_check_verify_expressions` in
  `checks_contracts.py` validates the top-level `verify` list with the same
  executable-expression check as node guards: non-executable checks, invalid
  `on_fail` (rejects `retry` at graph level), and missing `check` are flagged
  offline. Folded into `check_guard_expressions` so one W025 rule covers both
  node guards and graph verify. 12 tests in `tests/unit/test_fr677_gate.py`.
- Contract tests `test_all_node_types_defined` and
  `test_registry_covers_all_compiled_types` updated to include `verify`.
  20 tests in `tests/unit/test_fr677_graph_verify.py`. Both import-linter
  contracts remain KEPT.
