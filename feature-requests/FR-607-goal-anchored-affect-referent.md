# Feature Request: Goal-anchored affect referent (L2 -> L7 isolation spike)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** CLOSED — REFUTED (2026-06-26). Honest lift +0.000: injecting goals did not move localization; referent-binding 0.143 even at the GT ceiling. Instruments (GT referents, additive scorer, validator, leak audit) retained; production goal-anchoring not promoted.
**Effort:** 1.5 days (spike + GT enrichment)
**Requested:** 2026-06-26

## Summary

Test the FR-605 post-mortem hypothesis directly: **L7 affect recall floors because each
emotion is detected without a referent — the goal it is about.** Every affect kind is a
goal relation (hope = a goal looks reachable; loss = a goal/possession is lost; guilt =
the agent harmed another's goal; betrayal = an ally defects from a shared goal). The
pipeline already computes goals at **L2** and goal causality at **L6**, but L7 runs on L3
glosses + L4 kinds *only* — blind to the very layer that holds the referent.

This FR (a) enriches the ground truth with a `referent: <goal_id>` on each affect delta,
(b) runs an **isolation spike** that feeds GT L2 goals to the affect detector and binds
each emotion to a goal, and (c) adds a **referent-aware scoring mode** that counts a hit
if the affect lands on any beat where its goal opens/closes — so a text-valid anchor the
annotator did not pick is no longer scored as a miss. Frozen `main_l7` stays untouched;
the new mode is additive and separately named.

## Value Statement

If emotions are goal-relational, anchoring each affect to an L2 goal should recover the
signature arcs the FR-605 two-pass left "wrong" (bereavement-loss vs entrapment-loss),
turning a brittle single-beat recall into a grounded-referent recall — the first lever in
the arc aimed at *which thing the emotion is about* rather than *where it sits*.

## Problem

L7 `affect_recall` sits at **0.214** and the entire lever inventory — character pinning,
budget, precision, per-kind decomposition, model-scale, and two-pass localization — has
been spent and *measured* (FR-596 -> FR-605). FR-605's prose-grounded post-mortem named
the residual cause precisely: the `wrong_beat` bucket (39% of misses after two-pass; 71%
before) **masks a referent mismatch, not localization drift.** Read against the prose:

- **Horror loss:** GT = entrapment, opens F1 (*"a collapse seals the main shaft ...
  trapped"*), closes F6 (*"feels moving air — a ventilation shaft"*). Model = bereavement,
  opens F4 (*"the Watcher takes him ... Fen is gone"*), never closes. Two different goals
  ("escape" vs "keep my companions"); both text-valid.
- **Quest hope:** GT closes F6 (*"surfaces with the Sunken Crown"* — the quest goal met);
  model closes F8 (*"the lack is liquidated"* — the kingdom-saving goal met). Two goals,
  proximate vs terminal; both grounded.

Two-pass cannot fix this because pass 1 names `loss`/`hope` **with no referent**, and pass
2 faithfully locates whatever pass 1 named. The missing signal is *which* goal, not
*where* the beat is. Separately, pass-1 SET recall was 0.50 and blind to the relational
kinds (`guilt` 1/4, `betrayal` 0/2) — exactly the kinds that are L1/L6 relations, the
layers L7 is starved of. The referent the detector lacks already exists one layer up.

## Raw Output Read (measurement / metric-tooling FRs only)

This FR adds a scoring mode (`_l7_counts` referent-aware variant), so the raw-output read
is mandatory.

- **Samples read:** the FR-605 two-pass draw dumps
  `examples/plot_modeller/results/l7_twopass/throughlines/draw1/{quest,horror}/*.yaml`,
  read against the gold beat prose in `fixtures/ground-truth/{genre}.yaml` (the goal and
  function fields, not just affect deltas).
- **What I saw (concrete, not generatable):**
  - Horror `loss.yaml` emitted `{open: F4, close: null}`. F4's gloss is *"Fen stumbles ...
    the Watcher takes him ... Fen is gone"* — a bereavement, which honestly never closes,
    so `null` is correct *for that referent*. GT's loss is the F1 entrapment that closes
    when air is found at F6. The model located its referent perfectly; it chose a different
    goal. A bare beat-id scorer calls this a total miss (F4!=F1, null!=F6); a goal-aware
    scorer would see two distinct goals and score each on its own anchor.
  - Quest `hope.yaml` emitted `{open: F4, close: F8}`. F8's gloss is *"places the Crown on
    Queen Livia's head ... the lack is liquidated"* — literally the L4 `liquidation`
    function, i.e. the **kingdom goal**, not the **crown-retrieval goal** GT scoped (F6,
    the L4 `victory`). The two closes are two different Proppian goal resolutions in the
    same arc.
  - Pass-1 set blindness is goal-shaped too: `guilt`/`betrayal` (named 1/4, 0/2) are the
    kinds whose referent is *another agent's* goal (L1 toward + L6 threatens) — unreadable
    from a single protagonist's beats without the relational layer.

## Proposed Solution

Three additive parts; none touches frozen `main_l7`.

```yaml
# 1. GT enrichment — add a referent to each affect delta (leak-audited).
#    fixtures/ground-truth/<genre>.yaml, per eff_affect entry:
#    - { op: close, kind: loss, char: Brynn, referent: goal_escape }
#    referent ids reference the existing L2 goals block in the same file.

# 2. Isolation spike — affect_locate_goal.yaml (forked, not replacing affect_locate):
#    in:  protagonist, kind, glosses, GT L2 goals (id + one-line desc), L6 threatens/motivation
#    out: { open: <beat|null>, close: <beat|null>, referent: <goal_id>, ... }
#    The detector must bind each emotion to one goal id from the supplied L2 set.

# 3. Referent-aware scoring mode — evaluate._l7_counts_referent (NEW, additive):
#    a predicted (op, kind, referent) scores a recall hit if it lands on ANY beat
#    where that goal opens/closes in GT — not only the single annotated beat.
#    Precision still guards ungrounded invention (a referent not in the L2 set,
#    or a beat the goal never touches, is a false positive).
```

- **Two isolation modes, both legitimate, reported separately:** (A) GT goals injected
  (tests the *ceiling* — does a perfect referent recover the arcs?); (B) model L2 goals
  injected (tests the *production path* — but L2/FR-574 is REVISE, so noise is expected
  and the gap A-B is the upstream-error cost). Run A first; only run B if A clears.
- **Leak audit (mandatory, per FR-605 correction-3).** A GT goal description can
  half-announce the answer ("retrieve the crown" implies where hope closes). The spike
  must report, for each genre, whether the goal text contains a beat id or a verbatim
  beat phrase, and strip/paraphrase any that do before injection. A leak finding voids the
  A-mode result.
- **Frozen gate untouched.** `_l7_counts` / `main_l7` imported read-only; the
  referent-aware counter is a new function with its own name. The headline number stays
  arm A's bare-beat recall; the referent-aware recall is reported alongside as the
  hypothesis test, not as a gate change.
- **Verdict rule:** GO if referent-aware recall (mode A) clears the 0.50 REVISE line AND
  the two signature arcs (horror entrapment-loss, quest crown-hope) score as hits under
  goal anchoring; REFUTED if goal anchoring does not recover them (the referent is not the
  binding constraint after all); PARTIAL otherwise.

## Acceptance Criteria

- [x] **GT referent enrichment.** Each `eff_affect` delta in all 5 genres carries a
      `referent: <goal_id>` (28 deltas) referencing that file's named goal vocabulary
      (`motivation.goal`/`threatens.goal`, not the predicate `goals:` block — J corr 2);
      `evaluate.validate_referents` confirms every referent is in-vocab (0 violations).
- [x] **Leak audit passed.** `evaluate.audit_goal_descriptions` flagged one leak
      (`find_Pell`: "the one who") which was paraphrased; all 5 genres now clean. A
      witness test asserts the fixture stays leak-free.
- [~] **Isolation spike runs both modes.** `affect_locate_goal.yaml` binds each emotion to
      one goal id; mode A (GT goals) ran 3 draws @ temp 0.7 (band [0.250, 0.250] — flat).
      **Mode B was gated off**: it is run only if mode A clears KILL 0.50; mode A's
      ceiling stalled at 0.250, so mode B (production, necessarily <= ceiling) is moot.
      Justified deviation — the ceiling failure makes the production path unreachable.
- [x] **Referent-aware scoring is additive.** `evaluate._l7_counts_referent` is a NEW
      function; `_l7_counts` / `main_l7` / `_affect_matches` byte-identical (the only
      deletions in the diff are the unrelated SIM905 stopwords rewrite — verified
      line-by-line).
- [x] **Signature-arc recovery measured.** Horror entrapment-loss: GT F1 open loss
      -> reach_surface; mode A placed open=F4 close=F7 referent=protect_crew (MISS beat,
      MISS referent). Horror hope F6 -> reach_surface: mode A open=F6 (beat HIT) but
      referent=find_exit (MISS). Quest crown-hope F4 -> retrieve_crown: mode A open=F4
      (beat HIT) referent=legitimize_queen (MISS) — and control placed it IDENTICALLY
      (open=F4 close=F8). The arcs did not recover; cited in the verdict.
- [x] **Verdict recorded.** REFUTED (below).
- [x] **Relational-kind note.** Supplying the goal set did not raise set recall (0.500,
      identical to control) and the model bound the wrong goal for relational kinds
      (guilt -> protect_crew for an escape-loss). L1 toward + L6 threatens were not
      separately injected — the ceiling failure made deeper relational context moot.
- [x] Diary reflection added.

## Enforcement Outcome (2026-06-26) — REFUTED

**Build.** Deterministic GT enrichment inserted 28 `referent:` lines (additive only —
0 non-referent lines, 0 deletions). Three additive `evaluate.py` instruments:
`validate_referents`, `audit_goal_descriptions` (+`_word_ngrams`), `_l7_counts_referent`
(`_goal_vocab`, `_referent_beats`) — frozen `_l7_counts`/`main_l7`/`_affect_matches`
byte-identical. Forked prompt `affect_locate_goal.yaml` (binds a referent) + mini-L2
`affect_goals.yaml` (mode B). Leak-audited descriptions in
`fixtures/goal_descriptions.yaml`. 11 witness tests (`test_l7_referent.py`); 196/196
example tests pass. `AffectDelta` gained an optional `referent` field at the schema
boundary (the new GT key entered there, not downstream).

**Result (3 draws @ temp 0.7, near-deterministic — every draw identical):**

| arm | strict recall | relax recall | referent recall |
|-----|--------------:|-------------:|----------------:|
| arm A (FR-604 single pass) | 0.214 | — | — |
| control (FR-605 two-pass, no goals) | 0.250 | 0.250 | — |
| mode A (inject GT goals = ceiling) | 0.250 | 0.250 | 0.143 (cap: set-recall 0.500) |
| mode B (model goals) | SKIPPED (mode A < KILL) | | |

**HONEST LIFT (J corr 1) = mode A relax − control relax = +0.000.** The control arm
(the judge's primary correction) is decisive: mode A's 0.250 is *identical* to the
no-goal control. The +0.036 over arm A is the FR-605 two-pass decomposition alone, not
the goal signal. Injecting the goal — even the exact GT goal, leak-free, with realistic
distractors — moved localization by nothing.

**Why it failed.** Referent-binding is 0.143 (4/28): even handed the right goal in the
injected set, the model binds the *wrong* sibling goal ~86% of the time — `protect_crew`
for an escape-loss whose referent is `reach_surface`; `find_exit` and `legitimize_queen`
for hopes about `reach_surface`/`retrieve_crown`. The appraisal-theory premise (emotion =
appraisal relative to a goal) is sound as theory but, as a *prompt-time hint*, the goal
set does not disambiguate WHERE an emotion opens/closes — the placement was already
determined by beat salience and the model treats the goal list as a labelling afterthought.

**Disposition.** Production goal-anchoring is NOT promoted (frozen gate stays frozen;
mode B never reached). The durable instruments are RETAINED as the evidence trail and
for future appraisal work: the 28 GT referents (now part of ground truth), the additive
referent scorer, the validator, and the leak audit. The refuted prompts and harness are
kept as the recorded experiment (per the FR-604/605 spike convention).

## Alternatives Considered

- **Better beat-placement prompting (continue FR-605's direction).** Rejected by the
  FR-605 prose post-mortem: the arcs are not mislocated, they are differently-referred. A
  placement lever cannot fix a referent disagreement.
- **Inject *model* goals only (skip GT enrichment).** Rejected as the *first* step: L2 is
  REVISE-quality, so a null result would be unattributable (bad goals vs bad hypothesis).
  Mode A (GT goals) isolates the hypothesis; mode B measures the production penalty.
- **Change the frozen gate to be referent-aware.** Rejected: the gate is frozen for
  cross-FR comparability. The referent-aware counter is additive and separately named; any
  promotion to the gate is a later, separately-judged decision.
- **Add referent to the affect kind taxonomy (loss-of-X as distinct kinds).** Rejected:
  explodes the kind space and couples taxonomy to story content; a `referent` field on the
  delta keeps the kind set fixed and the referent data-driven from L2.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, with four corrections.** This is the substantive next lever
and it escalates *correctly* from a genuinely REFUTED predecessor: I confirmed FR-605 is
CLOSED—REFUTED, that correction-2 paid off (the bottleneck relocated to pass-1 SET recall
0.50, making the miss attributable), and that the post-mortem isolated the residual as
referent mismatch (wrong_beat fell 71%→39% yet the two signature arcs stayed "wrong" — not
mislocated, differently-referred). I verified the central architectural premise directly:
`affect_locate.yaml` and `affect_set.yaml` mention `goal` **zero times** — the detector is
truly blind to L2, while the goal vocabulary exists one layer up. The Raw Output Read is
present and substantive (the F4 bereavement-never-closes vs F1/F6 entrapment, and the F8
`liquidation`/kingdom-goal vs F6 `victory`/crown-goal split, both map to L4 functions
visible in the GT). The two-mode isolation (A = GT goals = ceiling; B = model goals =
production path) is exactly the attribution discipline this arc keeps paying to learn.
Four corrections bind the grant.

1. **(PRIMARY) The referent-aware scorer LOOSENS the matcher — control for scorer-relaxation
   before crediting goal-anchoring.** Counting a hit on "ANY beat where the goal opens/closes"
   widens the acceptance set from one annotated beat to several. That is a legitimate fix for
   the text-valid-different-anchor problem, but it mechanically inflates recall *independent
   of any model improvement* — a plausible-looking win that is really a looser ruler
   (`gate_checks_shape_not_substance`, one level up). Add the control arm: apply the SAME
   referent-aware scorer to FR-605's EXISTING (non-goal) two-pass draws. The honest lift is
   (goal-injected × referent-scorer) − (old two-pass × referent-scorer); if the relaxed
   scorer alone already lifts recall, the hypothesis is confounded and the verdict must say
   so. Precision-guarding invention is necessary but does NOT substitute for this control.

2. **(PRIMARY) The "L2 goals block" the FR references does not exist as described — key
   referents on the `motivation.goal` vocabulary.** Verified against the GT: the top-level
   `goals:` block holds world-state predicates (`pred: holds [Queen Livia, Sunken Crown]`),
   NOT named goal ids. The named goal vocabulary the FR wants (`retrieve_crown`,
   `legitimize_reign`, `guard_temple`, `prevent_coronation`, …) lives inside
   `functions[].motivation.goal` (and `threatens`). Therefore: (a) the `referent:` enrichment
   must reference that goal-name vocabulary; (b) the AC validator must check against it, not
   the `goals:` block; and (c) the "id + one-line desc" injected to the detector must be
   *assembled* from those goal names — and since no canonical descriptions exist, authoring
   them is the single fattest leak surface ("retrieve the Sunken Crown" half-announces where
   hope closes — the FR's own example). The leak audit must police the authored descriptions
   hardest, not just scan for beat ids.

3. **(secondary) Bind GO to a reachable production path, not a ceiling-only result.** Mode A
   injects perfect GT goals — a ceiling production can never reach (L2/FR-574 is REVISE). The
   verdict rule "GO if mode-A recall clears 0.50" could declare victory on an unreachable
   ceiling. Strengthen: a mode-A clear is hypothesis-CONFIRMED; reserve GO for when mode B
   (model goals) also beats arm A's 0.214 — otherwise PARTIAL (referent is the lever, but the
   production gain is gated on L2 quality, and the A−B gap names that debt).

4. **(secondary) Pass-1 SET recall (0.50) still caps the headline — anchoring pass 2 cannot
   recover a kind pass 1 never named.** FR-605 proved the bottleneck is now set-detection
   (guilt 1/4, betrayal 0/2 — the relational kinds). Referent-aware recall (mode A) cannot
   exceed ~0.50 regardless of perfect localization unless pass 1 also gets the relational
   layer. The FR's AC for L1-toward/L6-threatens raising guilt/betrayal set recall is the
   right probe — report referent-recall *conditioned on* set recall so the verdict states
   which constraint actually moved (localization vs set detection), not a blended number.

**Endorsed:** forked `affect_locate_goal.yaml` (not replacing), additive
`_l7_counts_referent` (frozen `_l7_counts`/`main_l7` byte-identical), mandatory leak audit
(inherits the FR-605 correction-3 skeleton guard, now confirmed implemented), ≥3 draws @
temp 0.7 with run-to-run band, mode A before mode B, headline stays arm A's bare-beat
recall. Correctly refuses to change the frozen gate.

**Frozen scope:** GT `referent` enrichment keyed on the `motivation.goal` vocabulary +
validator; leak-audited goal-description injection; `affect_locate_goal.yaml` binding each
emotion to one goal id; the additive referent-aware counter WITH the scorer-relaxation
control arm; mode A and mode B reported separately with the A−B gap; the two signature arcs
scored explicitly; referent-recall conditioned on pass-1 set recall; GO/PARTIAL/REFUTED per
the strengthened rule. Frozen `main_l7` untouched.

## Related
- `feature-requests/FR-606-affect-rationale-field.md` — the cheaper legibility sibling;
  the rationale field would make this spike's autopsy free.
- `docs/diary/diary-2026-06-26-the-emotion-had-the-wrong-referent.md` — the typed-referent
  seed this FR implements.
- `examples/plot_modeller/docs/architecture.md` — the L1..L7 layer stack (L2 goals, L6
  motivation/threatens).
- `examples/plot_modeller/evaluate.py` (frozen `_l7_counts`/`main_l7`),
  `examples/plot_modeller/prompts/affect_locate.yaml`,
  `examples/plot_modeller/fixtures/ground-truth/*.yaml` (L2 goals + affect deltas).
