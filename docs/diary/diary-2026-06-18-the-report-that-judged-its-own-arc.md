# 2026-06-18 — The report that judged its own arc

FR-531 was the cheapest FR of the FR-506→527 continuity arc to build and the most
uncomfortable to read. It is a pure aggregator: no LLM, no new measurement, just six
deterministic witnesses summed into one per-book row. Half a day of plumbing. And the
first time it ran over the real corpus it said, plainly, what a season of seam-hardening
work had not: the aggregate did not move. Inside the em-dash floodmark premise the
`wasted_turns` column climbs 14 → 23 → 26 → 34 across consecutive books. We had added
detectors, not improvements.

## The trap: measurement mistaken for progress

The arc had the `detection_without_enforcement` shape and I could not see it, because every
individual witness was green-by-construction — each scan reported *its* number, and no two
numbers ever sat in the same table. The instrument shelf grew to six scripts and the
program "measured a lot and never showed a trend" (continuity-issues §5.5, written before I
believed it). The cure was embarrassingly small: put the columns next to each other and
sort by slot. The regression was always there; the absence of a single view was the only
thing hiding it.

Heuristic: **a metric with no neighbour cannot regress.** A witness that only ever prints
its own scalar manufactures the illusion of control. The first obligation of an instrument
shelf is not another instrument — it is the one table that forces the instruments to
disagree with each other in public.

## The load-bearing correction: trend is premise-relative

J2 froze the only constraint that mattered: the corpus mixes premises, so a naive
slot-ordered delta would subtract a floodmark book from a Lolita book and print a number
that means nothing. `premise_of` keys on the exact `tagline`, and the delta column only
ever compares same-premise neighbours. The smoke run vindicated this immediately — the
exact-string grouping split the *hyphen* floodmark from the *em-dash* floodmark into
separate sections, and only then did the hyphen group's real `seam_gaps 2 → 1 → 0`
improvement become legible as improvement rather than noise. A mis-scoped trend is strictly
worse than no trend, because it is a false trend wearing a number's authority.

## The quieter win: no-duplication by extraction

`book_turn_waste` had lived only inside `scan_turn_waste.py`. The tempting path was to
import the script; the honest path was to promote the measurement into `witness_metrics.py`
and let both the script and the report import the one implementation. `completed_chapters`
went the same way — reuse `parse_story_progress_metrics`, the established
chapter-completion witness, rather than count `text` fields myself. The aggregator earns
the right to call itself "no new measurement" only if every column traces to a witness that
already existed.

And the report closed the loop on its sibling FR-528: 10025-BC's recorded epilogue beat
shows up as `unplayable_beats = 1` — the exact pathology the FR-528 outline gate now
prevents from ever being authored again. The deterministic shelf can see the thing the gate
was built to stop, which is how you know the gate guards a real boundary and not a
hypothetical one.

**Seed:** the report shows the arc did not move the aggregate — so the next FR should not be
another detector. If `wasted_turns` is the column that regressed, the leverage is at the
turn-budget boundary (the director's `scene_complete` decision), not at the synopsis or the
outline. Could the report itself rank the open gaps by *which column they touch and how much
that column has drifted*, so prioritization stops being a matter of taste? The instrument
that proves the arc stalled is the same instrument that should name what to fix next.
