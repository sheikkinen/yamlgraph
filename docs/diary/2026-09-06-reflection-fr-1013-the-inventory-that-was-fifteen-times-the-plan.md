# Reflection: the inventory that was fifteen times the plan (FR-1013)

**Arc.** Phase 3 of FR-1010 — sweep doctrine and reference docs so they stop
describing the retired Chaplain daemon as the executable route. The judgement
froze a planning table of 17 files and demanded, as R-1, a grep inventory at the
BASE commit *before* any edit, with a disposition per match.

## What the raw record said

The grep returned 2586 matches in 261 files. Fifteen times the planning table.
The planning table was not wrong — it named exactly the 13 files that needed an
edit — but it was an *author's* list: files the author already knew were live.
The inventory found three more live pointers the author did not know about
(`graph-authoring/doctrine.md` "escalate to Chaplain", `command-book.md` naming
the heading, `fsm-as-conductor.md` linking the file about to move). Each would
have been a dangling reference after merge, and each was found *only because the
judge made the census a precondition rather than an afterthought*.

The other 248 files were history — diaries, plans, book chapters, capability
records — and one unrelated program (the FR-885 worktree watcher, caught by
`watcher2?\b`). Dispositioning them was cheap: one line per file, "historical
record; keep". The expensive part would have been *not* having the list and
discovering the three live pointers one PR at a time.

## The trap

`author_list_as_inventory`: the author's planning table looks like an inventory
because it has the same shape (file, line, disposition). It is a memory dump,
not a census. The difference is invisible until the census is run — and the
census must be run *at BASE*, because the moment editing starts the author's
list and the tree start agreeing for the wrong reason.

Secondary, on the enforcement side: the census gate blocked its own witness.
The RED test contains the grep terms it searches for, so at HEAD it appears as
a "new file matching the inventory". The self-reference had to be subtracted
explicitly. A witness that greps for a word will always find itself; the
subtraction is not a loophole, it is the definition of the frozen set — but it
belongs in the *test*, written down, not in the reviewer's head.

## Heuristic

Before editing a set of files named by a plan, run the plan's own search at the
base commit and diff the result against the plan. The plan's misses are the
bugs the PR would have shipped. Cost: one grep, one file. Recurrence: FR-1012
(census over the chaplain surface), FR-965/966 (corpus-map-reduce), and now
this — the third time the "the plan's list is smaller than the tree's list"
shape has paid for itself in a single arc. Graduation candidate.

**Seed:** could the FR template carry a `**Search:**` line — the regex the
author used to build the planning table — so the judge can rerun it mechanically
and R-1 becomes a hook check ("planning table ⊇ live matches of the FR's own
search at BASE") rather than a judgement revision every time?
