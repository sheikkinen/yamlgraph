# Diary — The ruler that disagreed with itself between runs

**2026-06-25 · FR-594 enforcement**

## What happened

I enforced FR-594, which graduated a throwaway probe
(`spike_regenerate_prose.py`) into a real five-node graph (`l5_measure.yaml`):
render the L5 beats → regenerate the chapter from *only* the world-state machine
→ count `[UNDERDETERMINED]` markers (simulability, deterministic) → judge the
regen against the synopsis (fidelity, LLM) → combine into a two-axis verdict that
never averages the axes. Three pure tools, eleven unit tests, one judge prompt,
one `--mode measure-l5` runner. The Judge had GRANTED authority but framed the
whole thing sharply: *"build the ruler, NOT to swing it."* Diagnostic only;
`world_recall` stays primary; nothing gates.

The acceptance run did its job. Corpus simulability reproduced the probe's
discrimination — ours 0.313 ≪ gt 0.697 — confirming the original finding that the
ground-truth L5 predicate channel cannot regenerate its own stories (it leans on
glosses the world machine doesn't carry), while our encoder's richer transitions
can. And the single most important acceptance criterion held: on scifi the
fidelity judge returned a **non-empty `inverted` (5)**, witnessing that the
encoder's confident climax-drift (rollback → ARIA winning) is caught as a
*meaning reversal*, not hidden behind a fluent-but-wrong high score. The W026
fusion warning — that a four-field judge prompt might starve the `inverted`
bucket — was empirically refuted.

## The cognitive trap

**`single_run_is_a_measurement`.** Before the full corpus run I did a one-genre
scifi smoke test and got simulability **1.00 (13/13)** for ours. That flatly
contradicted the probe's 0.15 (2/13) on *identical input data*. My first instinct
was wiring-bug panic: surely the beats aren't reaching the regenerator. They
were — I rendered them outside the graph and confirmed 2893 chars of rich
predicate stream. The 1.00 was real model behavior: at temp 0.7 the regenerator's
*propensity to emit `[UNDERDETERMINED]` markers* is itself a noisy LLM variable.
The corpus run then gave 0.77 for the same scifi-ours. Same data, three different
numbers across runs (0.15 / 1.00 / 0.77).

The deterministic counter is faithful — it counts exactly the markers present.
The noise lives one layer up, in the LLM that decides how many markers to write.
I almost "fixed" a non-bug because I treated a single temp-0.7 sample as if it
were the measurement. The measurement is the *distribution*, and a sample of one
has no error bar.

## What made the enforcement honest

The Judge's correction #4 — *declare a minimum-detectable-effect and required n
before this gates anything* — stopped being abstract the moment scifi-ours swung
1.00 → 0.77. I didn't have to argue the ruler was underpowered; the ruler
demonstrated it on me, in one session, with identical inputs. So the FR ships it
diagnostic-only with the variance recorded as a finding, not smoothed away. The
two axes stayed orthogonal and attributable: historical-gt fired
`low_simulability` alone (fidelity clean) while historical-ours fired
`fidelity_inverted` alone (simulable but drifted) — the same corpus row proving
the two axes measure genuinely different failures and must never collapse to one
scalar.

## Heuristic

When an LLM sits *inside* a deterministic measurement, the determinism is a
costume. Count the LLM calls between the input and the number: each one is a
variance source the final digit hides. A measurement whose value swings across
runs on identical input is reporting the noise of its noisiest stage, not the
property you named it after. Sample the distribution before you trust the point.

## Seed

The simulability counter is deterministic but its *input* (the regen prose) is
not — so the cheap GT-free axis inherits the expensive axis's variance. Could the
regenerator be pinned (temp 0, or N-sample-and-median the marker count) to make
simulability a stable enough signal to gate *on its own*, leaving the noisy
fidelity judge as advisory? What is the required n at temp 0.7 for the ours-vs-gt
gap (0.31 vs 0.70) to clear a 95% interval — and is that n cheaper than just
pinning the temperature?
