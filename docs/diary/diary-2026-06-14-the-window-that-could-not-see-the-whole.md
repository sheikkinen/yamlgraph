# The Window That Could Not See the Whole

*2026-06-14 — FR-484, DM v2 post-play Final Cut*

## The trap: a fix that only moves the horizon

The DM play loop wrote turns online, each seeing the last three recaps. The
symptom was repetition — Lana's ledge re-established five turns running. The
*obvious* fix is to widen the window: show six recaps, show ten. But widening the
window only moves the horizon; it never gives the writer the whole arc, and it
does nothing at all for the second, deeper defect — shallowness. A forward-only
writer at turn _n_ cannot know which later turn is the climax, so it cannot
allocate emphasis. No per-turn change can fix that, because the information
required (which beat is pivotal) does not exist until the arc is complete.

Naming the two defects apart was the whole leverage. **Repetition is a windowing
artifact; shallowness is a global-emphasis problem.** Only the second one forces
the architecture: it is *structurally* unsolvable per-turn, and that is what earns
a post-play pass that sees the finished whole. Had I conflated them, I'd have
shipped a window-widening prompt tweak and declared victory on the half that was
cheap, leaving the half that mattered untouched.

## The cure that recurred: code knows the fact, the model writes the prose

This is the third FR in a row (480 → 482 → 484) where the same seam reappeared:
the model must be handed the *fact*, and asked only for the *judgement*. Here the
fact is **which turn is the climax** — and code already knows it, because FR-481
made `phase` monotonic precisely so the first `climax` turn is trustworthy. So
`climax_turn` derives it deterministically (with a `scene_complete` fallback, and
a last-turn last resort), and the prompt is told "Turn 5 is THE CLIMAX." The model
never recomputes the arc's structure; it only weights the prose. The deterministic
seam (`final_cut_context`) is a pure function with a unit test; the generative
seam (the weave) has no clean test and is witnessed by a live run.

That live-run witness is itself a graduation. FR-483 *seeded* the idea: for the
irreducibly-generative half, cite one real run rather than inventing a brittle
metric gate. FR-484 *practised* it — I composed the cited run `6eae1ce5` against
vertex and read the output as the proof: ledge established once then threaded,
climax given dialogue and the mud at the chin. An n-gram repetition gate would
have ossified a fragile heuristic into CI; one cited run proves the prose is good
without pretending a number can. If this recurs a third time, it graduates to
Scripture.

## The boundary I nearly crossed

The turns are dynamic; the `Stage.context` mechanism only threads the accepted
text of *named static stages*. The lazy move is to bolt the turns onto `context`
somehow. The judged constraint held me to the honest seam: `final_cut` gets its
own invoke branch (like the turn stages already have), reading the turns through
`turn_ops`, not through a mechanism that was never built for them. The leaf is
additive by construction — a new `doc["final_cut"]` artifact — and a mandatory
byte-for-byte test proves the played turns are untouched after compose+accept. The
play-by-play stays the immutable record; the Final Cut is the polished narration
on top.

**Seed:** The climax marker is derived from one signal (`phase`). The arc carries
others — `beats_satisfied` density, recap length, the turn where `scene_complete`
fires. Could a *dramatic-shape* vector (rising tension, the beat-completion curve)
be computed deterministically from the recorded direction data and handed to the
Final Cut, so the model is told not just *where* the climax is but *what shape*
the whole arc has — and would that structure help or merely over-constrain the
prose?
