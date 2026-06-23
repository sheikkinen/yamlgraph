# Fixture corpus — frozen snapshot (FR-570 J5)

These files are a **frozen snapshot**, copied (not referenced) so the L4 spike
corpus stays reproducible and immune to later edits in the source docs.

## Source

| Fixture | Source path |
|---------|-------------|
| `synopses/*.txt` | `examples/dungeon_master/docs/v5/*.txt` |
| `ground-truth/*.yaml` | `examples/dungeon_master/docs/v5/genre-plots/*.yaml` |

**Snapshot commit:** `d93f446d22ea94bd9bc61b980ec000ff4d92082f`
**Snapshot date:** 2026-06-23

## Self-derived corpus ceiling (J2)

The synopses were reverse-derived from the same plots whose `kind` fields are the
ground truth, and each `gloss` was authored alongside the label it must now be
classified into. Measured accuracy is therefore an **upper bound** — "recover the
author's label from prose the author wrote knowing it," not "classify
naturalistic prose." Any GO verdict is optimistic pending a blind-corpus re-test.

## Contents

| Genre | Functions | Notes |
|-------|-----------|-------|
| Detective thriller | 8 | villainy, lack, pursuit, donor_test, provision, exposure, recognition, punishment |
| Quest adventure | 8 | lack, departure, donor_test, provision, struggle, victory, return, liquidation |
| Horror survival | 7 | villainy, departure, pursuit, death, struggle, rescue, return |
| Sci-fi hybrid | 12 | villainy, lack, departure, donor_test, provision, pursuit, recognition, struggle, reconciliation, death, return, liquidation |

35 glosses covering 15 of 16 kinds (`exposure` n=1; `recognition` nearly so).
