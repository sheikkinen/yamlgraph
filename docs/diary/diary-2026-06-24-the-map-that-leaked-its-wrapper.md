# 2026-06-24 — The map that leaked its wrapper

**FR-589 enforced.** The abstraction-span metric, rejected as a Python spike under
FR-588, was rebuilt as a graph-native example and passed its separation gate on the
first scorer iteration. The interesting part was not the metric working — it was the
one bug that the judge's three pre-enforce corrections *did not* catch, and why.

## What the corrections caught, and what they couldn't

The judgement flagged three things to verify before building: the REQ-YG ID, the
nested map-item access `{state.item.text}`, and the `type: python` `state_key`
contract. All three were real, and all three I could settle by *reading code* —
`resolve_state_path` traverses dots; `python_tool` merges dict returns. Static
reads. The corrections were a map of the boundaries I could inspect without running
anything.

The bug that actually bit was on a boundary I *thought* I had read: the map node's
inner `state_key`. The judge asked me to verify the python node's state_key; I
verified it. Neither of us asked the symmetric question about the **map sub-node's**
state_key — because the map demo I used as the template (`examples/demos/map/`)
sets `state_key: expansion` on its inner node, so the convention was present but
invisible, never named as load-bearing. I copied the *shape* of the demo (map over,
as, collect) but dropped the one field that looked like boilerplate.

## The trap: invisible-because-present

`map_compiler` extracts each sub-node result with
`result.get(state_key, result)` — and the fallback `, result` is the trap. When the
inner llm node had no `state_key`, it stored under its auto-generated node name
(`_map_score_sub`), the extractor's lookup missed, and the `, result` fallback
**silently returned the whole wrapper dict** instead of raising. The bug surfaced
three nodes downstream as `Score missing level_count` — a boundary symptom for a
boundary cause, exactly the displacement the Scripture warns about. The fix was at
the entry boundary (`state_key: span` on the inner node), not a guard in the
verdict.

This is a sibling of the `downstream_fix` trap, but with a twist: the silent
fallback (`get(k, result)`) is itself a *plausible-wrong-answer* generator. It did
not crash on the malformed shape; it passed a bigger, wrong object forward. A raise
on the missing key would have pointed straight at the map node. (I will not patch
the framework here — out of FR-589 scope — but it is a seed.)

## Why the metric is allowed to be believed

The gate is the point, not the score. `assign_pre_eff` — the only prompt with a
*measured* L5 failure rate — ranked highest (span 8) without being told it was
special. The number now carries evidence: it reproduces labels drawn from a
different process (schema-shape calibration, FR-586) and from a measured failure
(FR-585). Had it not separated, the example would have shipped as a documented null
result. The discipline that made FR-588's spike worth rejecting is the same
discipline that lets FR-589's number be trusted: validate at a boundary the score
did not author.

**Heuristic:** when copying an example's *shape*, enumerate every field of the
template node and ask which are load-bearing — the boilerplate-looking one
(`state_key`) is often the contract. A silent `.get(key, whole_object)` fallback in
a fan-out/collect path will not crash; it will enlarge the payload and defer the
crash to a consumer that names a missing field.

**Seed:** should `map_compiler`'s sub-node extraction *raise* when the configured
`state_key` is absent from the result, instead of falling back to the whole wrapper
dict? The fallback turns a wiring mistake into a downstream shape error. A failing
test (`scores` collected without the inner model's fields when `state_key` is unset)
would condemn it — a candidate fix FR, separate from this example.
