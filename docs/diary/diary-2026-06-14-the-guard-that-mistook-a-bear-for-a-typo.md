# The Guard That Mistook a Bear for a Typo

*2026-06-14 — FR-483, DM v2 scene-pivotal non-roster actors*

## What happened

A user read a generated key scene and caught what every automated check missed:
Krog, a cave bear who *kills one hunter and is killed by the other*, was absent
from the scene's CHARACTERS list. He was in the SUMMARY. He was in the BEATS. He
just wasn't *cast* — the one section that says "this is a principal." A major
actor reduced to set dressing.

The cause was a guard I'd helped write two FRs earlier. FR-480 added a roster
lock to kill name drift (`Brog`/`Broga`, `Tarka`/`Tarek`): "use exactly the
rostered names, introduce no name the roster does not list." Correct for its
purpose. But the roster is minted from the *human* principals, and the lock was
phrased absolutely — *any* non-roster name is forbidden. So when the synopsis
itself introduced a bear, the model faced two contradictory instructions ("list
who drives the scene" vs "no non-roster names") and obeyed the stricter one,
silently cutting the bear from the cast while still narrating him everywhere.

## The trap: a guard wider than the thing it guards

This is the `downstream_fix` / over-broad-guard pattern, but with a sharper edge:
the guard wasn't in the wrong *place*, it was the wrong *width*. It was written to
catch "variant of a rostered name" and "invented human principal," but it was
*phrased* as "name not on the roster." Those are not the same set. A
synopsis-introduced beast is a name not on the roster, but it is neither a variant
nor an invention — it has provenance. The guard's predicate was a proxy
("on the roster?") for the real question ("does this name have provenance?"), and
the proxy failed exactly where the two diverge.

The user's framing was the key that turned it: *"despite being a major actor Krog
is not listed."* Not "the model made an error" — "the rule is wrong." Once I
stopped asking "why did the model drop Krog?" and started asking "what category
does Krog belong to that our pipeline has no slot for?", the fix wrote itself.
The missing category was *scene-declared non-roster actor*: legitimate, provenance
in the frozen scene card, just not a rostered character sheet.

## The premise was enforced in two places, not one

My first FR draft fixed only `key_scene.yaml`. The user said "address the
underlying issue," and reading `turn_direct.yaml` showed why that was shallow: the
*same flawed premise* — non-roster name = error — lived in a second guard, the
director's continuity check ("flag any name acting that is NOT one of the rostered
cast"). Fixing only the casting prompt would have let the model cast Krog and then
flagged him as a continuity breach *every single turn* — the exact perpetual-noise
failure FR-480's dedupe was meant to kill. A premise enforced in two boundaries
must be corrected at both, or the symptom just migrates from one to the other.

## The decision the Judge forced: generative vs deterministic

Casting Krog is irreducibly generative — only the model, reading the synopsis, can
decide a bear is a principal and write him in. So A is a prompt reword, and it has
*no deterministic witness*: the J3 harness mocks the scene, so no test can prove
the live model will actually cast him. That's an honest weakness, named in the
Seed.

But *suppressing* his continuity flag is deterministic — the scene card already
lists him, so code can read the CHARACTERS block and drop flags about declared
names. The Judge invoked the FR-482 precedent: do not ask the model to do the
deterministic part. Trusting `gemini-3.5-flash` to exempt the actor it just cast,
when FR-480 already proved it honors roster rules inconsistently, would repeat the
mistake. So B is a code filter (`_filter_continuity`) in the same `invoke_turn`
normalization seam as `_clamp_phase` and `_canonicalize_beats`. The prompt reword
stays only as honesty — so the instruction isn't self-contradictory — but the
guarantee is the code.

## The witness that matters is the *kept* one

The easy test proves the filter suppresses Krog. The test that proves the filter
is *correct* proves it KEEPS Zalor — a name with no provenance in roster or scene.
A filter that drops everything passes the suppress test and fails the world.
Provenance is the line: cast in the scene's CHARACTERS block, not merely mentioned
in prose. That distinction is what keeps the FR-479 Vane case (a phantom named
only in a prose sentence) a real breach — `_parse_scene_characters` returns empty
for a card with no CHARACTERS block, so the filter no-ops and the prose phantom
stays flagged.

## Seed

A (casting) is a hypothesis with no automated witness; only a live run can confirm
the model casts the beast now that it's permitted. **Seed:** when a fix splits
into a generative half that can't be unit-tested and a deterministic half that
can, should the FR carry an explicit *live-run acceptance* — a recorded real
`vertex` run cited in the FR — as the witness for the generative half, the way we
cite LangSmith traces for operational defects? Or is a permanently-unwitnessed
prompt change an acceptable J3 residual, trusting the next real story to surface
it? Where is the line between "tested in code" and "observed in production" for
the parts of an LLM system that are irreducibly the model's judgement?
