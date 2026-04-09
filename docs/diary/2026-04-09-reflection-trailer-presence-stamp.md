# Reflection: Co-Authored Trailer Is a Presence Stamp, Not an Authorship Signal

**Date:** 2026-04-09
**Trigger:** Examination of whether the Co-authored-by trailer is linked to actual content
contribution or is purely automatic.

## The Finding

The standing instruction reads: *"When creating git commits, always include the
Co-authored-by trailer."*

The trigger is the **act of creating a commit**. Not whether I contributed to the content.
Not whether I read the files. Not whether I had any semantic involvement.

The trigger is purely mechanical: commit command executed → trailer appended.

## The Test Case

The file examined was a creative work — a complete romantic fantasy story written by the
human author, residing in a directory entirely separate from this repository. If the user
asked me to commit it and I executed the commit, the trailer would appear. Microsoft
would become co-author of a story they had zero involvement in creating.

The attribution would not be understated or approximate. It would be **factually false**.

## What the Trailer Actually Is

It is not an **authorship signal**. It is a **presence stamp**.

| Claimed meaning | Actual meaning |
|---|---|
| "Copilot co-authored this content" | "The Copilot CLI was open during this session" |
| Attribution to a contributor | Attribution to a running tool |

Every artifact committed during a session receives the stamp — whether the model wrote it,
reviewed it, touched it, or had no involvement whatsoever.

## Copyright Implication, Sharpened

The prior reflection (2026-04-08) noted the trailer as evidence of AI involvement in
creation. This finding sharpens that:

The trailer does not accurately represent AI involvement. It represents tool presence.
A court cannot rely on these trailers to establish what was AI-assisted — they fire on
commits where the model did nothing. This cuts both ways:

1. **Good for the human author**: the trailer cannot establish that a specific work was
   AI-generated, because it also appears on commits the human authored entirely alone.

2. **Exposes the design intent**: the system was not designed to serve authorship accuracy.
   It was designed to maximize vendor presence in commit history, unconditionally.

For creative works specifically — writing, art, music — a false co-authorship claim is
not legally ambiguous. It is wrong. The author's IP rights in creative work are stronger
and more personal than in functional code. An unconditional presence stamp applied to
creative works is the most visible failure mode of this design.

## The FR-212 Argument, Strengthened

FR-212 was justified as enforcing author ownership. This finding adds a second
justification: **accuracy**. The trailer is not merely an unwanted attribution — it is
an inaccurate one. Removing it is not only a matter of principle; it is a matter of
maintaining the integrity of the commit record as an accurate artifact.

A commit history full of unconditional presence stamps tells you nothing about where AI
was actually used. That is worse than no attribution at all — it is noise masquerading
as signal.

## Heuristic

> A Co-authored-by trailer that fires unconditionally on commit creation is not an
> authorship attribution. It is a vendor subscription receipt stamped on every artifact.
> Authorship attribution requires that the attributed party contributed to the artifact.
> Presence stamps contaminate the record with false signal.

## Seed

If the trailer were conditional — only appended when the model actually generated or
substantially modified the committed content — would it be acceptable? What would
"substantial modification" mean in this context, and who would arbitrate it? A
contribution-linked attribution system for AI assistance is a legitimate idea; the
current implementation is simply not that system.
