# Diary — 2026-06-20 — The Schema That Could Not Hold an Object

**FR-548** — DM v2 World Codex: faction/location backstory as a new outline-time stage.

## What happened

The feature request arrived already shaped like a solution: a new side-effect graph "mirroring
`character_roster.yaml`" with an inline `schema: WorldCodex` carrying `type: list[object]` and
nested `fields:`. It read fluently. The judgment could have stopped at the prose — the value thesis
(length comes from widening the funnel's *inputs*, not inflating `final_cut`'s compressed output) was
genuinely sound. But `judge_as_junior_pr` says: assume plausible code hides a subtle bug, and the
load-bearing claim here was a mechanism, so I opened the mechanism.

The mechanism did not exist. [`schema_loader.resolve_type`](../../yamlgraph/schema_loader.py) matches
`list[(\w+)]` and resolves the inner token through a `TYPE_MAP` that contains `str/int/float/bool/
dict/Any` — and **no `object`**. `type: list[object]` raises `ValueError` at load. Worse,
`build_pydantic_model` reads only `field_def["type"]` and never recurses into nested `fields:` — the
faction/location sub-schemas would be silently ignored even if `object` resolved. The graph could
not compile. And the "mirrors `character_roster`" claim was false in a second way: the roster is
`parse_json: false` + `split_roster` (plain names), no schema at all. Every DM graph that emits a
*nested* structure (`chapter_outline`, `chapter_close`, `turn`) uses `parse_json: true` with the JSON
contract written into the prompt and normalization at the Python boundary.

So I approved *with conditions* rather than rejecting (the idea was right, the mechanism wrong) and
folded five corrections into the spec before a line of test was written: C1 swap inline-schema for
`parse_json` + boundary-normalize; C2 fix the "mirrors" framing; C3 drop a dead `reviewed` flag; C4
name the real trigger (synopsis-accept after `expand_roster`, not a "between roster and chapters"
point that doesn't exist as a single call site); C5 demote the LLM-nondeterministic length claim from
a blocking test to demo-log visibility evidence. Then RED-first: five deterministic failures, then
GREEN — graph, prompt, `expand_codex`, the guarded `final_cut` block. 390 DM tests green.

## The trap

`framework_costume` at the spec layer, plus `spec_kill`. The FR dressed a feature in a capability the
framework does not have — an inline nested-object schema — because the *shape* of the existing inline
schema (`{name, fields}`) looked like it should nest. It looks recursive; it is one level deep. The
cheapest possible bug is the one that never compiles, and it was sitting in the spec, costed at
"~1.5 days," waiting to be discovered three hours into enforcement when the first `graph lint` threw
`ValueError`. Reading the FR against the loader killed it in minutes.

The second trap was quieter: C4. The FR said "sequence `expand_codex` between `expand_roster` and
`expand_chapters`." That sentence presumes the two expansions are adjacent calls. They are not —
[session.weave](../../examples/dungeon_master/api/session.py) fires `expand_roster` in the
`stage.name == "synopsis"` branch and `expand_chapters` in a *separate* `cast_complete` branch, two
`if/elif` arms triggered by different accept events. "Between A and B" is not a location when A and B
live on different events. The cure was to read what the codex actually consumes (only the synopsis)
and place it where that input lands — beside `expand_roster`, not in a fictional gap. And when I went
to make the matching edit in `generate.py` (the FR listed it as a second call site), I found
`generate.py` drives `session.accept()` — the same adapter — so the single insertion covered both
paths. The "two call sites" were one. Another phantom duplicate the prose implied and the code denied.

## What saved it

Reading three files before writing one: `schema_loader.py` (does the type system support this?),
`character_roster.yaml` vs `chapter_outline.yaml` (which is the real pattern?), and `session.weave`
(where do these expansions actually fire?). Every one of the five conditions came from a file, not
from reasoning about the FR's intent. The FR's intent was fine; its claims about the code were the
defect, and only the code can refute a claim about the code.

## The heuristic

**`spec_claims_a_capability` — when an FR specifies a mechanism ("inline nested schema," "between A
and B," "thread through X and Y"), the claim is a hypothesis about the codebase, not a fact; verify
each mechanism against the file that implements it before granting authority.** A feature's *value*
can be judged from prose; a feature's *mechanism* can only be judged from the code it presumes.
Corollary: an FR that describes itself as "mirroring X" is asserting an equivalence — open X and check
that the mirror is true at the axis that matters (here: output shape, not trigger site).

## Seed

The codex recovered the named cast from the synopsis for free; the proper-noun lexicon (FR-547)
recovered it from the prose; the roster names it explicitly. Three derivations of "who is in this
story," each scoped differently, each blind where another sees. **Should there be one `world_codex`
boundary that resolves cast, factions, and locations once at synopsis-accept — a single
named-entity authority the seams read — so the roster/cast/lexicon distinction is settled at the
entrance instead of re-discovered, one painful witness at a time?** And: how many other FRs in the
backlog specify a mechanism the framework cannot perform, costed as if it could — is there a cheap
`graph lint` pass that could be run against an FR's *proposed* YAML before it is judged, killing the
`spec_claims_a_capability` class at the plan boundary rather than the enforce boundary?
