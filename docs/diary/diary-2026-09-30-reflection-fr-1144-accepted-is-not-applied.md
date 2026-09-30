# Reflection: FR-1144 — accepted is not applied

**Date:** 2026-09-30
**FR:** FR-1144 (race nodes honour `thinking_budget`)

## What happened

The bug was one missing keyword argument. `NodeConfig` accepts
`thinking_budget` on every node type. The `llm` node factory reads it.
The race node factory never did. An author who wrote
`thinking_budget: 0` on a race node got no lint warning and no runtime
error, and Gemini kept thinking for about 4 s per call. The only symptom
was latency, and a latency race takes a slow candidate in its stride by
design. So the race hid its own defect: the hedge quietly became a
single-provider call.

The fix was 6 lines. Three smaller things were worth noticing:

1. **The size gate shaped the code.** `race_node.py` was 447 lines
   against a hard limit of 450. The `temperature`-style three-line lookup
   plus a wrapped call site came to 452. I wrote the lookup as a walrus
   with a short local name and recorded the deviation in the FR, rather
   than trimming unrelated lines. That is the right call inside frozen
   scope. But a file at 99.3 % of its budget will turn the next small fix
   into this kind of contortion.
2. **`scripts/worktree.sh new` branches from local `main`, not
   `origin/main`.** The first worktree lacked the just-merged FR, and
   `--prefix fix` without a slash produced `fixfr1144-…`. Both were caught
   by `ls` and `git log` before any write, and fixed with a rebase of an
   empty branch.
3. **The pre-command guard matches the substring `pytest` in any
   command.** Grepping `tests/unit/test_router_race.py` through `| head`
   was denied. The guard protects the right thing, but I spent two tool
   calls learning that its match is lexical.

## Trap

`accepted_is_not_applied`: a schema that validates a field proves the
field is *allowed*, not that anything *reads* it. Validation success is
the signal an author trusts, so a validated-but-ignored field is
worse than an unknown field, which would at least fail loudly.

## Heuristic

For every field a node schema accepts, name the factory line that
consumes it for each node type that accepts it. A field with no
consumer on some node type should either be rejected at lint for that
type or wired through. A silent no-op is never acceptable.

**Seed:** Which other `NodeConfig` fields are accepted on node types
whose factories never read them? A one-pass census could cross
`NodeConfig` fields × node types against `node_config.get("<field>")` /
`cfg.<field>` reads in `yamlgraph/node_factory/`. Each empty cell is a
candidate FR-1144 twin. `max_tokens` on race is already one: the schema
accepts it (`node_schema.py:159`), `llm_nodes.py:159` reads it, and
`race_node.py` never mentions it.
