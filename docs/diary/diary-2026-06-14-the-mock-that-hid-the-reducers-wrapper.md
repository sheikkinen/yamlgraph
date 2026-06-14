# The Mock That Hid the Reducer's Wrapper

*Diary — 2026-06-14 — FR-487 DM v2 full-text walkthrough (the rendered finish)*

## What happened

FR-487 was the convergence the whole DM finish arc had been building toward: take
the FR-485 cut spine (what happens, and the emphasis), the FR-486 performance
(the spoken line, the visible tell, the acted intent), add a director-staging pass
(the place), and render the full text of each turn — the scene as it would be
*performed*, not summarised. The architectural gift the Judge underlined held in
practice: **alignment composed for free.** The cut is 1:1 to the played turns, so
the walkthrough is turn-aligned by construction, and the same `validate_cut_turns`
post-condition guarded it with no new code. That part was boring, which meant the
Judgement was good.

Two things were not boring, and both were caught by the *live witness*, not the
unit tests.

## The trap: the mock hid a real boundary shape

The per-turn render is a `map` node whose sub-prompt returns a plain string
(`parse_json: false`). My mock returned clean strings, the five unit tests went
green, ruff was clean, graph-lint was clean. By every gate I had, FR-487 was done.

Then the live witness printed this into the rendered prose:

```
{'_map_index': 2, 'value': 'Kara pins Tarek flat against the wet limestone wall…'}
```

The `map` compiler, when collecting a string sub-result, wraps each item as
`{"_map_index": i, "value": <text>}` for ordering — and the collected list order
is *not* guaranteed. My code did `clean_text(r)` on each item, which `str()`'d the
whole wrapper dict into the page. The unit tests passed **anyway**, because the
substring assertions (`"Hold the ledge" in text`) survived the dict repr — the
needle was still in the haystack, just wrapped in reducer bookkeeping.

This is the `demo_vs_test` law with teeth: *tests prove constraints; the live run
proves the abstraction is worth having.* The mock asserted the shape I expected,
not the shape the framework actually produces at a `parse_json: false` map
boundary. A mock is a hypothesis about the boundary; only the real provider
falsifies it.

The cure was a boundary normalizer (`_ordered_render_texts`: sort by `_map_index`,
unwrap `value`) **plus** a regression assertion the mock can no longer satisfy
falsely: `"_map_index" not in resp.text`. Normalize at the boundary where the
reducer's data enters my code, not downstream where the wrapper manifests on the
page.

## The second finding: "emphasis rides on the spine" was a half-truth

The Judge bound that the climax turn must be the heaviest passage. The FR's theory
was that the cut spine already carries global emphasis, so the local per-turn
render inherits it. The first live run falsified this too: all three passages came
out ~90–108 words, and Turn 1 (the most setup) was accidentally the longest. The
local render had *no climax signal* — the prompt said "if this is the climax turn,
write it heaviest" but the bundle never told it *which* turn was the climax. Theory
said the emphasis rides on the spine; reality said a uniform spine carries no
emphasis to ride. Fixed by passing an explicit per-bundle `climax` boolean (from
`climax_turn(doc)`, the same marker FR-484 already derives) — after which Turn 3
rendered at 170 words against 94/93, and the seam between Turn 2's close and Turn
3's open read as one continuous confrontation.

## The honest core held

Every layer the walkthrough renders was authored upstream; the render composed and
invented nothing, and the private `thinking` was dropped at the assembly boundary
(not trusted to be omitted by a well-behaved prompt). Dropping it in code, at the
seam, is the same move as FR-486's seam-freeze: make the privacy a property of the
data handed to the model, not a hope about the model's behaviour.

## Seed

Both real defects here were invisible to a green mock and visible only to the live
run. Could the DM prototype grow a *single* recorded live-witness fixture per
finish (one captured real `{setting, turns}` per FR) that a fast test replays —
turning each witness from a one-shot manual log quote into a standing regression
asset? The mock proves the wiring; the captured witness would prove the boundary
shape. Where else am I trusting a mock to model a framework boundary I have never
actually observed — the `map` reducer wrapper was one; how many more `parse_json:
false` collect sites in the wider codebase quietly `str()` a wrapper dict?
