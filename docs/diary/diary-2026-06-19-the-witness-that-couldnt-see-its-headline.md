# The Witness That Couldn't See Its Own Headline

*2026-06-19 — Distill, FR-538 (DM v2 seam-entrance witness)*

## What happened

FR-538 builds the deterministic mirror of the exit-edge detector: catch a character
who *acts* in a chapter's prose but crossed the seam with no on-page arrival. The
plan, the judgement (B1: measure prose establishment, not manifest presence), the
seven RED fixtures — all clean. I implemented `seam_entrance_gap`, split it into a
leaf to dodge the 450-line ceiling, went green, lint-clean, import-linter KEPT.

Then I ran it on 10028-BC — the exact book whose review *motivated the FR* — and it
reported `gap_count = 0` on every chapter.

## The trap: the worked example named a character the lens cannot see

The FR's Value Statement quotes the reviewer verbatim: *"Arnulf appears in Chapter 3
… never present in Chapter 2 … no prior establishment."* That is the headline
seam-entrance defect. But `acting_in(cid)` was scoped to **roster** names — and
Arnulf is **not in `characters.roster`** (the roster is Hilde, Gunnar, Reinmar,
Svala). Arnulf and Eirik are non-roster named NPCs. The detector structurally cannot
see them. It passed all seven roster-shaped fixtures and reported a confident,
*honest-for-its-lens*, and completely headline-blind zero.

This is `gate_checks_shape_not_substance` relocated one layer earlier than the
judgement anticipated. B1 guarded the **establishment** term — a manifest must not
suppress a gap. It did not guard the **membership** term — the roster scope silently
excludes the very class of character the FR exists to measure. A witness that reads
zero while the named defect persists is the trap, whether the blindness lives in the
establishment check or in who counts as a candidate.

It is also `inventory_by_visibility`: roster membership is a legibility proxy
(tracked, sheeted, reviewed characters), and I let it stand in for "named characters
who can break a seam." The incident-dense cases (Arnulf, Eirik) were exactly the ones
the proxy hid.

## What I did right

I validated against the book the spec cited *before* finalizing, not after shipping.
The fixtures were green; reality was not. I stopped, recorded the finding, and
surfaced the fork rather than silently shipping a zero — because the alternative
(broaden to arbitrary proper names) changes a judged scope and deserved a decision,
not a guess. The requester chose the roster lens knowingly, and the correction landed
where it belonged: in the FR's worked example (Arnulf is non-roster, out of scope —
covered by the status/resurrection rail), not buried in a caveat after merge.

## The heuristic

**A deterministic witness must be run against the exact incident its spec cites,
before its scope is frozen.** Green fixtures prove the lens is internally consistent;
only the cited real case proves the lens is pointed at the defect. When the worked
example falls outside the lens, the cheapest fix is to correct the example or widen
the lens in the *spec* — never to let a confident zero stand.

**Seed:** Could each continuity witness carry a machine-checkable "cited-incident"
anchor — a `(book, chapter, character)` triple from the motivating review that the
witness MUST flag — so a witness that cannot reproduce its own founding defect fails
its own acceptance test instead of silently reporting zero?
