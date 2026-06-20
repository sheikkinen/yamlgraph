# Diary — 2026-06-20 — The Witness That Borrowed the Wrong Edge's Words

**FR-543** — DM v2 seam-entrance witness cleared an unbridged entrance with a death-fall.

## What happened

The FR-538 seam-entrance witness exists to catch a character who *acts* in a chapter
with no narrated arrival across the seam. In 10030-BC Ch3, Arnulf appears "was already
with them on the higher stone" — the literal opposite of an arrival — and the witness
reported `gap_count: 0`. A human reviewer caught what the deterministic witness missed.

The judgment traced two candidate root causes: (1) `_name_has_arrival_signal` scans
*every* occurrence of the name, so a later mention can clear an unbridged first
appearance; (2) the establish lexicon contained exit/fall tokens. Verifying against the
code revealed the deeper truth: `_ESTABLISH_TOKENS` was a **verbatim copy** of
`gap_detectors._REPOSITION_TOKENS` — the *exit-edge, movement-toward-hazard* vocabulary
(`slips`, `loses footing`, `into the water`, `down the bank`). The arrival witness had
borrowed its sibling's **opposite-edge** words. So a sentence narrating Arnulf's death-
fall "dropped into the water below" registered as his *arrival*.

## The trap

`false_duplicate` at the lexicon layer. Two detectors sit on opposite edges of the same
seam (entrance vs exit). Their token lists *look* interchangeable — both are "movement
near a name" word-runs — so the exit lexicon was copied into the entrance detector. But
the **sense inverts** across the edge: "into the water" is a valid reposition-toward-
hazard for the EXIT detector and a death-fall (never an arrival) for the ENTRANCE one.
Syntactic similarity, semantic opposition.

## The judgment that mattered

Two fixes were proposed; one piece of evidence justified them. The cited defect is
cleared by the lexicon purge *alone* (the only clearing token was the fall). Per
`spec_kill`/`purge`, I bound the FR to the lexicon-hygiene fix and **deferred** the
first-occurrence anchoring — it was not condemned by the evidence, and strict anchoring
inside a 60-char window carries its own false-positive risk (a slightly-late but
legitimate arrival becoming a false gap that would force needless FR-539 revisions).
Refusing to bundle the unjustified fix is the cheaper path: less code, less risk, and
the deferred fix keeps a clean condemnation bar if it ever earns its own evidence.

## Heuristic

- **lexicon_provenance**: When two detectors sit on opposite edges of one boundary
  (entrance/exit, open/close, acquire/release), NEVER copy one's token/keyword list into
  the other. The words may be identical while their *sense inverts* across the edge.
  Derive each edge's lexicon from its own direction, and document the prohibition at the
  constant so the next copy-paste is caught at review.

## Seed

The fix forbids re-borrowing `_REPOSITION_TOKENS` with a docstring — an *advisory*
guard. Could a cheap unit test assert `set(_ESTABLISH_TOKENS).isdisjoint(_REPOSITION_TOKENS)`
so the prohibition is *mechanical*, not prose? More broadly: how many other opposite-edge
detector pairs in DM v2 (and the FSM bridge) share a lexicon by copy, and would a single
disjointness test across all such pairs convert a recurring `false_duplicate` trap into a
gate?
