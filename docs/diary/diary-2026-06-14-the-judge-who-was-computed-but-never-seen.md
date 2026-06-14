# The Judge Who Was Computed but Never Seen

*2026-06-14 — FR-481, DM v2 Director card & monotonic phase*

## What happened

FR-479 built a director: every play turn, a structured `direction` judgement —
`phase`, `establishing`, `beats_satisfied`, `scene_complete`, `steer`,
`continuity` — computed by the model and recorded on the turn. The first full
9-turn run (`6eae1ce5`) ran clean. But when I read the run to reflect, I noticed
the UI surfaced only two of the six fields, and only when non-empty. The director
*judged* the arc on every turn and showed almost none of it to the human it was
judging for. The signal existed; the window onto it did not.

A second defect hid in the same run: `phase` went
`opening → rising → climax → rising → resolved`. The director labeled the yield
the climax, then **un-climaxed** for the next three beats. An arc that runs
backwards is not an arc.

## The trap: computed ≠ surfaced

The first trap was treating "the field is recorded" as "the field is seen." A
structured output that no view renders is a tree falling in an empty forest. The
director was doing real work whose only consumer was the JSON file on disk. The
cure was boring: a `direction: dict` on the view, one always-rendered card. But
the *naming* of the trap matters — **a judge nobody can see is indistinguishable
from no judge**, and the absence is invisible precisely because the code runs and
the tests (which checked the recorded dict, not the rendered page) passed.

## The boundary insight: clamp where the data is certain

For the backwards phase, I had two options the judgement weighed: tell the model
not to regress (prompt context), or clamp deterministically in code. I chose the
clamp alone. The reasoning is the one-law again: **normalize at the boundary
where the data is certain, not where it is unreliable.** The model's per-turn
phase is the unreliable input; the prior turn's *recorded* phase is a certainty
already on disk. `max(prior, current)` by ordinal makes the record correct
regardless of what the model does next turn. Spending prompt tokens to *ask* the
model to be monotonic trusts the faculty that already failed. A floor that cannot
be violated beats an instruction that can be ignored.

## The fold that removed a drift hazard

The judgement folded `StageView.scene_complete` and `StageView.continuity` into
the single `direction` dict. The tug was real: two scalars were "simpler" per
field. But two sources for one datum (`StageView.scene_complete` vs
`direction["scene_complete"]`) is a drift hazard — the moment they can disagree,
one of them is a lie. Collapsing to one reader (`turn_direction` already returns
the whole dict) means there is nothing to keep in sync. The check that made this
safe was confirming `_accept_target`'s play-loop stop read `turn_direction`
*directly*, not via the view — so moving the scalars off `StageView` could not
break the one place that branches on scene completion.

## Seed

The Director card now renders `beats_satisfied` as the model's raw phrases, which
drift in wording turn to turn — the same beat appears as three spellings across a
run. FR-482 will canonicalize them against the frozen key-scene BEATS. **Seed:**
when a structured field's *values* are free text from a model, is the field
trustworthy until something pins those values to a closed vocabulary the model
cannot expand? Where else in the codebase do we display model free-text as if it
were an enum?
