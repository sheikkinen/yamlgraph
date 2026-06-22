# The router that wasn't a router

**Date:** 2026-06-22
**FR:** FR-563 (DM v3 M4a -- author & attach, activate the plot lane)

## What happened

M4a's job was small on paper: let an LLM author a `PlotPlan`, validate it, and
attach it. The plan I inherited from the design's §6a sketched it the obvious way --
a `type: tool` validate node, a `type: router` node keyed on `condition:
"validation.ok"`, routes `true -> done / false -> repair`. Every piece of that
sketch was a plausible lie about how the framework actually behaves, and the only
way to find out was to read the as-built node factory instead of the design doc.

## The trap: the node type has a hidden output contract

A `type: tool` node does not put its return value where you wrote it. It wraps the
return as `{task_id, tool, success, result, error}`. So `validation.ok` -- the
field the router was supposed to read -- would actually live at
`validation.result.ok`, and the condition would resolve to "missing" and route the
same direction forever. The symptom would not be a crash; it would be a repair loop
that never repairs, or a graph that always exits as if valid. A plausible-wrong
answer, exactly the class Commandment 6 warns about, hidden one indirection deep.

The fix was to stop trusting the node-type label and read what each one *merges
into state*. A `python` node merges a returned DICT at the state TOP level (only a
non-dict return goes under `state_key`). So the validator function returns
`{"validation": {"ok", "flaws"}}` and `state["validation"]` is exactly the dict the
edges read. No `state_key`, no wrapper, no `.result.` indirection.

## The second lie: "router" does not mean "route"

`type: router` in this framework is an LLM classifier -- it calls a model and keys
on a schema `route_field`. It is the wrong tool for a deterministic boolean. And
`evaluate_condition` refuses a bare `validation.ok`: it REQUIRES a comparison
operator, so the truth lives in `validation.ok == true` on a plain conditional
EDGE, not in a router node at all. The five-whys and reflexion demos already
encode this pattern -- conditional edges plus `loop_limits`/`loop_exits` for the
bounded cycle. The honest move was to copy the working demo, not the design sketch.

## Evidence over assertion

I did not assert the routing worked. The two routing tests inject `plan_raw`
directly and call `plot_validate_plan` with no live LLM, then assert
`evaluate_condition("validation.ok == true", state)` fires for the valid plan and
`== false` for the `world_revival_variant`. The graph itself is exercised by
`lint_graph` asserting zero error-severity issues. The seam-activation test proves
the payoff end to end through the public surface: before `write_plot_plan`, ch3
does not exclude Arnulf; after, it does -- the FR-560 director comes alive.

## Heuristic

A design doc describes intent; the node factory describes behavior. When a graph
routes on a computed value, do not trust the node-type name -- trace where that
node's return actually lands in state (top-level merge vs `state_key` vs tool
wrapper) and confirm the condition's path against a real `evaluate_condition` call.
The cheapest version of this bug is a route that silently never fires; pin it with
a no-LLM routing test before writing the graph, not after.

**Seed:** The three node types here (`tool`, `python`, `router`) each have a
distinct, undocumented contract for *where their output lands*. Could the linter
grow a check that, given an edge `condition` referencing `X.y`, verifies some
upstream node actually produces `X.y` at the state path that condition reads --
turning this whole class of silent-misroute into a lint error?
