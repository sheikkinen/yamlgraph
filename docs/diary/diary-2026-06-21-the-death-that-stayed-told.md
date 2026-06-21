# The Death That Stayed Told

*2026-06-21 — FR-560, DM v3 M1 belief lane: graduate api/plot, projection, grounding, live seam*

## What happened

FR-559's M0 spike proved a classical planner could carry the floodmark distinction (world-truth
alive, clan *believes* dead) with belief reified as a plain boolean fluent. FR-560 graduated that
throwaway into a real `examples/dungeon_master/api/plot/` package and added the three things M1 is
for: pure projections (`chapter_cast`/`exclusion_set`/`protected_set`), an ungrounded-reveal
grounding check, and a live, plan-optional exclusion seam wired into `compile_opening_onepager`.

The Judge approved with four conditions, three blocking. None were nitpicks — each pinned a place
where the single floodmark fixture *hid* a contract gap because, for it, every value is the
identity.

## The trap

**`false_duplicate` by fixture identity.** The floodmark plan is a beautiful demo and a treacherous
test: its character ids equal their display names, its chapter ordinals equal their cid strings,
and its only presumed-dead observer is a single clan. So the seam I was about to write —
`exclusion_set(plan, chapter: int)` unioned into a `must_exclude: list[str]` keyed by `cid: str` —
would have *passed every floodmark assertion* while silently keying the plan at the wrong chapter
for any real book, or unioning an id where a display name was expected. Two impedance mismatches,
both invisible under the identity fixture. The Judge (J3) named both before I wrote a line: pin the
`cid -> ordinal` bridge (`_chapter_index`, already living in `chapter_open`) and assert it with a
doc whose `chapters.order` makes the bridge do real work; scope `id == display_name` explicitly and
freeze it in the docstring rather than let the mapping be a hidden `plausible_wrong_answer`.

The second trap was **`detection_without_enforcement` in the spec itself (J2).** The grounding
section described *two* behaviours — ungrounded reveal, and an "unclosed belief gap when G demands
it" — but only the first had a witness test. The cheapest fix was the Purge: cut branch (b)
entirely. M1's check is *sharper* as ungrounded-reveal-only, and belief-side closure is M3-adjacent.
A production branch with no condemning test is exactly the speculative surface the doctrine deletes.

## The cure

**Normalize at the boundary, and let the boundary be the seam.** The two bridges (`cid -> ordinal`,
`id -> display name`) are impedance mismatches *at the seam between the typed plot island and the v2
prose path* — so I pinned them there: the union happens inside `compile_opening_onepager`, before
the existing `[:12]` truncation, through the one typed read (`chapter_nav.attached_plot_plan`), and
the characterization test proves the function is byte-identical when no plan is attached. The seam
is a strangler-fig: it can *add* an exclusion the reconstruction missed, never *remove* a v2
constraint. The island stays a leaf (`chapter_open -> api.plot`, never the reverse), enforced by
review because `api/plot/` sits outside import-linter's `root_package = yamlgraph` — a gate I was
careful *not* to claim would run (J4a). I also made the `world_revival` fixture clear its reveal's
belief effect, so it stays a *pure* lifecycle case and doesn't accidentally trip the new grounding
check — keeping each regression fixture a single-axis witness.

The non-circular `exclusion_set` rule was the keystone: the v2 phrasing ("believed-dead by every
onstage observer") made exclusion depend on the cast, which the exclusion is supposed to *shape* —
a latent circularity. The pinned rule reads only the belief timeline: *X is excluded at chapter c
iff the latest belief beat about alive(X) at chapter <= c sets held=False for some observer and no
reveal restores it at chapter <= c.* The inclusive `<= c` is load-bearing: it is exactly why the
reveal at ch6 releases Arnulf *at* ch6, not the chapter after.

## Seed

The grounding check is ungrounded-reveal-only because that is the one branch with a witness. But
the cut branch — "a belief gap G demands but no beat closes" — is the *belief-side* twin of the
affect-closure check coming in M3. When two milestones each carry half of a symmetric invariant
(belief closure now, affect closure later), is there a single "open/close ledger" abstraction that
would let both lanes share one checker, or does forcing them together re-introduce the coupling the
leaf island exists to prevent?
