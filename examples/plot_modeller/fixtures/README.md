# Fixture corpus — FR-570 snapshot + FR-572 retrofit + blind

These files are a **frozen snapshot** (FR-570 J5), retrofitted with the refined
17-kind / 6-affect vocabulary (FR-572 Phase 1a), plus one blind-authored synopsis
(FR-572 Phase 1b).

## Source

| Fixture | Source path |
|---------|-------------|
| `synopses/*.txt` (4 self-derived) | `examples/dungeon_master/docs/v5/*.txt` |
| `synopses/historical-fiction-the-salt-road.txt` | **Blind** — authored without seeing the 17-kind list |
| `ground-truth/*.yaml` (4 self-derived) | `examples/dungeon_master/docs/v5/genre-plots/*.yaml` |
| `ground-truth/historical-fiction-the-salt-road.yaml` | **Blind** — plan hand-authored after synopsis, with kind list visible |

**Original snapshot commit:** `d93f446d22ea94bd9bc61b980ec000ff4d92082f`
**Snapshot date:** 2026-06-23
**FR-572 retrofit date:** 2026-06-23

## Self-derived corpus ceiling (J2)

The 4 self-derived synopses were reverse-derived from the same plots whose `kind`
fields are the ground truth. Measured accuracy is an **upper bound**. The blind
synopsis (historical fiction) was authored without consulting the 17-kind list —
only the synopsis text was written blind; the ground-truth plan was hand-authored
afterwards with the kind list visible.

## Blind authoring process (FR-572 AC#5)

The synopsis "The Salt Road" was written as a pure story: characters, conflict,
setting, resolution — without the 17-kind vocabulary visible. The author did not
consult `vision.md`, `classify_kinds.yaml`, or any vocabulary reference during
synopsis writing. After the synopsis was complete, the ground-truth plan was
authored using the 17-kind list to classify each beat. This process is stated
here for honesty — it is not verifiable by CI.

## FR-572 Retrofit

The 4 self-derived plans were updated with:
- **mediation** beats (3 plans: detective, quest, scifi) — `lack` split where
  discovery and commitment were combined
- **hope** affect threads (4 plans) — opened by provision/rescue/mediation,
  closed by exposure/victory/death (or left unclosed in horror)
- **toward** on relational affects (4 plans) — guilt toward, betrayal toward,
  retaliation toward

## Contents

| Genre | Functions | Corpus | Notes |
|-------|-----------|--------|-------|
| Detective thriller | 9 | self-derived | +mediation, +hope, +toward |
| Quest adventure | 9 | self-derived | +mediation, +hope, +toward |
| Horror survival | 7 | self-derived | +hope (unclosed), +toward |
| Sci-fi hybrid | 13 | self-derived | +mediation, +hope, +toward |
| Historical fiction | 10 | **blind** | mediation, hope, toward included |

48 glosses covering 15 of 17 kinds across 5 genres. All 3 mediation beats
correctly classified. `exposure` n=2 (detective + blind), `punishment` n=1.

## FR-600 — Affect is anchored to the EXPERIENTIAL beat, not the causal one

An `eff_affect` delta belongs on the beat whose own gloss text *shows the feeling
being felt*, not on the beat that causes it. A character can be harmed on one beat
and visibly grieve on the next — the affect delta goes on the grieving beat.

FR-599's licensing probe found 12 ground-truth affect deltas anchored to beats
whose text did not license them (the "(e) UNLICENSED" bucket). FR-600 corrected
them against a human-confirmed frozen verdict (`affect-licensing/fr600-unlicensed-frozen.yaml`):
7 were re-anchored one beat forward to the experiential beat, 5 were dropped as
inferred-from-arc rather than shown on any nearby beat. See
`affect-licensing/fr600-gate-report.md` for the recall decomposition.

When authoring or extending the corpus: place each affect on the beat that
manifests it in text. If no beat shows the feeling, do not annotate it — affect
inferred from genre, role, or arc but absent from every gloss is not recoverable
by a beat-grounded model and inflates the denominator dishonestly.
