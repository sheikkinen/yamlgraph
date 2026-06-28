# Feature Request: FR-601 L7 Close-Op Kind Discrimination

**Priority:** MEDIUM
**Type:** Enhancement (prompt/taxonomy) — classifier change, frozen gate untouched
**Status:** Enforced — (c) close-op 4->1, recall 0.107->0.214, precision 0.064->0.122, (a) 17->14 (2026-06-26)
**Effort:** ~0.5 day (prompt clarification + spike re-run; one corpus pass)
**Requested:** 2026-06-26
**REQ:** REQ-YG-020 (reuse — no new CAP)
**Predecessor:** FR-599 (miss-decomposition probe — (c) KIND-WRONG = 16%, close-heavy 4/1)
**Gate (frozen, untouched):** FR-578 `affect_recall` (`main_l7` in `evaluate.py`)
**Lever this FR pulls:** six-kind taxonomy / close-op classifier hint — NOT model scale

## Summary

The FR-599 probe found that of the 5 KIND-WRONG misses (right beat, right op, right char,
wrong `kind`), **4 are `close` ops**. The model places a closing affect on the correct
beat but names the wrong kind. This FR sharpens the classifier's close-op kind
discrimination without touching the gate or buying a larger model.

## Value Statement

When the model already knows *where* an arc resolves and *who* it belongs to, it should
name the *kind* correctly — closing the cheap, in-reach share of the recall floor that is a
naming gap, not a perception gap.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, conditional on FR-600 and on the read landing first.** This
is correctly framed as investigation-then-fix: the FR's own Raw Output Read section
admits the dump does **not** yet carry the *predicted* mismatched kind, so no fix is
designed until the confusion pair is read. That honesty is exactly the
`read_raw_output_first` discipline and is endorsed. Three corrections bind it:

1. **No prompt edit until the extended probe carries predicted kind and ≥3 close-op
   confusion pairs are read and the dominant pair named (PRIMARY).** This is the FR's own
   first AC — promote it to a hard gate: `affect_throughline.yaml` is not touched until the
   pair (e.g. `close guilt` mis-emitted as `close relief`-shaped) is named from the read,
   not guessed. A resolution-signature cue authored against an unread confusion is a fix
   for a hypothesised bug.

2. **Recompute (c) KIND-WRONG on the POST-FR-600 residual (PRIMARY).** The "5 KIND-WRONG,
   4 close" count is measured on the *pre*-re-annotation miss set. FR-600 moves and drops
   GT deltas, so it changes the miss set — the close-heavy signal must be re-confirmed
   against the re-partitioned residual before sharpening the close path, or you may sharpen
   a confusion that re-annotation already dissolved. (This is why the FR is correctly
   ordered after FR-600.)

3. **Keep the open-op path byte-identical and guard precision (endorsed).** FR-599 showed
   op-path coupling destabilises calibration; the diff must prove the open branch is
   untouched. And (c) must fall without an offsetting rise in (a) ABSENT or an
   `affect_precision` regression — the model must not over-emit closes to chase recall.

**Endorsed:** frozen `main_l7` untouched, REQ-YG-020 reuse, no new CAP, the taxonomy-
collapse and cross-beat-context alternatives correctly deferred (the latter would revive
the FR-598 invention engine).

**Frozen scope:** extend the probe (read-only) to carry the nearest predicted delta's kind
for (c) members; read ≥3 close-op pairs on the post-FR-600 residual and name the dominant
confusion; add per-kind close-op resolution-signature cues to `affect_throughline.yaml`
with the open branch byte-identical; re-run spike + probe showing (c) falls with no (a)
rise and no precision regression. BLOCKED until FR-600 re-partitions the residual.

