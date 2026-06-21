# floodmark_up — FR-559 M0 plot-model spike

A standalone falsification spike (NOT wired into DM v2). It proves an off-the-shelf classical
planner can author the typed floodmark `PlotPlan`, compile belief-as-fluent, and prove the
early-reveal variant **unsolvable** — before any v2 surface area is committed.

See [`feature-requests/FR-559-dm-v3-m0-floodmark-plot-model-spike.md`](../../../../feature-requests/FR-559-dm-v3-m0-floodmark-plot-model-spike.md)
and [`docs/design-v3-plot-model-implementation.md`](../../docs/design-v3-plot-model-implementation.md) §4.

## What it proves

| Plan | Outcome | Owner |
|---|---|---|
| `floodmark` (presumed-dead arc) | **solvable** — world `alive`, clan believes dead | `unified-planning` |
| `early_reveal_variant` (Arnulf onstage Ch3) | **proven unsolvable** — belief established only at Ch6 | `unified-planning` |
| `world_revival_variant` (revival as world-truth) | one `lifecycle_violation` | hand-written check |

## Layout

```
floodmark_up/
  schema.py      # throwaway Pydantic subset of design §2 (NOT the production contract — J4)
  up_model.py    # build_problem(plan) -> up.Problem; belief reified; mandatory done_<id> steps (J2); chapter chain (J3)
  validate.py    # solve_status (typed three-way outcome, J1) + _check_monotonic_lifecycle
  floodmark.py   # the floodmark literal + early_reveal + world_revival variants
  run.py         # prints the solved chapter order (the realizer's input skeleton)
```

## Engine of record (J3)

**`fast-downward` with `astar(blind())`** — a *complete* search. This config is pinned in
`validate.py` (`_ENGINE_NAME` / `_ENGINE_PARAMS`).

**J1 engine-reality note.** No pip-installable UP engine on the target machine emits
`UNSOLVABLE_PROVEN`:

- Fast Downward proves unsolvability (`Completely explored state space -- no solution!`) yet exits
  **12**, which the UP wrapper maps to `UNSOLVABLE_INCOMPLETELY` (never exit 10/11 → `PROVEN`);
- `symk` (symbolic, complete) behaves identically;
- `aries` (the design's preferred temporal engine) **hangs** on untimed classical problems.

So for a complete search on a **finite** problem, `UNSOLVABLE_INCOMPLETELY` *is* the proof.
`validate.PROVEN_UNSOLVABLE` accepts both proven enums, while `validate.GAVE_UP`
(`TIMEOUT`/`MEMOUT`/`INTERNAL_ERROR`) is a distinct set that **fails** the test, and a missing
engine **skips** via `NoEngineAvailable`. This preserves the proof-vs-give-up distinction; it only
corrects the enum the engines actually use. (FR-559 J1 amendment, approved 2026-06-21.)

## Optional dependency

`unified-planning` is **not** a YAMLGraph runtime dependency — it is an opt-in spike install. The
test (`examples/dungeon_master/tests/test_floodmark_spike.py`) skips gracefully when it is absent,
so the default `pytest tests/unit/` run and the CI dependency audit are unaffected.

```bash
pip install "unified-planning[fast-downward]"
```

## Run

```bash
# the proof (3 assertions)
PYTHONPATH="$PWD" python -m pytest examples/dungeon_master/tests/test_floodmark_spike.py -q

# the chapter-order skeleton
PYTHONPATH="$PWD" python -m examples.dungeon_master.spikes.floodmark_up.run
```

Expected `run.py` output:

```
status: SOLVED_SATISFICING
solved chapter order (the realizer's input skeleton):
  ch 1  F1         villainy
  ch 6  Fr         reveal
  ch 6  Ff         reconciliation
```
