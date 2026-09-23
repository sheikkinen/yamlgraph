# Feature Request: Subgraph `mode` is unvalidated — `SubgraphNodeConfig` is never applied

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-23
**First consumer / first event:** the next author who writes `mode: direct`
for a subgraph node — concretely, `sergesha` (issue #474) and anyone following
the reply posted on 2026-09-23, which promised this correction. The first
event is `yamlgraph graph lint` on a `mode: direct` graph: today it emits two
warnings advising a change the schema itself forbids.
**Research:** in-body dispositioned alternatives table (FR-889 style), below.
Every row carries a probe result executed against `origin/main` at `b84a6850`.
**Prior art:**
- [FR-1058-subgraph-runnable-config-propagation.md](FR-1058-subgraph-runnable-config-propagation.md)
  — fixed `mode: direct` *execution*; explicitly recorded this documentation and
  linter gap as out of frozen scope (S-1, S-5). This FR is that deferred work,
  plus the root cause neither was traced to.
- [FR-081-copilot-node.md](FR-081-copilot-node.md) — argues the codebase uses a
  single `NodeConfig` for all node types, with "the sole exception ...
  `SubgraphNodeConfig`". That exception is the claim this FR falsifies: the
  class exists but is never applied, so the stated pattern is in fact universal.
- [FR-716-preemptive-module-splits.md](FR-716-preemptive-module-splits.md) —
  moved `SubgraphNodeConfig` into `node_schema.py`. A relocation, not a wiring;
  the class was already unreferenced by the load path before and after.
- [FR-797-subgraph-interrupt-propagation-langgraph-1x.md](FR-797-subgraph-interrupt-propagation-langgraph-1x.md)
  — added `interrupt_output_mapping` as a `SubgraphNodeConfig` field. Same
  pattern: a field declared on a model that no graph YAML is ever checked
  against. Distinguished: FR-797 changed relay behaviour, not validation.
- [FR-210-subgraph-interrupt-state-commit.md](FR-210-subgraph-interrupt-state-commit.md)
  — proposed adding `response_key`/`resume_key` to `SubgraphNodeConfig`,
  reasoning from `extra="allow"`. Distinguished: it assumed the model gates
  graph YAML. It does not.

## Summary

`SubgraphNodeConfig` declares `mode: Literal["invoke", "direct"]` and a
validator rejecting `mode: direct` combined with input/output mappings. Neither
rule can ever fire on a real graph: `GraphConfigSchema.nodes` is typed
`dict[str, NodeConfig]`, and `NodeConfig.mode` is `str | None`. Nothing in the
load, validate, or compile path ever constructs a `SubgraphNodeConfig`.

The consequences are a silent fallback and a self-contradicting toolchain.

## Value Statement

Graph authors get an error at `validate` time for a misspelled or unsupported
subgraph `mode`, instead of a silently mis-executed graph, and stop receiving
linter advice that the schema forbids.

## Problem

### 1. Any unknown `mode` silently degrades to `invoke`

Probed via `create_subgraph_node` (`origin/main` @ `b84a6850`):

```
mode='direct'      -> CompiledStateGraph
mode='invoke'      -> function
mode='stream'      -> function
mode='bogus-typo'  -> function
```

`mode: bogus-typo` produces no error, no warning, and a working graph with
different semantics than the author asked for. This is the silent-fallback
prohibition in Commandment 6: *a plausible wrong answer is harder to catch than
a crash.* The author who typed `direct` and mistyped it gets `invoke`, which
maps state through mappings instead of sharing the schema — a different
program, reported as success.

`yamlgraph graph validate` returns exit 0 for all four. So does
`yamlgraph graph run`.

### 2. The documented mode does not exist

[reference/graph-yaml.md](../reference/graph-yaml.md) line 879:

| `mode` | `string` | No | `invoke` (default) or `stream` |

`stream` is not implemented anywhere; it lands on the plain-invoke path. The
mode that *does* exist, `direct` — the subject of issue #474 — is documented
nowhere in that reference. A reader following the table writes the one value
that is meaningless and cannot discover the one that works.

Note this row is not merely stale: because validation is unwired, `mode:
stream` *appears to work*, so the documentation is self-consistently wrong.
Nothing in the system can contradict it today.

### 3. The linter recommends what the validator forbids

Three probes on one graph (`mode: direct`, no mappings → then with mappings):

| Probe | Result |
|---|---|
| `yamlgraph graph lint` on `mode: direct` | `W501` + `W502`: "missing input_mapping" / "missing output_mapping", with a `fix:` telling you to add them |
| `SubgraphNodeConfig(mode="direct", input_mapping={...})` | `ValidationError: mode=direct does not support input/output mappings` |
| `yamlgraph graph validate` on `direct` **with** mappings | exit 0 — accepted |
| `yamlgraph graph run` on `direct` **with** mappings | exit 0 — `phase: complete` |

The linter tells the author to add exactly the keys the schema would reject,
and the shipping path ignores both verdicts.
[yamlgraph/linter/patterns/subgraph.py](../yamlgraph/linter/patterns/subgraph.py)
emits W501/W502 with no `mode` condition, while
[yamlgraph/node_factory/subgraph_nodes.py](../yamlgraph/node_factory/subgraph_nodes.py)
returns the compiled child before either mapping is read.

### Root cause

One cause, three symptoms: `SubgraphNodeConfig` is dead code that reads as live
doctrine. `grep` finds it only in tests that instantiate it directly, a vulture
whitelist, and re-exports. The tests pass and prove nothing about graph YAML —
the `mirror_test` trap from the FR-1058 diary, at schema scope.

## Ideal Result

A subgraph node's `mode` is validated at the same boundary every other graph
field is, so an unsupported value fails `yamlgraph graph validate` with a
message naming the supported values. The reference table lists exactly the
modes the schema accepts, and the linter's mapping advice is silent for modes
that do not read mappings. No second validation mechanism is introduced: the
rules already written in `SubgraphNodeConfig` simply become reachable.

## Proposed Solution

Minimal path back from the ideal: **make the existing model reachable**, rather
than re-implementing its rules in a new place.

Dispatch subgraph nodes to `SubgraphNodeConfig` during `GraphConfigSchema`
validation, so the already-written `Literal` and `validate_config` rules fire:

```yaml
# now an error at `yamlgraph graph validate`, not a silent fallback
nodes:
  child:
    type: subgraph
    graph: child.yaml
    mode: stream        # ValidationError: unsupported mode 'stream'
```

Then, as direct consequences of that wiring:

1. Correct the `mode` row in `reference/graph-yaml.md` to `invoke` (default) or
   `direct`, and document what `direct` means (shared state schema; mappings
   not accepted).
2. Gate `W501`/`W502` in `linter/patterns/subgraph.py` on `mode != "direct"`.

## Acceptance Criteria

- [ ] AC-01 `yamlgraph graph validate` exits non-zero for a subgraph node with
      `mode: stream` and for `mode: bogus-typo`; the message names `invoke` and
      `direct`. **Method clause:** assert through the CLI entry point, not by
      constructing `SubgraphNodeConfig` directly — a test that instantiates the
      model cannot observe whether it is wired.
- [ ] AC-02 `yamlgraph graph validate` exits non-zero for `mode: direct`
      declared together with `input_mapping` or `output_mapping`.
- [ ] AC-03 `mode: invoke`, `mode: direct`, and an omitted `mode` continue to
      validate and run; the FR-1058 fixtures in
      `tests/fixtures/subgraph_direct_fr1058/` still pass unchanged.
- [ ] AC-04 `yamlgraph graph lint` emits no `W501`/`W502` for a `mode: direct`
      node, and still emits both for a `mode: invoke` node missing mappings.
- [ ] AC-05 `reference/graph-yaml.md` documents `invoke` and `direct` and no
      longer mentions `stream`. **Method clause:** a test asserts the reference
      table's mode values equal the schema's `Literal` members, so the two
      cannot drift again.
- [ ] AC-06 Tests added, tagged `@pytest.mark.req("REQ-YG-685")`, each
      condemning its defect on unfixed code before the fix lands.
- [ ] AC-07 `python scripts/req_coverage.py --strict` exits 0.

## Alternatives Considered

Each row states a probe executed at `b84a6850`, not a prediction.

| # | Alternative | Probe | Disposition |
|---|---|---|---|
| A1 | Add a linter rule (e.g. `E503 unknown mode`) instead of wiring the schema | `yamlgraph graph run` on `mode: bogus-typo` → exit 0, `phase: complete`. Lint is not on the `run` path | **Rejected.** Lint is advisory; the defect is a silent *execution* fallback. A warning that `run` ignores repeats `detection_without_enforcement`. |
| A2 | Delete `SubgraphNodeConfig` as dead code | `grep -rn SubgraphNodeConfig` → 43 hits across 13 files, incl. `test_subgraph.py` (12 assertions), `test_fr721_literal_seeds.py`, ARCHITECTURE.md REQ-YG-544, CAP-201 | **Rejected.** The rules it encodes are correct and wanted; only the wiring is missing. Deleting discards two working validators to fix a routing gap. |
| A3 | Re-implement the mode check inline in `create_subgraph_node` | `subgraph_nodes.py:191` already branches on `mode`; adding a raise there is ~3 lines | **Rejected.** Moves validation from the config boundary to the compile boundary, and leaves `SubgraphNodeConfig` still dead — `the_one_law`: normalize where external data enters. |
| A4 | Fix only the documentation row (the original S-1 scope) | Probe that killed it: `mode: stream` **validates and runs clean**, exit 0 | **Rejected.** I filed S-1 believing `stream` was "schema-rejected". The first probe falsified that. Fixing the prose would leave the silent fallback and the linter contradiction in place and make the docs the only thing standing between an author and a mis-executed graph. |
| A5 | Widen `NodeConfig.mode` to the `Literal` instead of dispatching | `NodeConfig.mode` is shared: `grep` shows `mode` also used by other node types | **Rejected.** Would impose subgraph-only values on every node type. |

## Related

- GitHub issue #474 (`sergesha`) and the reply posted 2026-09-23, which states
  this gap was "filed separately" — this FR discharges that statement.
- PR #673 (FR-1058) — the review that deferred S-1/S-5.
- `yamlgraph/models/node_schema.py` — `SubgraphNodeConfig` (L21), `NodeConfig.mode` (L214)
- `yamlgraph/models/graph_schema.py:149` — `GraphConfigSchema.model_validate`, the live boundary
- `yamlgraph/linter/patterns/subgraph.py:65-83` — W501/W502
- CAP-01 config loading & validation; new requirement REQ-YG-685

## Out of scope

- **S-4** (FR-1058): invoke-mode non-relay children compile without a
  checkpointer. A durability defect on a different path; needs its own FR.
- **S-2 / S-3** (FR-1058): `examples/demos/subgraph-direct/` and a direct-mode
  interrupt demo. Demos, not validation.
- Any new subgraph mode. This FR makes the existing two enforceable; it does
  not propose `stream`.

## Judgement (date)

**Verdict:** pending
