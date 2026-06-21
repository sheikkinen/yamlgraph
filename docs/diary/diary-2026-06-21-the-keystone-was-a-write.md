# The keystone was a write, not a type

**Date:** 2026-06-21
**FR:** FR-556 (DM v2 Typed StoryDoc Contract + Sole Accessor, Contract A)

## What happened

Contract A reads, on its face, like a typing exercise: wrap the chapter sub-tree
in a Pydantic model, point the reach-in sites at getters, call it done. That was
my first mental model, and it was wrong in the way the Judge had already flagged.
The keystone deliverable is not the `StoryDoc` type. It is `write_chapter_card` --
the one setter that REJECTS a structurally-invalid card before it reaches the doc.
The type is the easy half; the write seam is the half the whole program is for,
because FR-558 binds the playability gate to a write that already exists.

## The trap: validate-where-it-manifests

My instinct was to validate at `read()` -- parse the doc as it loads, fail fast on
a bad shape. The Judge's J2 caught it: read-time validation raises mid-run on the
legacy and partial books that degrade gracefully *today*. The instruments already
tolerate a missing `turns` or an empty `world_state`; forcing validation at the
read boundary would convert a graceful degrade into a crash for every book authored
before this contract. The boundary that matters is not where the data *enters
memory* (read) but where *new* data is *authored* (write). So the parse binds to
the setter: a card that an authoring path tries to commit is validated; a card that
was persisted last week is read as the plain dict it has always been. Same law --
normalize at the boundary -- but the boundary is the write, not the read.

## The cycle I did not create

Binding the setter into `chapter_nav` tempted a cycle: the gate battery
(`gap_detectors`) imports `chapter_nav`, so a setter that gates would close the
loop. For Contract A I sidestepped it entirely -- the setter does ONLY structural
validation via `story_doc` (a leaf over json/pathlib), so `chapter_nav` stays
acyclic and near-leaf. The gate binding is FR-558's problem, and it will need a
lazy import or a write-site bind. Naming the cycle now, before it exists, is
cheaper than discovering it under the next FR's deadline.

## Evidence over assertion

42/42 live books validate against `StoryDoc`. I did not assert the parse was
permissive enough; I ran it against every story.json on disk. The permissive
`extra="allow"` plus all-optional fields is not laziness -- it is the measured
shape of what the codebase actually writes (`world_state` as `""` on a fresh card
AND a typed ledger dict on a closed one; both had to pass).

## Heuristic

When a refactor is framed as "add a type," ask which WRITE the type is protecting.
A type with no rejecting write is documentation; the value is in the seam that
refuses bad data, and that seam is almost always a setter, not a model.

**Seed:** The setter validates structure; FR-558 will make it validate
playability. Both are "reject before commit." Is there a single `write_chapter_card`
contract that composes an open list of card-level validators (structural, then
gates, then future continuity checks) so each new gate is a registration, not an
edit to the setter body?
