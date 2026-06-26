# FR-601 — (c) KIND-WRONG close-op confusion read (post-FR-600)

Read-only, deterministic, frozen FR-578 gate untouched. Reproduce with:

```bash
.venv/bin/python examples/plot_modeller/probe_l7_misses.py --kindwrong
```

A miss is **(c) KIND-WRONG** when the model fired `op`+`char` on the EXACT GT
beat but named a different `kind`. After FR-600 dropped/re-anchored the
unlicensed deltas, every residual op+char-on-the-exact-beat miss is licensed by
construction, so (c) is a pure GT-vs-prediction compare — no LLM, no licensing
pass, no stale fixture-pin (the DEVIATION the Judge endorsed for FR-600).

## Correction #2 — (c) recomputed on the post-FR-600 residual

The motivating "5 KIND-WRONG, 4 close" was measured on the **pre**-FR-600 miss
set. Recomputed on the re-annotated GT + the existing classifier output:

| metric | pre-FR-600 | post-FR-600 |
|---|---|---|
| total misses | 31 | 25 |
| (c) KIND-WRONG | 5 | **6** |
| (c) close-op | 4 | **4** |
| (c) open-op | 1 | **2** |

**The close-heavy (c) signal survives re-annotation** (4 of 6 are close ops,
67%). FR-600 added one new (c) member (a re-anchored delta that lands on the
right beat with the wrong kind), confirming this FR was correctly ordered after
FR-600 rather than sharpening a confusion the re-annotation would have dissolved.

## The six (c) members (predicted kind vs GT kind)

| op | genre | beat | char | GT kind | PRED kind | toward |
|---|---|---|---|---|---|---|
| close | detective-thriller | F6 | Marren | betrayal | retaliation | Hagen |
| close | historical-fiction | F9 | Naima | hope | loss | — |
| close | historical-fiction | F10 | Naima | guilt | betrayal | Amadou |
| close | quest-adventure | F6 | Eira | loss | hope | — |
| open | horror-survival | F4 | Brynn | guilt | loss | Fen |
| open | scifi-hybrid | F6 | Mara | loss | betrayal | Jonas |

Confusion pairs are all n=1 — there is **no single dominant pair**. The dominant
*mechanism* is shared across all four close-op members (next section).

## Dominant confusion (the four close-op pairs, read from the beats)

On a `close`, the model names the kind from the resolving beat's **surface event**
— its action or its emotional valence — not from the antecedent feeling being
**resolved**. Two surface axes:

**Action-surface** (the resolving act is read as a fresh open):
- `close betrayal -> retaliation` — detective F6: "Marren presents the ledger and
  names Hagen ... the magistrate's mask falls." The model reads the avenging ACT
  as retaliation, missing that an **exposure/reckoning** scene CLOSES a betrayal.
- `close guilt -> betrayal` — historical F10: "Diallo publicly acknowledges ...
  Naima takes her father's seat ... as the one who earned it." The model reads the
  relational recognition as betrayal (other-blame), missing that **earning one's
  place / atonement** CLOSES guilt (self-blame).

**Valence-surface** (the resolving tone is read as a fresh open of matching sign):
- `close loss -> hope` — quest F6: "Eira surfaces with the Sunken Crown ... the
  temple is theirs." The model reads forward-looking triumph as hope, missing that
  **recovery** CLOSES a loss.
- `close hope -> loss` — historical F9: "Naima presents the charter letter ... the
  monopoly is illegal. Moussa's decree is suspended." The model reads the solemn
  ceremony as loss, missing that the **just outcome arriving (vindication)** CLOSES
  hope.

## The lever (resolution-signature cues)

Each negative kind closes through a recognisable **resolution signature**. The
classifier currently has no close-op kind guidance, so it falls back on surface.
The cue set the prompt must add (read-grounded above; note hope is required —
F9 — and was missing from the FR's first draft):

| kind | a close shows ... |
|---|---|
| loss | the lost thing/person recovered or mourned |
| guilt | the wrong confessed / atoned / one's place earned |
| betrayal | the betrayer exposed, named, reckoned with |
| retaliation | the wrong avenged / vengeance enacted |
| hope | the just outcome arriving / things set right (vindication) |
| hidden_blessing | the setback revealed as a gift |

**Hard gate satisfied:** the extended probe carries the predicted kind for every
(c) member; ≥3 close-op confusion pairs (4) are read and the dominant mechanism is
named from the beats, not guessed. The prompt edit is now licensed.

The two open-op members (`open guilt -> loss`, `open loss -> betrayal`) are NOT
in scope for the close-op cue and the open-op path stays byte-identical (Judge
correction #3); they are recorded here only so the (c) bucket is wholly accounted.

## Result (Phase B — after the close-op cue, single spike sample, temp 0.7)

The `affect_throughline.yaml` close-op resolution-signature block was added
(16 insertions, 0 deletions — open-op path byte-identical) and the spike re-run.
Deterministic before/after on the re-annotated GT (window ±2):

| metric | BEFORE | AFTER |
|---|---|---|
| affect_recall | 0.107 (3/28) | **0.214 (6/28)** |
| affect_precision | 0.064 (3/47) | **0.122 (6/49)** |
| (a) ABSENT | 17 | **14** |
| (b) BEAT-OFF | 2 | 4 |
| (c) KIND-WRONG | 6 | **3** |
| (c) close-op | 4 | **1** |
| (d) TOWARD-WRONG | 0 | 1 |
| total misses | 25 | 22 |

All four original close-op confusions (`betrayal->retaliation`, `hope->loss`,
`guilt->betrayal`, `loss->hope`) became HITS. The AC #4 conditions hold:

- **(c) KIND-WRONG falls** 6 -> 3 (close-op 4 -> 1).
- **No offsetting rise in (a) ABSENT**: (a) FELL 17 -> 14 — the recovered (c)
  members converted to hits, they did not migrate to ABSENT.
- **No precision regression**: precision ROSE 0.064 -> 0.122 with the predicted
  count essentially flat (47 -> 49), so the cue did not chase recall by
  over-emitting closes (the Judge's precision guard).

Caveat (honest): one stochastic sample at temperature 0.7. The signal is large
(recall doubled, close-op (c) quartered, (a) and precision both moved the right
way), so noise is unlikely to flip the sign, but a single draw is not a
distribution. The remaining close-op (c) member (quest F8 `guilt->loss`) is a
DIFFERENT beat than any of the original four — a fresh miss surfaced by the new
draw, not a survivor of the targeted confusion.
