# The Judge Caught the Trap I Was Already Walking Into

*2026-06-21 — FR-554, DM v2 recap present-fact preservation*

## What happened

FR-553 ended with a sharp redirect: the continuity breaks were *present-but-ignored*, so the lever
is wording/recap, not prompt mass. FR-554 was the fix FR. I planned it, and a judge pass (the
chaplain's, or a prior turn's) had already written conditions onto it before I returned. C1 was
blocking, and it named precisely the hazard I was about to step into: the FR proposed detecting a
"revived actor" by a *"subject-position name match against the recap text, reusing the deterministic
presence machinery from FR-553."* The judge pointed out that machinery is a turn-1 lowercase
substring test, that no actor-position parser exists, and that "Arnulf surges up", "Arnulf's fallen
body was carried past", and "they wept for Arnulf" all contain the substring while only the first is
a revival. Subject-vs-object position without NLP is the `regex_fourth_exclusion` trap wearing a
respectable noun.

The thing that saved the design was not cleverness — it was *calibrating against real recap text
before writing the detector*. I dumped the actual Ch8 recaps and saw the shape with my own eyes:
`Arnulf surges up`, `Arnulf surges out` (revivals) sitting right next to `Arnulf's fallen body`,
`Arnulf's weapon arm`, `Arnulf's side` (aftermath). The discriminator was not grammar; it was the
**possessive apostrophe**. A single frozen exclusion — drop occurrences immediately followed by
`'s`/`’s` — cleanly separated the two classes the judge said a bare substring would conflate. No
verb lexicon, no fourth special case. And the RED test froze *both* surfaces the judge demanded: the
true-positive and the true-negative, so the false-positive boundary is condemned in code, not
rediscovered in three weeks.

On real data the gauge read 10 — Ch8 Arnulf exited at turn 5 and was narrated acting through turn
14, while the director kept *re-declaring* the exit at turns 13/14. The narrator kept reviving a
character the director kept killing. That tableau is the whole bug in one image.

## The trap

**`downstream_fix` inverted into `over_specified_detector`.** The instinct when building a witness is
to make it *precise* — parse subject position, detect "acting". But precision you cannot implement
deterministically is worse than an honest over-count you can: the parser fails silently on the fourth
sentence shape, and a witness that lies about its own reach is more dangerous than one that says "I
flag possible revivals, go look." The judge's option (a) — drop the precision claim, accept the
over-count, freeze the false-positive surface with a true-negative test — is the `plausible_wrong_answer`
guard applied to a *measurement* rather than an output: assert the shape AND assert the documented
limit.

## The heuristic

**Calibrate a text heuristic against the real corpus before you specify it, and let the corpus pick
the discriminator.** I almost wrote a verb-lexicon "acting" detector from imagination; the actual
recaps handed me a better, simpler signal (the possessive) that I would not have guessed from the
armchair. The corpus is cheaper and truer than the spec's intuition about the corpus. Corollary:
when a detector needs a fourth special case to stay correct, that is the signal to retreat to the
honest over-count, not to grow the regex — bake that retreat into the FR *before* enforce so the
pressure to over-engineer has no opening.

## Seed

The witness over-counts grief and passive constructions ("Arnulf pinned") on purpose, and the recap
clause will drive the count down but probably not to a clean zero — legitimate aftermath references
will keep it lukewarm. **If the gauge floor is non-zero by design, how do we express a regression
target as a *delta against a frozen baseline* rather than an absolute, so "drove 10 -> 3" reads as
success without pretending 3 means three bugs?** And: should the possessive exclusion itself be
tested against a *second* book's recaps before I trust it generalizes beyond Arnulf?
