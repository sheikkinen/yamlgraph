# The Stage That Was Never Declared — 2026-06-07

## What happened

FR-475 reshaped the DM v2 preplan from a linear chain (`synopsis → plot`) into a
tree: the synopsis (root) gates a static **Key Scene** leaf and a **Characters**
branch that spawns *one card per character* — an unbounded, synopsis-derived set —
all navigated by a breadcrumb that became the only selector. The synopsis loop,
`weave/edit/accept`, and auto-draft-on-entry (FR-474's `cursor_is_not_artifact`
cure) all carried over unchanged. Eleven walkthrough tests, green.

Two things resisted the existing shape, and both were instructive.

## The cursor namespace became the data structure

`STAGES` is a frozen tuple — it can hold `synopsis`, `key_scene`, and the
`characters` group, but it *cannot* hold the characters themselves: their count and
names are not known until the roster graph runs against an accepted synopsis. The
temptation was to mutate `STAGES` (or build a parallel registry) as cards spawn.
Instead the **cursor string** carries identity: a card is addressed `char:<slug>`,
and `resolve_stage` *synthesizes* a `Stage` on demand for any `char:` cursor —
label = the card's name, graph = the one shared `character.yaml`, `var_name` = the
name to inject. The static registry owns the fixed skeleton; the prefix-encoded
cursor owns the dynamic leaves.

The payoff was that everything downstream — `_entry`, `_autodraft`, `navigate`,
`breadcrumb`, `_can_visit` — calls `resolve_stage` and never asks "is this a real,
declared stage or a synthesized one?" The two resolution paths (registry lookup vs.
synthetic construction) unify behind one function, so the dynamic case is invisible
to every consumer. A `Stage` that was never declared behaves exactly like one that
was.

## The linter caught a stage wearing a costume it didn't need

I built `character_roster.yaml` by copying the stage template — `state: synopsis,
draft, instruction, roster` and a node that maps all four into the prompt. `graph
lint` warned: `draft` and `instruction` are declared but never referenced. They
weren't bugs; they were **vestigial channels**, carried over by pattern inertia from
the uniform weave/edit/accept stage. But the roster is not that kind of stage. It is
not a card the DM weaves and accepts — it is a *pure derivation*: `synopsis → names`,
run once on synopsis-accept, never visited (`kind="roster"`, rejected by
`_can_visit`). The honest channel set is `synopsis → roster`, nothing else.

The tell was the lint warning, but the deeper signal was conceptual: "Characters" is
a non-visitable group that renders no card. It wears `Stage`'s shape so the registry
can hold it, but it is not a stage in the experiential sense. The costume was load-
bearing for *structure* (it needs a parent, a label, a graph) and dead weight for
*behavior* (it has no draft, no accept, no card). Trimming the vestigial channels
made the graph say what it is.

## Heuristic

> **`prefix_namespace_over_registry`** — When a fixed skeleton must host an unbounded,
> runtime-derived set of peers, don't grow the static registry. Encode identity in the
> cursor (a `kind:<id>` prefix) and synthesize the registry entry on demand behind the
> *same* resolver the static entries use. The dynamic case stays invisible to every
> consumer, and "declared" vs. "synthesized" stops being a branch anyone has to write.

> **`costume_channels`** (corollary to Scripture's `framework_costume`) — A node copied
> from a uniform template inherits channels it doesn't use. The linter's "declared but
> unreferenced" warning is not noise; it is the template's costume showing through.
> Trim to the channels the node actually reads — the honest channel set names what the
> node *is*.

## Seed

The `characters` group is a `Stage` that holds structure but no behavior; the
`char:<id>` cards are behavior synthesized without a declaration. We now have two
half-stages on either side of one dataclass. **Is `Stage` actually two types wearing
one name** — a *PlaceInTheTree* (parent, label, visitability) and a *Producer*
(graph, seed, var_name, output_key) — and would splitting them let a group be a pure
place while a card is a pure producer, with no vestigial fields on either?
