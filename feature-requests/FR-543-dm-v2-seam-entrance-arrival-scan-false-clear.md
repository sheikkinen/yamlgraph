# Feature Request: DM v2 Seam-Entrance Arrival-Scan False-Clear

**Priority:** HIGH (the FR-538 witness silently misses the exact defect class it exists to measure)
**Type:** Bug
**Status:** Enforced (binding lexicon-hygiene fix); anchoring deferred (see Judgement)
**Effort:** ~0.25 day (lexicon-hygiene fix alone); ~0.5 day if first-occurrence anchoring is kept and fully tested
**Requested:** 2026-06-20

## Summary

The FR-538 seam-entrance witness (`seam_entrance.seam_entrance_gap`) reports a **false
negative**: a roster character who crosses a chapter seam with no on-page arrival is cleared
from the gap because the arrival-establishment scan (a) inspects **every** occurrence of the
entrant's name in the chapter, not just the first on-page one, and (b) accepts at least one
**exit/falling** token (`into the water`) as an *arrival* signal. The net effect is that a
genuine unbridged entrance is suppressed by a later, semantically-opposite sentence describing
the character's **death-fall**.

## Value Statement

The witness regains its honesty: an unbridged seam entrance is counted as a gap even when the
same chapter later narrates that character *leaving* (falling, being swept away, dying), so
FR-539's seam-aware Final Cut can be proven against a number that does not lie.

## Problem

Observed in **10030-BC**, Chapter 3. Arnulf is a roster member, **absent from the prose of
Chapters 1 and 2**, who first appears *acting* in Chapter 3:

> "...Gunnar rose beside her at once... **Arnulf was already with them on the higher stone**,
> shoulders squared against the wind..."

"...was already with them..." is the literal opposite of a narrated arrival — a textbook
unbridged seam entrance, and precisely the defect class the reviewer LLM flagged by hand
("Arnulf's sudden presence on the ledge in Chapter 3... never explained"). Yet:

```text
seam_entrance_gap(doc, "3") -> {"chapter": "3", "acting_count": 3, "gap_count": 0, "gaps": []}
```

Two compounding root causes:

1. **Whole-chapter name scan (any-occurrence clear).** `_name_has_arrival_signal` succeeds if
   *any* occurrence of the entrant's name sits near an establishment token. The **first**
   mention is the unbridged entrance; a **later** mention cleared it. The arrival check must be
   anchored to the entrant's *first on-page occurrence*, where the seam obligation actually
   falls.

2. **Semantically-inverted establishment token.** The occurrence that cleared the gap was:

   > "...**arnulf** slid off the ledge and dropped **into the water** below."

   This is Arnulf **falling to his death** — an *exit*, not an arrival. `into the water` was
   added to `_ESTABLISH_TOKENS` as an arrival signal (a character coming down the bank into the
   water), so a fall/exit token clears an entrance. This is the `downstream_fix` /
   `gate_checks_shape_not_substance` trap at the token layer: the witness checks the *shape* of
   an arrival word near a name, not the *substance* of an arrival.

This is the witness missing the exact class it was built to catch (FR-538), so it must be
condemned by a failing test before any fix (Scripture: no bug fixed without a failing test
first).

## Proposed Solution

**Binding fix -- lexicon hygiene (the_one_law: fix the defect at the lexicon where it is born).**
The inversion-prone tokens in `_ESTABLISH_TOKENS` are a verbatim copy of
`gap_detectors._REPOSITION_TOKENS` (gap_detectors.py:60) -- the **exit-edge,
movement-toward-hazard** lexicon (`slips`, `loses footing`, `into the water`, `off the ledge`,
`down the bank`, `goes back`, `back for`). The entrance witness borrowed the **opposite edge's**
vocabulary: verbs describing an actor moving *toward death* were enlisted as *arrival* signals.
The defect is a lexicon-provenance error, not "a few bad words".

1. **Purge reposition/exit tokens from `_ESTABLISH_TOKENS`.** Remove every token whose dominant
   sense is descent / fall / departure: at minimum `into the water`, `slips`, `loses footing`,
   `down the bank`, `goes back`, `back for`; audit `descends`/`descended` (dual-sense) and any
   remaining token shared with `_REPOSITION_TOKENS`. The establish set must contain ONLY
   unambiguous arrival verbs (`comes up`, `climbs to`, `arrives`, `reaches them`, `joins them`,
   `steps onto`) and must never re-borrow the sibling exit-edge lexicon. Verified safe: no
   existing `seam_entrance` test fixture uses these tokens as an arrival signal (fixtures use
   `arrived` / `marched`), and `gap_detectors._REPOSITION_TOKENS` is a separate constant
   unaffected by this purge.

