# The flood that only changed its name

**Date:** 2026-06-24
**FR:** FR-585 (L5 salience-gate decode) — Gate 1 KILL
**Predecessor reflections:** [the flood and the miss are one gesture](diary-2026-06-24-the-flood-and-the-miss-are-one-gesture.md), [the lever that taught to the test](diary-2026-06-24-the-lever-that-taught-to-the-test.md)

## What happened

FR-584 proved the L5 precision wound (0.30) is not fixable by prompt wording: a
salience-suppression rule cut the `at` flood but raised misses in lockstep. The
diagnosis was structural — one LLM call carrying ~12 cognitive jobs, the
discrimination task starving among the bookkeeping. FR-585's hypothesis followed
cleanly: give salience its **own** call with nothing else to do, and the flood
should resolve.

I built the gate exactly as judged. Node A, one question per beat — which facts
do you *require*, which do you *change* — emitted as bare `subject | relation |
object` triples. A deliberately dumb keyword adapter typed them for scoring (J:C1,
no LLM in the adapter). I ran it on haiku, measured, and wrote a KILL: recall
collapsed 0.60 → 0.27, and a **new** flood appeared — `rel`-FPs went 15 → 88. I
called it "the flood changed its name" and declared the hypothesis falsified.

Then the user, who had not run anything, said: *the prompt is complicated to a
human.* I had never read the model's raw output. I went and read it.

## The trap

I had condemned decomposition on a measurement from **an instrument I built
wrong**. Reading the raw triples and dumping the 88 `rel` values showed they were
**action verbs** ("announces", "pursuing", "departed") and **belief facts**
("aware of", "knows") — and the cause was three defects in *my own spike prompt*:
the vocabulary was never closed, the DIRECTION example literally demonstrated an
action verb as a relation (`The Swarm | assimilates | ARIA` — I taught the flood),
and it anchored "most beats have 0–2 facts" when the ground truth is *most beats
change nothing*. A KILL on a confounded prompt is not a falsification; it is a bug
report about the test.

So I spent the stop-rule's single permitted iteration *deconfounding the
instrument*, not iterating the idea: closed the vocabulary to the five predicates,
deleted the action-verb example, re-anchored on "empty lists are expected." The
result was decisive in both directions. The `rel`-flood went **88 → 0** and recall
recovered **0.27 → 0.54** — the talk/decide/announce beats that had spewed spurious
triples now correctly came back **empty**, matching the GT. The deconfounding
worked. *And precision stayed flat at 0.32 ≈ 0.30.* The over-emission didn't
dissolve; once I forbade verbs and beliefs it **funneled into `at`** (56 → 86 FPs),
the model now tracing every leg of every caravan journey as location-pairs while
the GT scores only the salient arrivals. The flood changed its name twice: `rel`
(my bug), then back to `at` (the real wound).

## The insight

Two insights, one from each pass.

**Decomposition relocates a flood; it does not manufacture a discrimination.**
Three prompt architectures now land on the same precision — FR-584 monolith
(0.30), open-vocab decode (confounded), closed-vocab decode (0.32). The model
genuinely does not possess the discrimination the wound requires at this tier;
giving it a cleaner desk just moves the same wrong call to the next-widest slot.
The deconfounded pass even *unlocked* one discrimination — empty lists on
talk-beats — yet the residual flood simply concentrated in `at`. *The flood and
the miss are one gesture* is not a property of the prompt; it is a property of the
model's competence.

**A measurement-based KILL is only as honest as the instrument that produced it.**
My first KILL was confounded by defects in the very prompt I was testing — and I
would have shipped it had the user not flagged that the prompt was hard to read.
The number (precision 0.14) was real; the *meaning* I assigned it was wrong,
because I never looked at what the model actually emitted. Reading five raw beats
told me more than the aggregate did across five fixtures.

**And then I made the same error one level up.** Having deconfounded the prompt, I
concluded "haiku model ceiling — escalate to a bigger model." The user caught this
too: *the task split is too complicated; it summarizes the story to world-level and
encodes the result in a single operation.* Every architecture I measured — monolith,
open-vocab decode, closed-vocab decode — shares one unexamined fusion: each asks the
model, in one pass, to **comprehend** (prose → implied persistent state) *and*
**encode** (typed predicate, slice, args, salient delta). FR-585 only split *typing*
off *selection* — both on the encoding side. The comprehension↔representation seam
was never cut. So "model ceiling" is a ceiling for *single-operation encoding*, not
for the task. I had inferred a verdict from three architectures that all share one
flaw — the exact shape of the Pass-1 confound, repeated against a wider canvas.

The `at`-waypoint flood names the real fix: it is a *delta-salience* failure. "What
does this beat *change*" forces the model to hold prior state, current state, and
salience at once. The untested seam is **snapshot, don't delta** — let the model
*comprehend* (emit a plain world-state snapshot after each beat, its easiest mode)
and let *code* diff snapshots and collapse waypoint runs. Snapshots bundle one hard
judgment; salient deltas bundle three.

## The cure (carried forward)

- **Read the model's raw output before declaring a measurement-based KILL.** An
  aggregate metric from an instrument you built can be confounded by the
  instrument. Five raw beats deconfounded a verdict that five fixtures of
  aggregates had hidden. The cheapest validation of a kill is one `print(raw)`.
- **When the prompt is hard for a human to read, suspect the measurement, not just
  the model.** The user's "this is complicated" was a confound detector. A prompt
  whose own examples teach the failure (an action verb shown as a valid relation)
  produces a failure that looks like the model's but is yours.
- **Spend the one permitted iteration deconfounding the instrument, not iterating
  the idea.** The stop rule said "don't iterate Node A wording more than once." The
  honest use of that single shot was to fix my prompt's defects and re-measure —
  which turned a confounded 0.14 into an honest 0.32, same verdict, real reason.
- When a precision flood shrinks but total precision doesn't improve, **dump the
  other predicates before celebrating.** A flood that relocates is not a flood that
  resolved; it changed its name.
- **Spike-gating paid for itself twice.** The first pass would have wrongly killed
  on a confounded number; the gate's cheapness let me re-run deconfounded for the
  cost of one prompt edit. A gate cheap enough to re-run is a gate that survives
  its own bugs.
- **Before concluding "model ceiling," check that your architectures don't share
  one unexamined fusion.** I called a haiku ceiling from three prompts that all
  fused *comprehension* (prose → world-state) with *encoding* (typed predicate).
  That is not three independent tests; it is one design tested three ways. The
  natural seam for any "understand X then formalize X" task is
  comprehension↔representation — and asking for **snapshots** (current state) is
  strictly easier for the model than asking for **salient deltas** (current +
  prior + salience), which code can compute instead.

## Seed

The untested seam is **comprehend, then represent**: ask the model for a plain
world-state *snapshot* after each beat (no vocabulary, no slices — just "what is
now physically true"), then let code diff consecutive snapshots into typed deltas
and collapse intra-chapter `at`-runs to net displacement. Does separating the two
loads break the 0.30 ceiling without a bigger model? If it does, the ceiling was
never the model — it was the single operation. If it doesn't, *then* scaling is the
honest lever, tested cleanly for the first time. And the wider seed: should every
measurement-based KILL in this repo carry two mandatory checkboxes — "raw output
inspected: yes/no" and "do my compared variants share an unexamined fusion:
yes/no" — the way every fix carries a condemning test?
