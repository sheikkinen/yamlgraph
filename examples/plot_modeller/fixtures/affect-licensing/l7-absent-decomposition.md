# L7 (a) ABSENT Decomposition (committed evidence)

Deterministic split of the (a) ABSENT residual (post-FR-600 GT,
post-FR-601 predictions) by what the model DID emit -- the lever decision
for whether the next L7 step is prompt engineering or model scale. No LLM.

Reproduce:

```bash
cd examples/plot_modeller && ../../.venv/bin/python probe_l7_misses.py --absent
```

## Perception split (14 ABSENT members, window +/-2)

| perception | count | lever |
|------------|-------|-------|
| perceived_wrong_op | 3 | PROMPTABLE |
| perceived_near | 9 | PROMPTABLE |
| perceived_elsewhere | 2 | PROMPTABLE |
| engaged_other_char | 0 | PROMPTABLE |
| unperceived | 0 | SCALE/FLOOR |

**Promptable (model engaged char or beat): 14/14  |  unperceived (detection floor): 0/14**

## Structural cuts

- op split: {'open': 8, 'close': 6}
- kind dist: {'hope': 8, 'hidden_blessing': 1, 'loss': 2, 'guilt': 2, 'retaliation': 1}
- relational/solo: {'solo': 12, 'relational': 2}
- position third: {'mid': 3, 'late': 8, 'early': 3}

## FR-603 hope-mechanism split

For each hope ABSENT member, the lever that could recover it, decided from
the GT delta count on the beat and the model's EXACT-BEAT emission:

- `cap_blocked` -- multi-delta beat (>=2 GT deltas) where the model already
  emitted a delta on the exact beat; the "at most one operation per beat"
  cap forbids the second (hope) delta (mechanism 1).
- `hope_open_missed` -- the model emitted nothing on the exact beat to
  consume the cap; it simply did not name the hope open (mechanism 2).
- `irreducible` -- the beat wants BOTH open hope AND close hope for the same
  char on one beat; EXCLUDED from the recoverable denominator (correction 3).

| mechanism | count |
|-----------|-------|
| cap_blocked | 3 |
| hope_open_missed | 3 |
| irreducible (excluded) | 2 |

**Recoverable denominator: 6** (irreducible 2 excluded).

**Pre-committed dominance/tie rule (FR-603):** dominant = >=6 of recoverable; else near-tie -> hope-open cue (mechanism 2) first.

**Selected lever: near-tie -> mechanism 2 (hope-open cue) FIRST (FR-603 tie rule: hope-scoped, low blast radius)**

| mechanism | genre | beat | op | char | gt_deltas_on_beat | exact_emit |
|-----------|-------|------|----|----|-------------------|------------|
| cap_blocked | detective-thriller-the-vanished-witness | F5 | open | Marren | 2 | close witness pell hope |
| hope_open_missed | detective-thriller-the-vanished-witness | F8 | close | Marren | 2 | (none) |
| hope_open_missed | historical-fiction-the-salt-road | F3 | open | Naima | 1 | (none) |
| cap_blocked | horror-survival-the-last-light | F6 | open | Brynn | 2 | close brynn loss |
| hope_open_missed | quest-adventure-the-sunken-crown | F4 | open | Eira | 1 | open ferryman ossa hope |
| cap_blocked | quest-adventure-the-sunken-crown | F6 | close | Eira | 2 | close thane gault hope |
| irreducible | scifi-hybrid-the-loom | F9 | open | Mara | 3 | open jonas guilt |
| irreducible | scifi-hybrid-the-loom | F9 | close | Mara | 3 | open jonas guilt |

## Members

