# The Final Cut That Only Stitched

*2026-06-14 — DM v2, tracing detail provenance through the pipeline*

## The question, and the number that answered it

The user asked the plain comparative question: between the Key Scene (the plan)
and the Final Cut (the render), is detail *lost* or *gained*? The surface answer is
flattering — 210 words of scene sheet become 427 words of continuous prose, every
one of the twelve beats survives, no event is dropped. A clean 2× amplification.

But the surface answer hides *where* the amplification happened. I traced the
provenance by vocabulary overlap, and the numbers relocated the credit entirely:

- Final Cut vocabulary covered by the **seven turn recaps: 78%**
- Final Cut vocabulary covered by the **Key Scene: 23%**
- Final Cut word count (427) ≈ **sum of the recaps (435)**

The Final Cut is a near-verbatim **stitch of the played turns**, not an
amplification of the scene sheet. The detail expansion — Freya's whole
choreography, an emergent second knife exchange ("ducks beneath the blade"), the
defiant "spits bloody saliva" coda — was all born **turn-by-turn in the play
loop** and carried up faithfully. The cut step added only connective tissue ("In
response…", "Even as his broken knee buckles…") that smooths the seams between
turns. Tokens like `crouch`, `spits`, `penetrat`, `duck` are absent from the Key
Scene, present in both recaps and Final Cut: born in play, not at the cut.

## The trap I had been standing in

FR-484 justified the Final Cut as the place that adds *dramatic weight* — the one
point where the whole arc is visible and emphasis can be allocated. In my
evaluation two exchanges ago I had even praised it for exactly this, citing the
climax passage's character count. But on *this* artifact the continuous Final Cut
added **volume parity and continuity, not new detail and not visible
re-weighting**: it is ~1:1 with the recaps it concatenates. I had attributed to the
cut a value the **play loop** was actually producing.

This is the length-as-proxy trap from the fifty-call entry, but caught from the
other side. There I worried length couldn't prove *craft*; here length actively
*misattributed* craft — the doubling Key Scene → Final Cut looked like the cut's
achievement, when 78% of it was the turns' achievement merely relocated. The honest
unit of measurement is not "how big did it get" but **"at which seam did the new
detail first appear."** Provenance, not size.

## What this confirms about the architecture

The seams divide cleanly by function, and the division matches the long-arc
correction:

- **The play loop** is where *substance* enters — expansion of beats into staged
  prose, and the consistency anchors (phase spine, roster binding) that keep that
  expansion coherent. This is the load-bearing work.
- **The Final Cut** is *deduplication and smoothing*. On a 7-turn arc the turns
  barely repeat themselves, so there is almost nothing to dedupe, and the cut's
  contribution shrinks to connective tissue. Its value is **monotonic in arc
  length**: it only starts paying off once the arc is long enough that the turns
  themselves begin re-establishing standing facts — precisely the windowing defect
  FR-484 was built to fix, which a 7-turn scene never triggers hard enough to see.

So the Final Cut is not theatre — but its worth, like the rest of the pipeline, is
invisible at this length and would surface on a longer one. Same shape as the
consistency-vs-length curve: I keep measuring length-flat properties at length 1
and watching them read as zero.

## Heuristic

When attributing a quality of the final artifact to a pipeline stage, measure the
**seam of first appearance**, not the size at the end. A late stage that is ~1:1 in
vocabulary with its input added *continuity*, not *content* — credit the stage where
each detail was born. Size at the terminal node is the sum of every upstream
contribution; it names none of them.

## Seed

The cut's real job — deduplicating standing facts across a long arc — is exactly the
thing a 7-turn scene cannot exercise. Should the consistency-vs-length eval
(previous Seed) score the Final Cut specifically on **redundancy removed**:
standing-fact repetition in the raw concatenated recaps minus the same in the cut,
as a function of turn count? That curve would show the precise arc length at which
the Final Cut stops being connective tissue and starts being the deduplicator it was
designed to be — turning "is the cut worth a call?" into a length threshold instead
of an opinion.
