# Feature Request: Demote world_recall, Gate L5 on Regenerability Discrimination

**Priority:** MEDIUM
**Type:** Fix (evaluation metric correction)
**Status:** Enforced (2026-06-25) — Authority granted by author instruction,
evidenced by the FR-594 Power Analysis
**Effort:** ~0.5 day
**Requested:** 2026-06-25
**Predecessor:** FR-594 (built and powered the regenerability ruler)

## Summary

FR-594 proved `world_recall` scores agreement with a *lossy GT skeleton*, not
story capture, and built a GT-free regenerability ruler (simulability + fidelity).
Its Power Analysis (5 repeated corpus runs) then established **which axis is
gateable**. This FR acts on that evidence: it **demotes `world_recall` from the L5
gate to an informational diagnostic** in `evaluate.py::summarise_l5`, and **stamps
a powered verdict** onto the measure summary — the *paired GT-anchored
simulability discrimination* (ours must be robustly more regenerable than the GT
skeleton).

## Value Statement

The L5 layer currently reads **KILL** (world_recall 0.49 < 0.50) on a metric
FR-594 falsified. That KILL is a measurement artifact. This FR replaces the false
gate with the one the power analysis showed is robust, so the L5 verdict reflects
encoding quality instead of agreement with a lossy target.

## Evidence (FR-594 Power Analysis, n=5)

- **Gateable:** paired discrimination `gt_sim − ours_sim` = **0.337 ± 0.035**,
  t(4)=**21.6**, p≪0.01. Every run scores ours more regenerable than GT.
- **NOT gateable:** absolute single-run simulability (corpus-mean sd 0.085 → needs
  n≈6 for MDE 0.10); per-genre verdicts (worst-cell sd 0.22); fidelity as a
  discriminator (ours 0.335 ≈ gt 0.358).

## Design

1. **`nodes/tools.py` — new pure `measure_l5_verdict(ours_sim_mean, gt_sim_mean)`**
   - `gap = gt_sim_mean − ours_sim_mean`
   - `GO` if `gap >= 0.15`; `REVISE` if `gap >= 0.05`; else `KILL`.
   - Thresholds grounded in the power analysis: per-run gap sd ≈ 0.035, so a 0.15
     floor sits ~4 sd below the observed mean gap — robustly positive at n=1
     corpus run. Returns `{verdict, gap, ours_sim_mean, gt_sim_mean, basis,
     power}` — never a per-genre or absolute-threshold call.
   - Pure, deterministic, `@pytest.mark.req("REQ-YG-020")`.

2. **`run.py::_write_measure_summary`** stamps `verdict: measure_l5_verdict(...)`
   onto `l5-measure-summary.yaml` (corpus mean only).

3. **`evaluate.py::summarise_l5`** demotes `world_recall`:
   - `verdict` → `"informational"` (world_recall no longer emits GO/REVISE/KILL).
   - `world_recall` retained as a labelled diagnostic, not the gate.
   - `conditions`/`note` redirect the L5 gate to the regenerability discrimination
     in `l5-measure-summary.yaml` (FR-594/595).

## Acceptance Criteria

- [x] `measure_l5_verdict` is a pure `REQ-YG-020` tool with unit tests: GO on the
      observed 0.34 gap, REVISE on a marginal 0.08 gap, KILL on a collapsed 0.02
      gap, and symmetric/edge handling (zero, negative gap → KILL). *(5 tests,
      16/16 green in `tests/unit/test_l5_measure_tools.py`.)*
- [x] `l5-measure-summary.yaml` carries a `verdict` block (GO on the live corpus).
      *(verdict GO, gap 0.294, ours 0.441 vs gt 0.735 — the false KILL is flipped.)*
- [x] `summarise_l5` emits `verdict: "informational"`; `world_recall` is labelled a
      diagnostic; `l5-summary.yaml` regenerated (deterministic, no LLM) reflects it.
      *(3 guard tests in `tests/test_evaluate.py`; regenerated via `main_l5`.)*
- [x] No per-genre or absolute-threshold gate is introduced (power-analysis bound).
- [x] Diary reflection + changelog fragment.

## Result (2026-06-25)

The L5 verdict flips from **KILL** (world_recall 0.49 — a measurement artifact) to
**GO** (regenerability gap 0.294, ~2× the 0.15 floor). world_recall is retained at
0.49 as a diagnostic. The L5 KILL that blocked Phase 4 merge was a ruler error, not
an encoding error; only L7 (affect recall 0.09) remains a true KILL.

## Alternatives Considered

- **Gate on absolute ours simulability ≤ 0.30.** Rejected: power analysis shows
  the absolute corpus mean swings 0.238–0.441 (sd 0.085); a single-run absolute
  gate would flip verdicts. The GT-anchored *paired* gap is the stable signal.
- **Couple `summarise_l5` to the measure graph (read l5-measure inside evaluate).**
  Rejected this cycle: keeps two concerns separate — `evaluate.py` demotes the
  false metric; the runner stamps the powered verdict where the means are computed.
- **Promote fidelity into the gate.** Rejected: fidelity does not discriminate
  ours from gt (0.335 ≈ 0.358) — it stays advisory.

## Related

- FR-594 — built and powered the regenerability ruler; this FR swings it.
- `examples/plot_modeller/evaluate.py::summarise_l5` — the metric being corrected.
- `examples/plot_modeller/run.py::_write_measure_summary` — where the verdict lands.
