# The Two Lenses of a Seam

*FR-539 — 2026-06-19*

## What happened

FR-538 built the witness that *measures* unbridged entrances (prose outcome).
FR-539 built the narrator's *peripheral vision* that should prevent them: a
`cast_entrances` manifest (who the chapter scopes in but the prior chapter left
off-page) plus the prior chapter's closing prose, both fed into the existing Final
Cut. The whole risk of this FR lived in one sentence of its Judgement: **the
manifest must never suppress the witness's gap.** Two lenses on the same seam — a
candidate set (planning) and a prose outcome (reality) — that are *supposed* to
disagree.

## The trap

`gate_checks_shape_not_substance`, in its most seductive form. The cheapest way to
make FR-538's gap drop to zero would have been to subtract the FR-539 manifest from
it: "we listed Arnulf as entering, therefore he's established." That passes every
shape check and is a lie — listing a name is not narrating an arrival. The Judgement
named this as paired-B1 before any code existed, so the cure was already in the
spec: the manifest is *input to the narrator*, never a term in the witness's
formula. I encoded the distinction as an assertion, not a comment —
`test_candidate_includes_entrant_with_no_prose` proves a scoped entrant absent from
the prose is *still* a candidate. The two lenses can never collapse into one because
a test forbids it.

## The smaller trap

My first S1 test asserted a *new* entrant's manifest line carried his inherited
ledger row ("wounded at the ford"). It didn't — and shouldn't: a genuine newcomer
has no last-seen detail, only "introduce them." The RED was *correct behavior*
condemning a *wrong test*. I'd reached for a plausible assertion (status should
appear) without simulating which `kind` the fixture produced. The fix was to test
the ledger-surfacing on a *continuing* entrant, where the row is real. Respect the
RED — it was the color of understanding, even when the production code was already
right.

## Heuristic

When a feature's two halves are *designed to disagree* (candidate vs outcome,
intent vs effect, plan vs prose), the load-bearing test is the one that proves they
*stay* separate — not the one that proves either half works. Write the divergence
assertion first; it is the spec's real claim.

## Seed

FR-538's witness now has a generative partner that should drive its gap toward
zero. But the gap-drop is only observable on a real LLM compose. Could a cheap
*synthetic* narrator — a deterministic stub that echoes the manifest into prose
("Arnulf arrives at the ford") — let the witness's success criterion run in the
unit suite, turning an integration-only acceptance into a deterministic one? Where
is the line between "testing the prompt" (integration) and "testing that the
context the prompt needs is present and shaped to be establishable" (unit)?