**Conditional fix -- first-occurrence anchoring (NOT authorized as-bundled).** The cited
10030-BC defect is fully cleared by the lexicon purge alone (the only clearing token was the
death-fall `into the water`), so the any-occurrence scan is not condemned by the cited evidence.
First-occurrence anchoring of `_name_has_arrival_signal` is therefore admitted to THIS FR **only
if** it ships with its own independent condemnation and a false-positive guard (see ACs);
otherwise it is deferred to a separate FR.

The negation-blindness of the on-page check itself (FR-538 known limitation: "of Arnulf there
was no sign" reads as on-page) is **out of scope** here.

## Acceptance Criteria

**Binding (lexicon-hygiene fix):**

- [x] RED test (committed separately, `SKIP=pytest`) reproducing 10030-BC Ch3: a roster
      entrant absent from prior prose, first appearing as "was already with them", with a later
      same-chapter fall/exit sentence (`into the water`) → asserts `gap_count == 1` (currently
      0). This unit test -- NOT the 10030-BC re-run -- is the binding success gate.
      (`test_exit_fall_sentence_does_not_clear_unbridged_entrance`, commit `ce80258d`).
- [x] Reposition/exit tokens removed from `_ESTABLISH_TOKENS` (`into the water`, `slips`,
      `loses footing`, `down the bank`, `goes back`, `back for`; `descends`/`descended` audited
      and also removed as dual-sense descent); the establish set documents that it must never
      re-borrow `_REPOSITION_TOKENS`.
- [x] Existing FR-538/FR-539 fixtures still pass (genuine narrated arrivals still clear).
- [x] Changelog fragment (`type: fix`, `scope: examples`, no `req:` — example-exempt).
- [x] Distill diary entry (name the lexicon-provenance / `false_duplicate` trap: borrowing the
      sibling edge's vocabulary).

**Conditional (only if first-occurrence anchoring is kept in THIS FR -- else defer to a new FR):**

- [~] DEFERRED. The lexicon purge alone clears 10030-BC, so the any-occurrence scan is NOT
      condemned by the cited evidence (Condition 1). First-occurrence anchoring + its two guard
      tests are deferred to a separate FR if independent evidence ever surfaces (a legitimate
      arrival token at a later occurrence clearing an unbridged first appearance).
- [~] Independent RED test condemning the any-occurrence scan — deferred (see above).
- [~] False-positive guard test — deferred (see above).
- [~] `_name_has_arrival_signal` anchored to the entrant's first on-page occurrence — deferred;
      `_name_has_arrival_signal` is UNCHANGED by this FR.

**Corroboration (advisory, not a gate):**

- [ ] 10030-BC witness re-run reports the Arnulf Ch3 entrance as a gap (evidence only; `story.json`
      is a regenerable artifact).

## Alternatives Considered

- **Negation-aware on-page detection** (handle "no sign of Arnulf"): larger, separate concern;
  does not fix this defect (Arnulf *is* genuinely absent from Ch1/Ch2 here, not described as
  absent). Deferred.
- **LLM-judged arrival establishment**: heavier and non-deterministic; defeats the witness's
  purpose as a cheap per-run signal. Rejected for the witness layer.
- **Bundling first-occurrence anchoring with the lexicon purge** (original Fix 1 + Fix 2): one
  piece of evidence (10030-BC) cannot justify two independent code changes (`spec_kill`/`purge`).
  Anchoring is admitted only with its own condemnation + guard, else deferred. See Judgement.

## Related

- `examples/dungeon_master/api/seam_entrance.py` — `_name_has_arrival_signal`, `_ESTABLISH_TOKENS`
- `feature-requests/FR-538-dm-v2-seam-entrance-witness.md` (the witness this corrects)
- `feature-requests/FR-539-dm-v2-seam-aware-final-cut.md` (consumer of the witness number)
- Evidence: `outputs/dungeon-master/10030-BC/story/story.json` (Ch3), `review.md` break #2
- Memory: `/memories/repo/seam-entrance-roster-vs-nonroster.md`

## Judgement (2026-06-20) — APPROVED with conditions

**Bug confirmed real (code + human ground truth).** Verified against the live source:

1. `_name_has_arrival_signal` (seam_entrance.py:112) scans **every** occurrence of the name
   (the `while True` / `start = i + len(needle)` loop) and returns on the first establish-token
   hit anywhere — the any-occurrence clear (root cause 1) is real.
2. `into the water`, `slips`, `loses footing`, `down the bank`, `goes back`, `back for` are all
   present in `_ESTABLISH_TOKENS` (root cause 2) — real.
3. The reviewer LLM independently flagged the Ch3 Arnulf entrance by hand (review break #2), so
   the witness's `gap_count == 0` is a **confirmed false negative**, not a disputed reading.

**Stronger root cause than stated (fold into the fix).** Those inversion-prone tokens are a
verbatim copy of `gap_detectors._REPOSITION_TOKENS` (gap_detectors.py:60) — the **exit-edge,
movement-toward-hazard** lexicon (`slips`, `loses footing`, `into the water`, `off the ledge`).
The entrance witness borrowed the **opposite edge's** vocabulary: tokens that describe an actor
moving *toward death* were enlisted as *arrival* signals. The defect is not "a few bad words" —
it is a lexicon-provenance error. Reframe Fix 2 as a **lexicon-hygiene** correction: the establish
set must contain ONLY unambiguous arrival verbs and must NEVER borrow reposition/exit verbs from
the sibling. The audit must explicitly cover `goes back`, `back for` (departure sense),
`descends`/`descended` (dual-sense), and `down the bank` in addition to the cited `into the water`,
`slips`, `loses footing`.

**Condition 1 — two fixes, one piece of evidence (avoid over-scope; `purge`/`spec_kill`).** The
cited 10030-BC defect is fully resolved by EITHER fix alone: the first Arnulf occurrence ("was
already with them") carries no establish token, so anchoring alone flags it; and the only clearing
token is the death-fall `into the water`, so the lexicon purge alone flags it. One defect cannot
justify two independent code changes. **The token-purge (Fix 2) is the binding root-cause fix
(`the_one_law` — the defect is born at the lexicon, fix it there).** The first-occurrence anchoring
(Fix 1) must either be (a) **deferred to its own FR**, or (b) kept here ONLY if condemned by its
**own** RED test — a legitimate arrival token sitting at a LATER occurrence that clears an
unbridged FIRST appearance (a case the lexicon purge does not catch) — proving anchoring is
independently necessary.

**Condition 2 — anchoring carries a false-positive risk; guard it.** Strict first-occurrence
anchoring inside the 60-char window converts a legitimate but slightly-delayed arrival into a
false gap (e.g. "Arnulf stood frozen. A breath later he climbed up to join them." — `climbed` >60
chars from the first mention). Since this witness GATES FR-539's seam-aware Final Cut, a false
positive forces needless revisions. If Fix 1 is kept, it MUST ship with a guard test: a legitimate
delayed arrival still clears. Without that guard, ship Fix 2 alone.

**Condition 3 — bind the criterion to the unit test, not the story re-run.** The "10030-BC witness
re-run reports a gap" AC is **advisory corroboration only**: `story.json` is a regenerable
artifact (a 10030-BC was just re-generated), so it is not a stable gate. The binding success
criterion is the committed RED→GREEN unit test reproducing the mechanism (unbridged first
appearance + later same-chapter fall sentence → `gap_count == 1`). Keep the re-run as evidence,
not as the gate.

**Scope ruling.** APPROVED for the **lexicon-purge fix (Fix 2), reframed as lexicon hygiene**, with
the RED unit test as the binding gate. The **anchoring (Fix 1) is NOT authorized as-bundled** —
either defer it to a separate FR, or fold in the two extra tests (independent-condemnation +
false-positive guard) that Conditions 1–2 require. The LLM-judge alternative is correctly rejected
for the witness layer (the witness must stay a cheap, deterministic per-run signal; FR-539 is the
actual remedy). Effort drops to ~0.25d for Fix 2 alone; ~0.5d if anchoring is properly tested.
Return to Enforce once the scope is narrowed and Conditions 1–3 are folded into the ACs.

## Implementation (2026-06-20) — Enforced

Binding lexicon-hygiene fix landed via TDD; anchoring deferred per Condition 1.

- **RED** (`ce80258d`, `SKIP=pytest`): `test_exit_fall_sentence_does_not_clear_unbridged_entrance`
  in `examples/dungeon_master/tests/test_seam_entrance_gap.py` reproduces 10030-BC Ch3 — Arnulf
  absent from Ch1/Ch2 prose, first appearing "was already with them on the higher stone" (no
  arrival token), then a later same-chapter death-fall "slid off the ledge and dropped into the
  water below". Asserted `gap_count == 1`; confirmed failing at `gap_count == 0`.
- **GREEN**: purged the exit-edge tokens from `_ESTABLISH_TOKENS` in
  `examples/dungeon_master/api/seam_entrance.py` — removed `into the water`, `slips`,
  `loses footing`, `down the bank`, `goes back`, `back for`, and the dual-sense
  `descends`/`descended`. Added a LEXICON HYGIENE docstring forbidding re-borrowing
  `gap_detectors._REPOSITION_TOKENS`. `_name_has_arrival_signal` is UNCHANGED (any-occurrence
  scan retained — not condemned by the cited evidence).
- **Verification**: full DM suite 365 passed; seam-entrance (14) + seam-precondition green; ruff
  check / ruff format --check / vulture all clean. `gap_detectors._REPOSITION_TOKENS` unaffected
  (separate constant); no seam_entrance fixture relied on the purged tokens as arrival signals.
- **Deferred**: first-occurrence anchoring (Fix 1) + its independent-condemnation and
  false-positive-guard tests — opened as future work if a later-occurrence false clear ever
  surfaces that the lexicon purge does not catch.