> **Predecessor update (FR-600 enforced 2026-06-26).** The blocker is cleared. FR-600's
> deterministic (e)=12 re-partition landed **1 HIT / 5 ABSENT / 1 KIND-WRONG / 0 (e)** — one
> re-anchored delta surfaced as a *new* KIND-WRONG, reinforcing this FR's close-op signal but
> NOT recomputing it. The motivating "5 KIND-WRONG, 4 close" figure was measured on the
> *pre*-FR-600 miss set and is now stale: FR-600 only re-partitioned the (e) subset, so the
> (a)/(b)/(c)/(d) buckets across the full re-annotated corpus are un-recounted. Correction #2
> / AC #1 stand as the first task — a full probe re-run on the post-FR-600 GT must re-confirm
> the close-heavy (c) signal (now ~6 candidates: 5 untouched-licensed + 1 from the re-anchor)
> before any `affect_throughline.yaml` cue is authored.

## Problem

`close` ops resolve an earlier feeling (a loss recovered, a guilt confessed, a betrayal
avenged). The FR-598 classifier judges each beat in isolation, so at a resolution beat it
sees the *positive* surface event (a triumph, a reconciliation) and must infer *which*
negative arc it closes. The op-split evidence (KIND-WRONG 4 close / 1 open) says this
inference is where it slips: detection (op+char) is right, kind is wrong. The 0/x
TOWARD-WRONG count rules out a relational-direction confound — it is specifically the kind
axis on closes.

This is distinct from (a) ABSENT (the model emits nothing) and (e) UNLICENSED (the GT is
wrong): here the model *does* fire on the right beat, so the lever is discrimination, not
scale or data.

## Raw Output Read (measurement / metric-tooling FRs only)

`read_raw_output_first` — this FR changes the classifier whose output the frozen gate
scores. The motivating read is the FR-599 dump `results/l7/miss-samples.txt` plus the
per-genre classifier files under `results/l7/throughlines/<genre>/<agent>.yaml`. Before
authority, this section must cite ≥3 KIND-WRONG close-op records showing the *predicted*
kind vs the *GT* kind on the same beat (e.g. model emits `close … relief`-shaped where GT
says `close guilt`), so the fix targets a real confusion pair, not a guessed one.

> NOTE: the FR-599 dump records the GT delta and the licensing verdict but not the
> *predicted* mismatched kind. The first task here is to extend the probe's miss record
> (read-only) to carry the nearest predicted delta's kind for (c) members, then read those
> pairs. No fix is designed until the dominant confusion pair is named from the read.

## Proposed Solution

1. **Read the close-op KIND-WRONG confusion pairs** (predicted kind vs GT kind) from an
   extended FR-599 miss record. Name the dominant pair(s).
2. **Sharpen the close-op kind cues in `affect_throughline.yaml`** — add, per kind, the
   *resolution signature* a close presents (loss→recovery/mourning, guilt→confession/
   atonement, betrayal→exposure/reckoning, retaliation→vengeance-enacted), so the model
   maps the positive surface event back to the correct negative kind. Keep the open-op path
   byte-identical (FR-599 showed op-path coupling destabilises calibration).
3. **Re-run the spike** (`spike_affect.py`) and the FR-599 probe; KIND-WRONG must fall and
   must not be offset by a rise in ABSENT or precision loss (over-confident closes).

## Acceptance Criteria

- [x] FR-599 miss record extended (read-only) to carry the predicted mismatched kind for
      (c) members; ≥3 close-op confusion pairs read and the dominant pair named.
- [x] `affect_throughline.yaml` close-op kind cues sharpened; the open-op branch is
      unchanged (verified by diff: 16 insertions, 0 deletions).
- [x] Frozen `main_l7` evaluator **not** modified (verified by diff: empty).
- [x] Spike + probe re-run: (c) KIND-WRONG falls 6->3 (close 4->1), with no offsetting rise
      in (a) ABSENT (17->14, FELL) and no `affect_precision` regression (0.064->0.122, ROSE;
      predicted count flat 47->49, so no over-emission).
