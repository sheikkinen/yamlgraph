# The Flag That Fired Every Turn

*2026-06-13 — FR-480, DM v2 roster/scene name binding*

## What happened

FR-479's first real run (`c8c0b08c`) gave the director everything it was built
for — scene start, scene end, arc steer all worked on the first try — and one
honest piece of noise: the continuity flag fired the *same* breach
(`Brog` ≠ `Broga`) on all six turns. The obvious next move was to dedupe the
flag. I almost wrote that FR.

The Judge stopped it. The flag was not the disease; it was the thermometer. Two
generation passes — `character_roster.yaml` and `key_scene.yaml` — each derived
character names from the synopsis *independently*, neither seeing the other, so
they drifted. Deduping the flag would have hidden a true positive while leaving
the cause untouched. The cure was to bind the key scene to the roster at
generation time, so the divergent name can never be minted.

## The trap

**`downstream_fix` wearing a UX costume.** The noise *manifested* in the turn
loop (a flag repeated six times), so the instinct was to fix it there (dedupe).
But the noise *originated* two stages upstream, at synopsis-expansion, where two
prompts invented two spellings of one character. The_one_law again: normalize at
the boundary where the divergence enters, not where it manifests. A dedupe is a
guard at the symptom; name binding is a fix at the source. Once bound, there is
nothing to dedupe.

There was a second, quieter trap the Judge caught: the draft FR feared a
"roster-id casing wrinkle" (binding to lowercased ids would lose proper-noun
casing). I had assumed the data flow without reading it. The roster *cards*
already store proper-case display names; only the *id* is lowercased. The feared
wrinkle did not exist. **A premise stated confidently in a plan is still a
premise — verify the data flow before designing around it.**

## The composition consequence

FR-480 hardened the generation boundary, which *broke a downstream test by
making it correct*. FR-479's phantom test obtained its phantom from the
generator (the mock emitted `Naru`). FR-480's whole purpose is that the
generator can no longer do that. So the test could not get its phantom the old
way. The fix was not to weaken FR-480 but to recognize the test's *assertion*
(the director flags a non-roster name) was still valuable as defense in depth —
and to inject the stray name *past* the now-hardened boundary, directly into the
frozen scene. The assertion never changed; only the injection point moved to
where a stray name could still plausibly arrive.

## Heuristic

When a detector fires the same true positive repeatedly, the fix is usually
upstream of the detector, not at it: silence the *source* of the signal, not the
signal. And when hardening a boundary breaks a downstream test, ask whether the
test's *setup* (not its assertion) was relying on the very defect you just fixed —
if so, move the injection past the boundary; keep the assertion.

**Seed:** The director's `continuity` is free prose that varies every turn, which
is *why* it cannot be deduped today (deferred Deliverable B). Is there a general
DM-prototype rule emerging — that any director signal a downstream stage must
*compare across turns* (dedupe, trend, escalate) has to be emitted as a stable
keyed object, never prose? Could a lint flag "an `output_schema` field consumed
by cross-turn logic but typed as free `str`"?
