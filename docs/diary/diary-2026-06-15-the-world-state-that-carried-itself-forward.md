# The World State That Carried Itself Forward

*Diary — 2026-06-15 — FR-488, DM v2 book-scope chapters*

## What happened

I added the missing middle of the book recursion: a Chapters stage between the
synopsis and prose. The synopsis splits into a fixed, ordered set of chapter
cards; each chapter expands into full prose **plus** an explicit `world_state`
ledger, and expanding chapter *n* threads chapter *n−1*'s ledger forward as the
opening truth it must honor.

The judgement (FR-488 J1–J7) had already corrected three "mirrors the roster
exactly" claims before I touched code — and that pre-correction is the whole
story of this enforcement. I did not discover the divergences; the Judge did. My
job was to obey them, and obedience was *boring*. Boring enforcement is the
signature of a good judgement (Scripture: `boring_enforcement`).

## The trap I did not fall into (because the Judge caught it first)

The seductive frame was **`framework_costume` in reverse**: "chapters are just
characters one level up — reuse `split_roster`, reuse `_invoke_stage`, reuse the
slug-append idempotency." Three times that analogy is *almost* right and exactly
wrong:

- **J1** — a chapter carries a title *and* a paragraph; `split_roster`'s
  line-split cannot hold structure. The outline is a `parse_json` `{title,
  summary}`, not a names-on-lines blob.
- **J2** — a chapter needs the previous `world_state` threaded in, which bare
  graph variables cannot supply; it is a *composed* stage (`_compose_special`),
  like a turn, not an ordinary card.
- **J6** — character slugs append idempotently (`kara`, `kara-2`); numeric
  chapter ids cannot. So the set is **fixed at derivation**, and
  `_expand_chapters` guards `if order: return`.

Each is `false_duplicate` made concrete: *syntactic similarity is not semantic
equivalence.* The roster pattern and the chapter pattern rhyme at the surface and
diverge at every load-bearing seam. Had I coded from the analogy I would have
shipped three subtle bugs, all passing a shape check.

## The seam that mattered

J7 named the priority RED test: assert that expanding `chapter:2` *passes*
chapter:1's `world_state` into the graph variables — assert on the **plumbing**,
not the LLM content. This is the right instinct sharpened to a point. The mock
supplies the world-state string; the test proves only that the wire delivers it.
A `plausible_wrong_answer` here would be a test that checks the chapter 2 *prose*
mentions the flood — which the model would do anyway, from the summary, even if
the forward-carry were broken. The forward-carry is invisible in the output and
only visible in the variables. Test the seam, not the destination.

The live vertex run was the reward: chapter 1 ended *"Jaren is alive and by her
side,"* and chapter 2 — handed exactly that ledger — **opened from Jaren alive**
and advanced to losing him, then wrote a new ledger: *"Jaren has been swept away
and is lost."* The prior truth was honored, never contradicted, and moved on. The
plumbing held under a real model.

## The honest caveat

At two chapters the forward-carry's *value* is invisible. Consistency-held-across-
length is the product (diaries 2026-06-14: *fifty-call story* → *consistency over
length*), and two chapters is not length. I built the seam the consistency eval
will exercise; I did not prove it scales. The eval is the witness; this is the
wire it tests.

## Heuristic

**When a new feature "is just the old one, one level up," list the seams where
the level-shift breaks the analogy *before* reusing any code.** A recursion is
scale-invariant in shape and scale-*variant* in mechanism: the data widens
(line → structure), the dependency deepens (independent → carried-forward), the
identity changes (append-safe slug → fixed numeric id). The analogy tells you
*where* the feature goes; it lies about *how* it works.

## Seed

The `world_state` is prose today (OQ1: typed ledger deferred). Prose is a
`plausible_wrong_answer` waiting to happen — a model can write a fluent
`world_state` that silently contradicts chapter *n−2* because nothing *checks*
it, only carries it. **What would a typed, diffable world-state ledger look like
— one where "Jaren: alive" → "Jaren: lost" is a recorded transition a gate could
assert on, turning the consistency anchor from a hope into a test?** That is the
real consistency engine, and it deserves its own RED.