- [x] No new CAP; REQ-YG-020 reused. Changelog fragment + diary reflection.

## Enforcement Outcome (2026-06-26)

**Phase A — the read (Judge's hard gate, satisfied before any prompt edit).**
The probe was extended (read-only) with `_kindwrong_members` carrying the predicted
mismatched kind and a deterministic `--kindwrong` mode. Recomputed on the post-FR-600
residual (correction #2): (c) KIND-WRONG = **6**, of which **4 are close** — the
close-heavy signal SURVIVES re-annotation (it was 5/4 pre-FR-600; FR-600 added one new
(c) member). The four close confusions, read from the beats:

| close confusion | beat | the surface the model misread |
|---|---|---|
| betrayal -> retaliation | detective F6 | an avenging ACT (names/exposes Hagen) read as a fresh open |
| guilt -> betrayal | historical F10 | relational recognition (earns her seat) read as other-blame |
| loss -> hope | quest F6 | a triumph that recovers the loss read as forward hope |
| hope -> loss | historical F9 | a solemn vindication ceremony read as loss |

**Dominant mechanism (named, not guessed):** on a close, the model names the kind from
the resolving beat's SURFACE (its action or valence), not from the antecedent feeling
being RESOLVED. No single pair repeats (all n=1); the lever is a per-kind
resolution-signature cue, not a single-pair patch. The full read is committed at
`examples/plot_modeller/fixtures/affect-licensing/fr601-kindwrong-confusions.md`.

**DEVIATION (endorsed precedent from FR-600).** The full probe's `_LICENSING_FIXTURES`
are pinned to the PRE-FR-600 miss set, so a verbatim live re-run would fail its own pin
and re-introduce non-determinism. (c) is deterministic, so the recount uses the
`--kindwrong` path (no LLM, no pin) — same substitution the Judge accepted for FR-600.

**Phase B — the fix.** Added a close-op resolution-signature block to
`affect_throughline.yaml` (16 insertions, 0 deletions; open-op path byte-identical, verified
by diff). The block also carries `hope`'s signature (vindication), which the FR's first draft
omitted but the F9 read required. Re-ran the spike (live haiku, temp 0.7) and recounted
deterministically:

| metric | BEFORE | AFTER |
|---|---|---|
| affect_recall | 0.107 (3/28) | 0.214 (6/28) |
| affect_precision | 0.064 (3/47) | 0.122 (6/49) |
| (a) ABSENT | 17 | 14 |
| (c) KIND-WRONG | 6 | 3 |
| (c) close-op | 4 | 1 |
| total misses | 25 | 22 |

All four original close confusions became HITS; (c) fell with (a) FALLING (not rising) and
precision RISING with a flat predicted count (no over-emission). Frozen `main_l7` untouched
(diff empty). **Caveat:** one stochastic sample at temp 0.7 — the signal is large enough that
noise is unlikely to flip the sign, but a single draw is not a distribution.

## Alternatives Considered

- **Buy a bigger model (FR-578 scale).** Refuted by the op-split: the model already detects
  the right beat/op/char on these misses — scale is the expensive lever for a naming gap a
  prompt cue can close.
- **Add cross-beat context so the close "sees" its open.** Tempting but violates the
  FR-598 per-beat grounding rule and risks reviving the invention engine; revisit only if a
  resolution-signature cue proves insufficient.
- **Collapse the six kinds (e.g. merge rarely-distinguished pairs).** A taxonomy change
  with corpus-wide blast radius; deferred unless the confusion pairs show two kinds are
  genuinely non-separable at beat granularity.

## Related

- FR-599 probe + dumps: `examples/plot_modeller/probe_l7_misses.py`,
  `results/l7/miss-samples.txt`, `results/l7/throughlines/`
- Classifier prompt: `examples/plot_modeller/prompts/affect_throughline.yaml`
- Sibling: FR-600 (GT re-annotation — run first), FR-602 (gate tolerance)
