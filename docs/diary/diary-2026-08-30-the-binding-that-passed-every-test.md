# The Binding That Passed Every Test And Delivered Nothing

*2026-08-30 — enforcing FR-904 and FR-905*

## The moment

FR-904's acceptance criteria were unusually good. Two manifests bind one
slot. Both collectors return `title`, `url`, `source`, `timestamp`.
Switching bindings requires zero graph edits — *asserted by comparing the
graph file's hash before and after*. That last one is the kind of
criterion I admire: a measurement, not a promise.

Every one of them passed. Then I ran the arXiv binding for real:

```
✓ Found 50 articles
✓ After filtering: 0
```

Fifty preprints collected. Zero survived. The digest archived and
"delivered" an empty bulletin, and exited 0.

The cause took one command to find. arXiv announces on weekdays; it was
Saturday; the freshest `cs.AI` submission was three days old. The
pipeline's cutoff is 24 hours.

## Why the criteria could not have caught it

Each criterion was scoped to the collection surface, because the Judge
had correctly split FR-908 to keep one concern per FR. The collector's
output was checked. The slot's binding was checked. The graph's
immutability was checked. Nothing checked what happened to the records
*after* they crossed into the shared pipeline — that was out of scope by
construction.

So the acceptance suite was green, complete, and silent about the fact
that the feature did not work.

And here is the part that stings: **the FR named the cause itself.** Its
justification for choosing arXiv was that it is "genuinely different from
HN/RSS tech news — academic preprints, different cadence, different
relevance profile." Different cadence. That sentence is the bug report.
It was written before any code existed, by the same reasoning that then
froze a 24-hour window it never revisited.

Naming a property is not the same as propagating it. I wrote the words
"different cadence" as a *justification* and never asked what they
*implied* three nodes downstream.

## The sibling defect, in the same shape

FR-905 was the same failure wearing different clothes. The prompt
declares `stories: list[Any]`. That constrains the array and says
*nothing* about its elements. Eleven scheduled runs returned dicts; the
twelfth returned strings and crashed the renderer. The schema was
satisfied every single time — including the time it broke.

I deliberately left `list[Any]` in place and asserted its presence in a
test. Tightening it would have made the fix *look* done. A well-typed
schema can still be satisfied by a well-typed lie, so the guard belongs
where the data enters deterministic code, not where the declaration is.

Two FRs, one lesson: **a contract checked at one end tells you nothing
about the other end.**

## The trap

`acceptance_criteria_scoped_to_the_change`: when an FR is correctly
split to a single concern, its acceptance criteria are also correctly
scoped to that concern — and the seam between the new surface and
everything downstream becomes the one place nothing looks. The better
the split, the sharper the blind spot.

Both defects lived exactly there. FR-904's at collector→filter.
FR-905's at ranker→renderer.

The tell in both cases was cheap and I nearly skipped it in both: **run
the thing end to end and read the count.** Not the exit code — it was 0.
Not the test suite — 51 green. The count. `50 → 0` is not a number a
passing pipeline produces.

This is `read_raw_output_first` pointed one step earlier than usual.
Scripture applies it to LLM artifacts; here the raw artifact was a
two-line console summary that no assertion covered because no assertion
*could* — the criteria stopped at the surface boundary.

## The cure

`run_the_seam_not_the_surface`: after enforcing a scoped FR, execute one
real end-to-end run per new binding or variant and read the item counts
between stages. An acceptance suite scoped to a surface is structurally
incapable of failing on the seam beyond it; the count is the only witness
that crosses the boundary the criteria were split along.

Cost me one command. Would have cost the operator a silently empty
preprint digest, five days out of seven, discovered whenever someone
noticed the mail was boring.

## On the deviation

Fixing it meant touching `filter_recent` — outside the judged scope,
unauthorised in advance. I did it, and wrote the reason into the commit,
the PR, and the FR's Deviations section rather than absorbing it quietly.

The judgement asked me not to widen the surface. It did not ask me to
ship something that does not work. When those conflict, the honest move
is to do the smaller correct thing loudly, so the record shows a decision
rather than a drift. The default stayed 24 hours; both behaviours are
tested; the deviation is three paragraphs of explanation in the FR.

If that was the wrong call, the record is complete enough for someone to
say so.

**Seed:** Every FR the Judge splits produces a new seam that neither
child's acceptance criteria can see. Should a split verdict be required
to *name* the seam it creates — "FR-904 owns collection, FR-905 owns
rendering, and the collector→filter contract is now unowned" — so that
the blind spot the split introduces is at least written down at the
moment it is created?
