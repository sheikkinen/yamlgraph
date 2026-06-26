# Diary — 2026-06-26 — A measurement whose best outcome is "change nothing"

## What happened

FR-602 asked one question of the L7 affect gate: is the residual BEAT-OFF — a model that
reads a feeling one beat early or late — a *gate-strictness artifact* (cheap to forgive in
the evaluator) or *genuine model error* (expensive to fix by scale)? The motivating
evidence, measured on the PRE-FR-600 corpus, showed beat-off misses rising 2 -> 5 as the
match window widened +/-1 -> +/-3. The Judge granted authority but BLOCKED on FR-600 and
set a hard close-condition: **if the post-FR-600 residual is ~0, close unstarted.**

I added a deterministic `--sweep` mode to the probe (the copy/flag the Judge mandated:
canonical `evaluate.py` imported read-only, a new windowed matcher in the probe, window 0
asserted to tie out to the frozen gate per genre). The answer: at +/-1, exactly **one** GT
delta is recovered — a single `open Naima loss` the model placed one beat late, at the
compliance vote instead of the monopoly announcement. One. The AC demands >=3 genuine
displacements before any tolerance may be recommended. So the honest outcome is to keep the
frozen ruler strict and **close the FR unstarted** — exactly the branch the Judge named.

## The trap I did NOT step in

**`downstream_fix` (by construction).** The whole FR was a fortified perimeter around this
trap: the temptation to loosen the ruler so the number goes up. Two predecessors had already
done the honest thing — FR-600 normalized the displacement at the DATA boundary (re-anchored
the GT to experiential beats), FR-601 converted the in-reach kind-confusions with a prompt
cue. By the time FR-602 ran, the residual the ruler could have "forgiven" was a single tail
event. Loosening the gate to recover it would have admitted ever more false matches as the
corpus grows, for a +0.036 recall gain — flattering the model against a ruler that is
correct as strict. The measurement EARNED the right to change nothing.

## The insight

> **A measurement FR succeeds when it produces a defensible decision, not when it produces
> a change.** The growth-as-default reflex says every FR should add or improve something; a
> mature evaluator benefits more from a recorded "we checked, and strict is right" than from
> a loosening that buys 0.036 recall and a slow precision leak. The committed sweep dump is
> the deliverable — the next person who wonders "should the gate be +/-1?" reads one table
> instead of re-litigating it. The cheapest gate change is the one a measurement talked you
> out of.

A structural note worth keeping: the close-condition was framed as "residual ~0", but the
operational test was sharper — **the >=3 evidentiary bar**. One displacement is not ~0 in
the trivial sense (it is non-zero), yet it is decisively below the bar that would license
touching a frozen ruler. The bar, not the raw count, is what makes "1" a clean close.

## Seed

The window sweep also exposes the *shape* of the remaining loss: recall climbs 0.214 ->
0.357 across +/-0 -> +/-3 while precision climbs in lockstep (0.122 -> 0.204). That parallel
climb means the wider-window hits are real op+char+kind matches sitting 2-3 beats off, not
noise — the model knows the arc but anchors it loosely. Is *anchor precision* (how tightly
the model pins an affect to its triggering beat) a separable, promptable skill — the way
close-op kind was — or is it the irreducible floor where scale finally matters? Decompose
the +/-2/+/-3 recoverables by op and chapter-position before concluding "scale".
