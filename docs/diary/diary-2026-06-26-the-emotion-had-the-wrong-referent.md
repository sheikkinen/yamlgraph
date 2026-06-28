# The beat was not wrong; the referent was

**FR-605 — L7 two-pass affect (what-then-where) — REFUTED, but the refutation re-named the problem**

## What happened

FR-604 closed by naming the surviving lever: not "how many deltas per beat" but "which beat
carries the close" — beat-localization. The autopsy quantified it: 71% of supported-kind
protagonist misses were `wrong_beat` (right emotion, far beat). FR-605 took the obvious
swing — split "what" (pass 1 names the SET of emotions) from "where" (pass 2 locates each
named emotion's open/close independently), so the model stops collapsing endpoints onto the
one salient beat. Three draws, temp 0.7, stable. Recall rose 0.214 -> 0.250; precision fell
to 0.368, **0.007 below** arm A's 0.375 floor. By the frozen revert rule: REFUTED. Aggregate
collapse did drop, 71% -> 39%. But the two arcs the autopsy singled out — quest hope F6,
horror loss F1/F6 — did not recover. The design worked in aggregate and failed exactly where
it was aimed. That contradiction was the real finding.

## The autopsy bucket lied by being a beat-id comparison

The whole FR rested on a number — `wrong_beat = 71%` — computed by comparing predicted beat
ids to GT beat ids. It is honest arithmetic and it pointed at a real phenomenon (the model
does not land on the GT beat). But I only believed it told me "the model places emotions on
the wrong beat" because I had been reading **beat ids**, never the **beat prose**. When the
spike refuted and I went back to read the actual glosses of the two unrecovered arcs, the
diagnosis inverted.

Horror loss: GT opens it at F1 (*a collapse seals the shaft — trapped*) and closes it at F6
(*moving air — a ventilation shaft*, the way out). The model opened loss at F4 (*the Watcher
takes Fen — Fen is gone*) and never closed it (`null`). Read as beat ids that is a
catastrophic mis-placement: F4 vs F1, null vs F6. Read as **prose** it is not a placement
error at all — it is a *different loss*. GT's loss is entrapment (resolves when they find
air); the model's loss is bereavement (a death does not resolve, so `null` is the honest
read). The model located its own chosen referent perfectly. Quest hope is the same shape: GT
closes hope at F6 (*Eira surfaces with the Crown* — the object obtained), the model at F8
(*the Crown on the Queen's head, the lack liquidated* — the kingdom saved). Proximate hope
vs terminal hope. Both grounded in the text.

This is the trap worth naming. A metric computed over **identifiers** (beat ids, labels,
keys) silently reports *referent* disagreements as *placement* errors. The `wrong_beat`
bucket counted "predicted id != GT id" and I read it as "the model can't find the right
beat," when a large share of it was "the model and the annotator chose different, equally-
valid events for the same emotion word." No amount of beat-placement prompting fixes that,
because the joint isn't placement — it's *which thing the emotion is about*. Pass 2 faithfully
located whatever pass 1 named; pass 1 named `loss` with **no referent**. The architecture was
well-built and aimed at a joint that wasn't there.

## What the two-pass split actually bought (and where the ceiling moved)

The correction-2 discipline — report pass-1 SET recall as its own number — paid off exactly
as the Judge intended. Pass 1 named only **half** the GT protagonist kinds (0.500), and the
per-genre read showed it is not random: all 9 named hits are `loss` or `hope` (the dominant,
self-contained arcs); the kinds pass 1 systematically drops are the **relational** ones —
`guilt` named 1/4, `betrayal` 0/2. An emotion that only exists "directed at another
character" is nearly invisible to a pass that reads beats for what the protagonist *feels*.
So the bottleneck relocated **upstream**, and split in two: pass-1 blindness to relational
emotions (a set-recall ceiling of 0.50), and, beneath it, the referent mismatch on the kinds
that *do* get named. Neither is a beat-placement problem. The one clean win: support-gating-
by-construction worked — retaliation emitted nothing (vs arm B's 0/18 flood), one false name
across five genres. A kind pass 1 never names cannot invent.

## Heuristic

**A metric over identifiers reports referent disagreements as placement errors.** When a
scorer compares ids/labels/keys (beat ids, span offsets, node names) and a category shows
high "wrong-location," do not trust the bucket name until you read the underlying *content*
at both the predicted and the gold location. If both are valid instances of the same
category attached to different objects, the failure is **referent selection**, not placement
or recall — and every lever aimed at "place it better" will miss. The id-level number is
necessary but it is a projection; the disagreement lives in the prose the ids point at. Read
the thing the id refers to before believing what the id-comparison says failed.

## Seed

GT annotates one canonical referent per emotion (entrapment-loss, not bereavement-loss), but
the text licenses several. The scoring asks "did you hit *my* beat?" when the honest question
is "did you hit *a* text-valid beat for this emotion?" Could the gate accept a **referent
set** — any open/close grounded in the prose for that kind scores, with precision guarding
against ungrounded invention — turning a brittle single-anchor recall into a grounded-anchor
recall? And upstream: if pass 1 named the *referent* ("loss-of-the-way-out", "loss-of-Fen")
rather than the bare kind, pass 2 would have something to locate and the gate something
specific to match. The missing primitive across this whole arc may not be a better detector
but a **typed referent** on every affect delta — the object the feeling is about, named once,
carried through detection, location, and scoring alike.
