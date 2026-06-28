# FR-600 — L7 affect-recall after experiential re-anchoring (committed durable report)

Reproducible from committed artifacts only (no live LLM call):
- selection: `fr600-unlicensed-frozen.yaml` (the human-confirmed 12-member verdict)
- model output: `results/l7/<genre>.yaml` (unchanged FR-598 classifier output, gitignored)
- ground truth: `fixtures/ground-truth/*.yaml` (this FR's edit) vs the same at git HEAD~ (pre-edit)
- gate: `evaluate.py` `_l7_counts` / `_load_gt_affects` (FROZEN, unmodified — verified by diff)

## 1. Both-denominator recall (correction #3 — anti-gaming)

The model output is held fixed. Only the ground truth changes (7 re-anchored, 5 dropped).

| measure | hits | denom | affect_recall | meaning |
|---|---|---|---|---|
| baseline (pre-edit GT)      | 2 | 33 | 0.061 | — |
| re-anchor only (denom held 33) | 3 | 33 | 0.091 | **pure model-skill gain** |
| + drop effect (denom -> 28) | 3 | 28 | 0.107 | denominator shrink |

- Re-anchor gain in hits: **+1** delta converted miss -> hit (genuine model skill; denominator fixed).
- Drop removed **5** hard false deltas from the denominator (NOT model skill).
- Reporting only the post-drop 0.061 -> 0.107 (a +75% relative jump) would overstate the
  improvement: most of the apparent rise is the denominator shrinking, not the model improving.

## 2. Former-(e)=12 re-partition (deterministic, no LLM)

Each of the 7 re-anchored deltas now sits on a beat the frozen verdict certified as licensed,
so each is re-bucketed deterministically at its target beat (HIT, or a/b/c/d via the probe's
`_classify_licensed`, window +/-2). The 5 dropped deltas leave GT entirely.

| outcome | count | lever it now names |
|---|---|---|
| dropped (removed from GT) | 5 | annotation over-reach — corrected at source |
| HIT (model already predicted it) | 1 | none — recovered |
| (a) ABSENT | 5 | model scale (FR-578 / reserved escalation) |
| (c) KIND-WRONG | 1 | six-kind taxonomy (FR-601) |
| (e) UNLICENSED remaining | 0 | — collapsed by construction |

Per-member:

| genre | target | op | char | kind | outcome |
|---|---|---|---|---|---|
| detective-thriller | F2  | open  | Marren | loss        | HIT |
| horror-survival    | F4  | open  | Brynn  | guilt       | c_kind_wrong |
| horror-survival    | F6  | close | Brynn  | loss        | a_absent |
| scifi-hybrid       | F2b | open  | Mara   | guilt       | a_absent |
| scifi-hybrid       | F6  | close | Mara   | guilt       | a_absent |
| scifi-hybrid       | F9  | close | Mara   | hope        | a_absent |
| scifi-hybrid       | F9  | open  | Mara   | retaliation | a_absent |

## 3. Reading

Re-annotation was a real data fix — but it does NOT convert (e) misses into hits. It recovered
exactly **one** hit; the other six re-partition into (a) ABSENT (5) and (c) KIND-WRONG (1), the
two levers FR-578 (model scale) and FR-601 (taxonomy) already own. This confirms the FR-599
MULTI-CAUSE verdict empirically: the (e) bucket was an annotation error, and correcting it
reveals — rather than hides — the model's remaining failures on those beats.

## 4. Side effect (observation, out of scope)

The 5 dropped deltas were all `open` operations whose matching `close` lives on a later beat
(historical F7 guilt closes at F10; quest F1 guilt closes at F8; quest F5 loss closes at F6).
Dropping the opens leaves three `close`-without-`open` deltas in GT. The closure validator
(`validators/affects.py`) only flags `open`-without-`close`, and it runs on model output, not
GT, so neither the gate nor the validator errors. Whether those orphan closes are themselves
licensed is a separate question for a future re-annotation pass — explicitly NOT in this FR's
frozen 12-member scope.
