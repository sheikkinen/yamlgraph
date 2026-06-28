# The wound that only changed its address

**Date:** 2026-06-25
**FR:** FR-587 (L5 snapshot-then-diff) — Gate 1 KILL
**Predecessor reflection:** [the flood that only changed its name](diary-2026-06-24-the-flood-that-only-changed-its-name.md)

## What happened

FR-585 deconfounded the L5 wound to a single mechanism: the model, asked per beat
"what *changed*?", floods `at` — tracing every leg of every journey as location
pairs while the ground truth scores only salient relocations (86 FPs, 88% of all
FPs). Its reflection named the next lever precisely: stop asking for the *delta*.
Ask the model only to **comprehend** — emit a per-beat world-state *snapshot* — and
let deterministic code compute the *change* by diffing snapshots. Move salience out
of the LLM and into a function that never floods.

I built it exactly as judged and Gate-1-first. A snapshot prompt (full current
state, opening `F0` baseline, no delta language). A pure `diff_snapshots` helper:
appearance/disappearance/value-flip, then two salience collapses — intra-chapter
`at`-run → terminus, and first-departure-only. Before reading any aggregate
(correction #2), I enumerated every `at … value: false` departure in the five GT
fixtures and found the rule the ground truth actually follows: **departure is
scored only for an entity's first move from its established origin; every later
relocation is arrival-only.** I built the helper to reproduce exactly that, then
ran haiku.

`at`-FP: 86 → 69. Recall: 0.32. The dominant FP class: still `at`, still 85%.

## The trap

The seam was real and I cut it cleanly — comprehension and encoding genuinely
separated, salience genuinely in code. I half-expected the flood to dissolve
because the *structure* was finally right. It didn't. The temptation here is the
mirror image of FR-585's: there I almost KILLed a good idea on a broken instrument;
here I could have over-credited a clean structure on a stubborn number. 86 → 69
*is* a fall, and a softer reading ("material, trending down, give it the typed
node") was available. The decision rule (correction #1) is what held the line:
`at`-FP must fall *with recall holding ≥ 0.50*. Recall was 0.32. The conjunction
failed, the FP class never shifted, and two runs agreed. Material-but-insufficient
is still a KILL when the recall floor is breached.

## The insight

**Moving the wound to a cleaner pass relocates it; it does not heal it.** The
snapshot didn't ask the model to judge salience — but it still asked the model
where everyone *is*, every beat, and the model still answers with every location a
beat mentions, transient waypoints included, drifting the place-phrasing as it goes
("the guild warehouse district" one beat, "warehouse" the next). The diff faithfully
turns each of those into an arrival. Deterministic collapse can only merge
*consecutive same-chapter* runs and suppress *repeat* departures — it cannot recover
a salience the model never encoded consistently in the first place. The flood is a
property of single-tier comprehension at this model size, not of the delta framing
specifically. FR-585's lesson generalizes one tier up: *decomposition relocates a
flood; it does not manufacture a discrimination* — and now, *neither does moving the
flood from the encoding pass to the comprehension pass.* Four framings —
prompt-wording (FR-581/582), prompt-architecture (FR-584), select→type (FR-585),
comprehend→represent (FR-587) — have failed the same way. Single-tier framing is
exhausted. The honest next lever is the one the stop rule reserved: scale (FR-578),
with the snapshot prompt as the larger model's input, the seam already cut so a GO
reveals *why* and a NO-GO is clean.

## What I'd do differently

Nothing in the build — Gate-1-first, one wording iteration (spent on a `rel`-line
YAML crash, not on the metric), GT validated before the aggregate, the recall floor
enforced as a hard conjunct. The discipline is what made the KILL *trustworthy*
rather than a vibe. The thing to carry forward is suspicion of my own structural
satisfaction: a correctly-cut seam is necessary, not sufficient, and the number
that refuses to move is data, not an obstacle to argue around.

## Seed

Every L5 lever has tested *whether the model can encode salience* and found no. None
has tested *whether the corpus's salience is learnable at all from a single beat's
text* — i.e., is the GT's "first-departure-only, arrival-mostly" rule recoverable
without the whole-plot view a human author had when authoring it? If FR-578's bigger
model also floods `at`, the wound may not be the model but the **task framing**:
single-beat salience may be underdetermined, and the real fix a two-beat (or
chapter-windowed) context the model can diff *itself*. Before scaling further: would
a deterministic `at`-FP ceiling — the best any snapshot+collapse could score against
this GT, computed from the GT itself — tell us whether 30 is even reachable, or
whether the target was never adapter-achievable?
