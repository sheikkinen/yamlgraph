# The Leaf That Broke the Cycle

*2026-06-19 — Distill, FR-536 (DM v2 module organization, Workstream C: turn_ops split)*

## What happened

The last and largest extraction of FR-536: `turn_ops.py`, 1169 lines carrying five
concerns, split into four modules. The plan sketched a three-way split
(`turn_ops` + `chapter_open` + `scene_cast` + `final_cut_ops`). The code, read
verbatim, asked for something different — and one detail the plan never anticipated
nearly produced an import cycle.

The play loop (`invoke_turn`, `running_scene`) needs the opening-gate helpers.
The gate helpers (`enforce_lifecycle_gate`, the precedence gate) need turn and
chapter accessors (`turn_direction`, `chapter_turns`, `chapter_beats`). If those
primitives had stayed in the play module — the obvious home, since play is "where
turns happen" — then `chapter_open` would import `turn_ops` and `turn_ops` would
import `chapter_open`. A clean cycle, born of a clean-looking split.

## The trap: the obvious home creates the cycle

The intuitive partition put primitives with their busiest caller. But "busiest
caller" is the wrong sorting key when two modules both need a shared substrate. The
substrate must sink *below* both, into a leaf that imports neither. I extracted the
chapter/turn accessors into `turn_state.py` — a module that imports only
`chapter_nav` (itself a leaf from Workstream B) and is imported *by* the other
three. The dependency graph became a tree: `turn_state` <- `chapter_open` <-
{`turn_ops`, `final_cut`}.

This is the same shape FR-534 left behind (the `lifecycle_resolver` leaf that broke
the `turn_ops` lazy cycle), and FR-536 J4 named it as a goal for Workstream B. The
recurrence is the lesson: **when a split would make two siblings import each other,
the fix is never to pick a winner — it is to find the shared leaf and sink the
primitives into it.** Cycles are a sorting error, not an unavoidable cost of
cohesion.

## What I did right

I read the real source verbatim before moving a single function — all 1169 lines in
three reads — rather than reconstructing from the plan's def-cluster map. The plan's
map was a *forecast*; the code was the *territory*. `dead_character_names` straddled
the boundary between two of my reads and had to be reconciled byte-for-byte; had I
trusted memory I would have silently dropped half of it. The cost of re-reading is
linear; the cost of a reconstructed-from-memory function is a debugging session that
looks like a logic bug but is actually an amputation.

I also let the migration, not a facade, carry the decoupling. Every consumer moved
to the new home; `git grep` for `turn_ops.<moved-symbol>` returns empty. The one
survivor — the `_state_map_*` identity re-exports — stayed only because a test
asserts on object identity, the exact exemption the Judgement pre-authorized. No
re-export hub, no compat shim: the emptied module references none of what left it.

## The smaller trap: the test double patches the old address

`test_final_cut_revise_cycle.py` monkeypatched `turn_ops.invoke_final_cut`. After
the move, `invoke_final_cut` lives in `final_cut`, and the consumer
(`chapter_ops.close_chapter`) resolves it by module attribute on `final_cut`. The
patch silently no-op'd — it set an attribute on the module the call no longer reads.
Three tests went red with `AttributeError`, which was the *honest* failure; a
re-export facade would have made them pass while patching a dead address. The
lesson: **a monkeypatch is coupled to the symbol's module home, not its name. When
you move a symbol, every `setattr(old_module, name, ...)` is a dangling reference
the type checker cannot see** — only the test run finds it. The red was the gift.

## Seed

`turn_state` is a leaf today because nothing in the split imports back up into it.
But leaves attract gravity: the next contributor who needs "just one accessor" will
be tempted to add a helper that reaches into `chapter_open` for context, quietly
re-introducing the cycle from below. What enforces leaf-ness over time — is there a
cheap import-linter contract that could pin `turn_state` as a sink (may be imported,
may not import siblings), the way the three-layer contract pins the package, so the
cycle cannot grow back under deadline pressure?
