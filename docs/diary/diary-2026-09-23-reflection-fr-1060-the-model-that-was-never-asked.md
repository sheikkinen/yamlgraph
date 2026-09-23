# The model that was never asked

**FR-1060** — `SubgraphNodeConfig` has existed for a long time. It declares
`mode: Literal["invoke", "direct"]` and refuses `mode: direct` combined with
`input_mapping`/`output_mapping`. Thirteen files reference it. Forty-three
grep hits. Every one of them is a test constructing the model directly, a
re-export, a vulture whitelist line, or prose in `ARCHITECTURE.md` describing
what it enforces.

Not one of them was a graph.

`GraphConfigSchema.nodes` is typed `dict[str, NodeConfig]`, and
`NodeConfig.mode` is `str | None`. So `mode: stream` validated. `mode:
bogus-typo` validated. Both ran to completion on the invoke path, silently.
Meanwhile the linter emitted two warnings against `mode: direct` advising the
author to add exactly the mappings the model rejects — a three-way
contradiction between linter, schema, and runtime, each internally consistent.

## The trap

This is `mirror_test` at schema scope, and the Scripture already names its
cure under a different heading: `gate_checks_shape_not_substance`. The
July 2026 diary for FR-673 records the identical discovery — "the Pydantic
schema existed but was only called from CLI validate/lint, not from the load
path. The gate existed but wasn't in the critical path." That fix wired
`validate_graph_schema()` into `validate_config()`.

It wired the *graph* schema into the load path. It did not ask whether the
*node* schemas were reachable from the graph schema. A gate moved into the
critical path can still be a gate that asks the wrong model.

The tell is cheap and I did not look for it: **a model whose only callers are
its own tests is not installed, it is displayed.** `SubgraphNodeConfig` had
100% test coverage of rules that governed nothing.

## The second boundary, found only by running

I wired `SubgraphNodeConfig` into `GraphConfigSchema` and the RED suite went
from 7 failures to 4. `graph run` rejected the bad mode. `graph validate`
still printed `VALID`.

`cmd_graph_validate` does not consult the Pydantic schema at all. It parses
YAML and runs its own hand-written field checks — a third independent opinion
about what a graph is. I had assumed "the schema boundary" was singular
because the FR said so and the judgement froze it that way. Author, judge, and
frozen scope all carried the same premise; three documents agreeing is one
observation.

Only executing the shipped entry point discriminated. The unit suite would
have gone fully green against a `validate` command that still lied, had I
written the tests one layer lower.

## Heuristic

> **Count the non-test callers of every validating model.** Zero means the
> rules are decorative regardless of coverage. One means check whether the
> other consumers of the same artifact reached it too — a schema with two
> independent readers has two chances to drift, and the one that does not
> consult the model is invisible to every test that does.

The fix follows: `check_subgraph_node()` is the single route into
`SubgraphNodeConfig`, taken by both the graph schema and the CLI. Not because
sharing is tidy, but because a second site would have been a second opinion,
and the defect *was* a second opinion.

## Seed

The repo has a `req_coverage --strict` gate that fails on phantom REQ IDs —
requirements claimed by tests but registered nowhere. It caught R-1 mid-commit
and it caught it mechanically.

**Seed:** What is the equivalent gate for phantom *enforcement*? A check that
enumerates every Pydantic model under `yamlgraph/models/` carrying a
`model_validator`, resolves its callers, and fails when the only ones live
under `tests/`. `req_coverage` asks "is this claimed requirement real?";
nothing yet asks "is this real rule reachable?" Both are the same question
about the gap between a registry and a runtime — and this repo already knows
how to ask one of them.
