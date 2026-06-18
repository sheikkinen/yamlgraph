# The Gate That Failed Its Own Cure

**FR-527 — DM v2 beat-progress early close (FALSIFIED at enforce)**

## What happened

FR-527 was judged, scope-frozen, and authorized for enforce. The cure (Fix A): a
deterministic guard that closes a chapter once its `beats_satisfied` count has not
grown for `BEAT_STALL_LIMIT = 3` turns — to stop the "no-progress tail" (208 wasted
turns over 127 chapters) where a director covers its playable beats, never flips the
computed `scene_complete` (`k == n`), and rides the FR-501 cap replaying a resolved
scene.

I built it under TDD exactly as judged: RED condemned the 10025-BC CH8 plateau and
added the J6 corpus counterfactual; GREEN added `_beats_stalled` and wired
`chapter_should_close`. Then the GREEN run **failed the judgement's own J6 safety
check**:

```
10003-BC CH5: stall guard preempted natural close at t9 (scene_complete @t14)
```

A full-corpus scan proved it structural, not a tuning miss. **Natural directors pause
beat-marking mid-scene and resume.** The longest plateau *preceding* a natural
`scene_complete` is 9 turns (10013-BC CH1: count frozen at 2 for t2..t10, then closes
at t13). To never preempt a natural close, the limit must exceed 9 — but 18 of 27
waste chapters have a frozen tail shorter than 9, so at any safe limit they get zero
benefit, and the motivating CH8 (frozen 11 turns) fires at t15, saving one turn before
the t16 cap. The promised win (close ~t9, save 7) evaporates. The signal cannot
separate a *finished* director from a *pausing* one. Guard reverted; cure deferred to
the outliner (FR-528, the J4 seed).

## The trap

**`gate_checks_shape_not_substance`, but in the JUDGEMENT, not the code.** J6 was the
right *design* — a deterministic corpus counterfactual is exactly the load-bearing
check an early-close guard needs. But the judge **spot-checked a single easy trace**
(CH1's `0,1,2,2,3,3,5`, which happens never to plateau for 3) and generalized "the
guard never fires before a natural close" from that one example. The worst-case corpus
member — a 9-turn natural plateau — was never enumerated. A safety check validated
against one cherry-picked trace is compliance theatre; the same check run over the
*whole* corpus is the real gate. The witness only earns its keep when it sees the
adversarial member of the population, not the convenient one.

## The insight

A count plateau is **mid-scene noise, not a scene-end signal.** The beat ledger marks
*which enumerated beats are now true*; a stochastic director stops and restarts that
marking for narrative reasons (a quiet beat, a digression, a slow build) with no
relation to whether the scene is over. The only deterministic "the scene is finished"
signal is `k == n` — which is already `scene_complete`. There is no second
deterministic signal hiding in the same vector; the plateau-vs-finished distinction is
simply not present in the count history at decision time (at t9, CH8-frozen and
CH3-about-to-resume are identical). When a proposed signal is a transform of an
existing one, it carries no new information — Fix A was `scene_complete` wearing a
fuzzier costume.

The honest enforce outcome is the cheapest bug killed at the gate: revert the guard,
replace the now-false "close on stall" unit tests with one corpus test that *pins the
non-separability* (`test_beat_plateau_signal_is_non_separable`) so the dead end is
never retried, and move the cure to the boundary J4 already named — the outliner must
not author a final beat the capped scene can never reach. Respect the RED: the witness
won.

## Seed

When a judgement mandates a deterministic safety check, must the *judgement itself* be
required to run that check over the full corpus before freezing scope — i.e. should
"J-gate validated against >1 trace, including the worst-case member" be a structural
requirement of judgement, the way RED-before-GREEN is of enforce? A gate spot-checked
on one example is a hypothesis; a gate run over the population is a proof. Where else
in the pipeline do we freeze a constraint on the strength of a single convenient
witness?