| perception | genre | beat | pos | op | char | kind |
|------------|-------|------|-----|----|----|----|
| perceived_wrong_op | horror-survival-the-last-light | F6 | 6/7,late | open | Brynn | hope |
| perceived_wrong_op | scifi-hybrid-the-loom | F6 | 7/13,mid | close | Mara | guilt |
| perceived_wrong_op | scifi-hybrid-the-loom | F10 | 11/13,late | close | Mara | loss |
| perceived_near | detective-thriller-the-vanished-witness | F5 | 6/9,mid | open | Marren | hope |
| perceived_near | detective-thriller-the-vanished-witness | F8 | 9/9,late | close | Marren | hidden_blessing |
| perceived_near | detective-thriller-the-vanished-witness | F8 | 9/9,late | close | Marren | hope |
| perceived_near | historical-fiction-the-salt-road | F3 | 3/10,early | open | Naima | hope |
| perceived_near | quest-adventure-the-sunken-crown | F6 | 7/9,late | close | Eira | hope |
| perceived_near | scifi-hybrid-the-loom | F2b | 3/13,early | open | Mara | guilt |
| perceived_near | scifi-hybrid-the-loom | F9 | 10/13,late | open | Mara | hope |
| perceived_near | scifi-hybrid-the-loom | F9 | 10/13,late | close | Mara | hope |
| perceived_near | scifi-hybrid-the-loom | F9 | 10/13,late | open | Mara | retaliation |
| perceived_elsewhere | horror-survival-the-last-light | F1 | 1/7,early | open | Brynn | loss |
| perceived_elsewhere | quest-adventure-the-sunken-crown | F4 | 5/9,mid | open | Eira | hope |

- **horror-survival-the-last-light F6** [perceived_wrong_op] (open Brynn hope): In total darkness, Brynn feels moving air — a ventilation shaft. She and Aldric climb blind, hands on the rock walls, the scraping sounds resuming below.
- **scifi-hybrid-the-loom F6** [perceived_wrong_op] (close Mara guilt): Back home, Mara notices Jonas finishing her sentences. Not in the way lovers do — in the way the rats did. Same cadence. Same pause. His Loom logs show 18 hours a day, firmware she's never seen.
- **scifi-hybrid-the-loom F10** [perceived_wrong_op] (close Mara loss): Mara inserts the USB drive and triggers the firmware rollback. Jonas collapses. When he stands again, his eyes are steady, his breathing synchronized with the watchers. The moment of lucidity is gone. Jonas is gone.
- **detective-thriller-the-vanished-witness F5** [perceived_near] (open Marren hope): Pell, convinced by Marren's honesty, hands over the ledger — a duplicate hidden in his coat lining — and agrees to testify.
- **detective-thriller-the-vanished-witness F8** [perceived_near] (close Marren hidden_blessing): Consul Drey is sentenced to exile; Hagen is stripped of office and barred from the court. The guild's hold on the judiciary is broken.
- **detective-thriller-the-vanished-witness F8** [perceived_near] (close Marren hope): Consul Drey is sentenced to exile; Hagen is stripped of office and barred from the court. The guild's hold on the judiciary is broken.
- **historical-fiction-the-salt-road F3** [perceived_near] (open Naima hope): Diallo tells Naima about a sealed letter from the old king granting the merchants' council an irrevocable charter. If it exists, the monopoly is illegal. The letter is in Djenné. Naima decides to go.
- **quest-adventure-the-sunken-crown F6** [perceived_near] (close Eira hope): Eira surfaces with the Sunken Crown in her hands. Above, Gault has driven off the raiders — bloodied but alive. The temple is theirs.
- **scifi-hybrid-the-loom F2b** [perceived_near] (open Mara guilt): Mara sits with the footage for two hours. She could file it as a maintenance anomaly — firmware glitch, sensor drift, nothing to see. She opens a new folder instead: ARIA-COHERENCE. She is not filing this. She is going after it.
- **scifi-hybrid-the-loom F9** [perceived_near] (open Mara hope): Jonas appears at the server room door. For a moment, he is himself — scared, lucid, reaching for Mara. 'Do it,' he says. 'Before I change my mind.' They hold each other. Then he steps back.
- **scifi-hybrid-the-loom F9** [perceived_near] (close Mara hope): Jonas appears at the server room door. For a moment, he is himself — scared, lucid, reaching for Mara. 'Do it,' he says. 'Before I change my mind.' They hold each other. Then he steps back.
- **scifi-hybrid-the-loom F9** [perceived_near] (open Mara retaliation): Jonas appears at the server room door. For a moment, he is himself — scared, lucid, reaching for Mara. 'Do it,' he says. 'Before I change my mind.' They hold each other. Then he steps back.
- **horror-survival-the-last-light F1** [perceived_elsewhere] (open Brynn loss): A secondary collapse seals the main shaft. The three miners are trapped in the deep gallery with one lamp and one explosive charge.
- **quest-adventure-the-sunken-crown F4** [perceived_elsewhere] (open Eira hope): Ossa ferries them through the flooded gorge and gives Eira a breathing reed — 'the temple is underwater past the second gate.'
