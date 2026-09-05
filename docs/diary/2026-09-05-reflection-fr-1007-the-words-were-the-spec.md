# Reflection — FR-1007: the words were the spec all along

**Date:** 2026-09-05
**FR:** FR-1007 (command book)

## What happened

The operator asked "any command missing" about an eleven-word sequence. Three
were missing (`research`, `release`, `retire`) and one was out of order
(`merge` armed at `pr` time). Then: "write command-book.md … wt, fr, judge,
doc pr, outsider, merge" — the book was to be filed through the very sequence it
documents. The judge returned seven revisions for a reference page, one of them
a human decision the doctrine had left open for a year: is `merge` in an
advance sequence a grant or a plan?

## The trap

`architecture_as_diagram`. The stages were documented (Sermon), the routes were
documented (five doctrines), the incidents were documented (diaries) — and the
thing that actually drives the loop, fifteen words typed by one person, was
documented nowhere. I had been executing an unwritten protocol from context
each session, and it drifted exactly where the context was thin: the end of the
sequence (`review` skipped on #603, `merge` armed early on #597). The
distinction the judge forced — doctrine / procedure / local convention / alias —
was the useful part: two of my "four rules" were already law, two were
observations from one day, and calling all four "rules" would have been
`quick_confidence` in a table.

Second: I wrote "every word leaves a file whose absence proves omission" and
believed it. `wt` leaves a directory that cleanup deletes; `merge` leaves a Git
object. The judge's R-6 (durable vs transient witness) is
`gate_checks_shape_not_substance` applied to my own evidence claim.

## The heuristic

**When the operator's utterance is a fixed vocabulary, the vocabulary is a
spec — write it down with the witness for each word.** A verdict that leaves no
durable trace cannot be audited by a successor; a word whose obligation lives
only in habit will be dropped by the session with the least context.

The operator's answer to R-5 is worth keeping verbatim: *merge given in the
example is permission to proceed; the agent may abort or fix.* That is the
manual loop's whole economy in one sentence — authority is granted in advance
and the agent's job is to know when not to use it.

**Seed:** the book has a "Verify" column that is all shell one-liners. Could
`scripts/rite-check.sh FR-NNNN` run them and print the fifteen entries with a
tick, a dash, or a question mark — a witness audit, not a driver — so that "any
command missing" becomes a command?
