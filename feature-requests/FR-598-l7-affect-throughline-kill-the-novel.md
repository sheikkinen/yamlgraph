# Feature Request: FR-598 L7 Affect Throughline — Kill the Novel (per-beat classification)

**Priority:** HIGH
**Type:** Bug (prompting defect — wrong output format at the L7 encoder's first stage)
**Status:** Enforced — hypothesis REFUTED, gate NOT cleared, stop rule fires (2026-06-26)
**Effort:** ~0.5 day (prompt rewrite + spike re-run against the frozen gate; no graph topology change)
**Requested:** 2026-06-26
**REQ:** REQ-YG-020 (reuse — no new CAP)
**Predecessor:** FR-596 (per-agent throughline) — built `affect_throughline.yaml` + `encode_affect.yaml`
**Sibling:** FR-597 (regenerability ruler — REFUTED the under-determination hypothesis; `affect_recall` stands)
**Gate:** frozen FR-578 `affect_recall ≥ 0.50` (deterministic; `main_l7` in `evaluate.py` untouched)
**Cited trace:** `019f01ef-dfe3-7412-8180-b6410cab26a3` (throughline, 658 prose tokens) /
`019f01ef-da3b-70b2-8407-e59675df72a9` (encode, faithful compression) — archived verbatim in
[`FR-598-evidence/langsmith-trace-throughline-vs-encode.md`](FR-598-evidence/langsmith-trace-throughline-vs-encode.md)

## Summary

The L7 affect encoder's first stage, `affect_throughline.yaml`, asks haiku for **prose
narration of one character's emotional arc**. The model obliges with a 300–450-word
**literary character study**, and the novelist's instincts that prose rewards —
completing the arc, supplying interiority, reaching for evocative diction, threading
causality across beats — are exactly what corrupt the affect labels. Replace the
free-prose stage with a terse, per-beat **classification** that emits one line per
affect-bearing beat and defaults to *none*. Measured against the standing
`affect_recall ≥ 0.50` gate.

## Value Statement

L7 affect_recall has sat at 0.09 (monolith) / 0.15 (per-agent throughline) across every
model scale tried, blocking FR-579 (merge node). This FR removes the actual cause — a
format mismatch, not a model-capability ceiling — so the gate can move without spending
effort on bigger models or harness changes that the trace proves are irrelevant.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED.** This is the sharpest diagnosis in the L7 arc, and the
evidence holds: the cited traces are archived in `FR-598-evidence/`; FR-597 is
**Enforced — Branch (b) REFUTED**, so `affect_recall` legitimately stands as the gate
(the exit condition my FR-597 Judgement required fired cleanly on the deterministic
channel); and reading `affect_throughline.yaml` confirms it is free-prose narration
("write plain prose … prose only") carrying the exact invention engine the FR names —
**"Every arc that OPENS should later CLOSE."** The root-cause story is sound: the kind
errors are born in the narration, not the faithful encode pass, so this is
PROSE-MISKINDED, and the fix is a format change, not a model-scale or harness change.

**Red Hat — the real prize is the diary, and it lightly indicts the rulers.** The
lesson "I measured the output for days before I read it" is the most valuable artifact
here: two FRs of metric tooling (594, 597) deferred a defect that one read of the raw
prose exposed. That said, FR-597 was not wasted — its refutation closed the "is the
gate even valid?" question that would otherwise haunt every L7 number. The sequencing
heuristic (read raw output *before* building metric tooling) is worth graduating from
the diary seed, not just recording.

**Corrections required before enforce (do not widen scope):**

1. **Name the operative levers precisely — do NOT credit constraints that already exist
   and already fail (PRIMARY).** The current prose prompt *already* says "Skip beats
   where this character feels nothing / Do NOT force a feeling onto every beat" and
   *already* instructs relational direction for guilt/betrayal — and it floods anyway.
   So "default none" and "relational direction" are **not** the fix; restating them is
   cargo-cult. The two load-bearing changes are: **(a)** output **format** = terse
   structured per-beat classification (kills the prose genre), and **(b)** **delete
   the "every arc that opens should close" cross-beat completion mandate** — that
   instruction is the invention engine (it is what authored The Swarm a four-kind
   arc). Per the subject-axis discipline: this removes an abstraction level
   (cross-beat arc-planning), it does not reword within it. State that (a)+(b) are the
   cure and the other listed constraints are carried only as guards, not as the
   mechanism.

2. **Resolve "Likely collapse the two-pass into one" — decide it now.** A topology
   choice cannot ride as "likely" in a Bug FR. FR-596 was frozen spike-only (no
   production graph was wired), and `encode_affect` only transcribes faithfully, so
   collapsing to a **single** per-beat classification node is clean and removes the
   vestigial pass — pick it, and update `spike_affect.py` coherently. If instead the
   two nodes are kept, `encode_affect` becomes a pure validator/pass-through and must
   be stated as such. No "likely."

3. **The grounding/citation constraint is an UNVALIDATED self-report — measure it, do
   not assume it.** "Quote the exact source phrase" is a prompt lever, not a
   mechanical guard (nothing checks the citation actually licenses the affect — the
   flood surface from the prompt-contract discipline). Its efficacy must be **read
   from the spike output** (does invention actually drop? the The-Swarm-non-character
   check is the named known-positive), not credited in advance.

4. **GO must be attributable to kind-given-detection, with detection held.** Detection
   is already 0.52; the thesis is that killing the prose lifts *kind*. The spike must
   report kind-given-detection rising **and** detection **not** dropping below ~0.52
   (the format change must not lose the arcs it currently lands) **and** `toward`
   moving off 0/10 — not merely the aggregate recall crossing 0.50. Same attribution
   discipline carried through the whole arc.

5. **Add the stop rule (anti-ritual).** This is the *first* format change, so it is a
   genuine new lever, not wording-iteration-#N — but bound it: **one** format
   iteration. If structured per-beat classification *also* lands kind-given-detection
   flat, the conclusion is a real kind-discrimination/taxonomy ceiling (the model
   cannot tell the six kinds apart per-beat even when grounded), which fires the
   reserved escalation — FR-578 model scale, or revisiting the six-kind taxonomy —
   **not** a second wording pass on the classifier.

**Minor:** the read-≥3-raw-samples-before-scoring AC is the diary's graduated lesson
mechanized — endorse strongly. REQ-YG-020 reuse, frozen `main_l7`, changelog + diary
fragment — all correct.

**Frozen scope:** rewrite `affect_throughline.yaml` into a terse per-beat
classifier (closed verbatim vocab, default none, no cross-beat connective tissue,
**arc-closure mandate deleted**, explicit relational direction), collapse to a single
classification node, update `spike_affect.py`, re-measure against the frozen FR-578
`affect_recall ≥ 0.50` gate reporting the detection/kind/toward sub-axes. No evaluator
change, no model scale, no second wording iteration. The format change is the cure;
the grounding citation is a measured guard, not the mechanism.

## Problem

Reading the raw `affect_throughline` output (the diagnostic deferred behind two FRs of
metric tooling — see diary `2026-06-26-i-measured-the-output-for-days-before-i-read-it`)
showed the defect in one read. The cited trace (agent **The Swarm**, scifi "The Loom")
is the cleanest witness: *The Swarm is not a person* — it is an emergent hive-mind — yet
the prose authors it a full four-kind arc (`loss`, `betrayal toward Jonas`,
`retaliation`, `hidden_blessing`), every one invented to satisfy the narrative's demand
for a complete arc.

The format produces three distinct, measurable corruptions:

1. **Invention** — narrative abhors a vacuum, so the prose fabricates affect to fill the
   arc (`guilt → Pell` for Marren, `retaliation` for Hagen, a whole arc for The Swarm).
   This is the cast-flood and kind-inflation at their source.
2. **Synonym drift** — the six kinds become literary *flavors* chosen for resonance, not
   a closed classifier vocabulary (`hidden_blessing` for GT `hope`).
3. **Beat smearing + relational suppression** — causal connective tissue offsets anchors
   (loss lands on F2 not GT's F1), and the heroic-arc framing suppresses relations that
   break the shape (Marren's own `betrayal → Hagen` is never named).

Beat-level localization (`logs/l7-kind-localization.log`) confirms `encode_affect`
transcribes the prose **faithfully** — including the prose's invented `guilt → Jonas`
and its conflation of ARIA with Mara. The kind errors are **born in the narration**, not
the encode pass. This refutes the FR-596 spike's own `ENCODE-MISKINDED` verdict: it is
**PROSE-MISKINDED**. The detection sub-axis (op+char on the right beat) is already
healthy at 0.52 — the arcs land; only the *kind* is wrong, and the kind is decided by
the prose.

## Proposed Solution

**Topology (decided, per Judgement C2): collapse to a SINGLE per-beat classification
node.** FR-596 was frozen spike-only (no production graph was wired) and `encode_affect`
only transcribes the prose faithfully, so the two-pass is vestigial. Replace
`affect_throughline.yaml` with one classifier node and **retire `encode_affect`** (fold
its typed-op shape into the classifier's output); update `spike_affect.py` coherently.

**The cure is exactly two load-bearing changes (Judgement C1). Everything else is a
guard, not the mechanism:**

1. **(a) Output FORMAT = terse structured per-beat classification.** This removes the
   prose *genre* — the literary register that supplies interiority and synonym drift.
2. **(b) DELETE the "every arc that OPENS should later CLOSE" cross-beat completion
   mandate.** This instruction is the **invention engine** — it is what authored The
   Swarm a four-kind arc. Removing it removes an abstraction level (cross-beat
   arc-planning); it is *not* a rewording within the prose frame.

Output shape — one line per affect-bearing beat, nothing else:

```yaml
# per-agent classification; default is NONE — most beats emit nothing
- id: F4
  op: open
  kind: betrayal        # exactly one of the six; verbatim from the closed set
  toward: Hagen         # required for relational kinds (guilt, betrayal); null otherwise
- id: F6
  op: close
  kind: betrayal
  toward: Hagen
```

**Guards carried (NOT the mechanism — several already exist in the prose prompt and
already fail there; they are retained only to not regress):**

- **Closed vocabulary, named verbatim** — `op ∈ {open, close}`, `kind ∈ {loss, guilt,
  betrayal, retaliation, hidden_blessing, hope}`. No literary synonyms.
- **Default none** — "most beats carry no affect." *(Already in the prose prompt; floods
  anyway — a guard, not the fix.)*
- **No connective tissue** — classify each beat independently; no cross-beat narration.
- **Relational direction** — for `guilt`/`betrayal`, state feeler and target explicitly.
  *(Already instructed in the prose prompt; carried, not credited as the cure.)*
- **Source-phrase grounding** — every emitted affect cites the beat phrase that licenses
  it. **This is an UNVALIDATED self-report (Judgement C3): nothing mechanically checks
  the citation licenses the affect.** Its efficacy must be *read from the spike output*
  (does invention actually drop?), not assumed — the The-Swarm-non-character check is the
  named known-positive.

## Acceptance Criteria

- [ ] `affect_throughline.yaml` replaced by a single per-beat **classification** node
      (no free prose); `encode_affect` retired or reduced to a pure validator; verified
      by reading ≥3 raw samples before any score is read.
- [ ] The arc-closure completion mandate ("every arc that OPENS should later CLOSE") is
      **deleted** from the prompt — confirmed absent.
- [ ] **GO is attributable to kind, not just the aggregate (Judgement C4):**
      `kind | detection` rises **and** `detection` is held ≥ ~0.52 (the format change must
      not lose the arcs it already lands) **and** `toward | relational` moves off 0/10 —
      reported alongside pooled + per-genre `affect_recall` (frozen `main_l7`) ≥ 0.50.
- [ ] Grounding efficacy **measured** from spike output: invention drops (the The Swarm
      whole-arc fabrication for a non-character does not recur) — read, not assumed.
- [ ] Raw samples for ≥3 agents archived to disk and read before the aggregate
      (forced-observation discipline — graduated to Scripture `read_raw_output_first`).
- [ ] **Stop rule (Judgement C5):** exactly ONE format iteration. If structured
      classification *also* lands `kind | detection` flat, the conclusion is a real
      kind-discrimination/taxonomy ceiling → fire the reserved escalation (FR-578 model
      scale, or revisit the six-kind taxonomy) — **not** a second wording pass.
- [ ] Tests updated/added under REQ-YG-020; frozen FR-578 evaluator untouched.
- [ ] Changelog fragment (`changelog/unreleased/`, `req: REQ-YG-020`) + diary reflection.

## Enforcement Outcome (2026-06-26)

The frozen scope was executed in full: `affect_throughline.yaml` was rewritten into a
terse per-beat classifier emitting typed YAML directly, the arc-closure mandate was
**deleted**, `encode_affect.yaml` was **retired** (single node), and `spike_affect.py`
was updated coherently. Measured against the frozen FR-578 gate
(`logs/fr598-classifier-spike.log`):

| axis | prose baseline (FR-596) | classifier (FR-598) | direction |
|------|------------------------|---------------------|-----------|
| `affect_recall` (the gate) | 0.15 (5/33) | **0.06 (2/33)** | WORSE |
| `detection` (op+char) | 0.52 | **0.24 (8/33)** | COLLAPSED |
| `kind \| detection` | 0.18 | 0.12 (1/8) | flat-low |
| `toward \| relational` | 0/10 | 0/10 | unmoved |

**The hypothesis is REFUTED.** The Judgement's GO condition (correction #4) required
`kind | detection` to RISE **with `detection` held ≥ ~0.52**. Detection did the
opposite — it **collapsed** to 0.24. The format change lost the arcs the prose used to
land.

**Reading the raw output explains why (`read_raw_output_first` — done before trusting
the aggregate).** The failure mode **inverted**. The prose flooded (over-generated, many
wrong-kind shots on goal — which a recall gate rewards); the terse classifier went
**near-silent**. Detective protagonist Marren emits **2** ops (`F2 open loss`,
`F6 close retaliation`) against GT's **8**; most agents emit 1–2. The Judgement's own
levers caused this: "default none" + "ground every operation in the beat's own words /
never infer from plot shape or role" + deleting the arc-completion mandate together
suppressed emission. Against a recall metric (how many GT deltas we reproduce), fewer
shots = lower recall. The arc-closure mandate that the Judgement correctly named the
*invention* engine was also, incidentally, a *coverage* engine.

Note the inversion is genuine, not a tuning artifact: where prose anchored Marren's
loss to F2 (GT says F1, off-by-one) the classifier does the *same* F2 — placement did
not improve, only volume fell. The two failure modes (flood vs silence) **bracket** the
problem: neither register hits recall because the real residual is beat-alignment
(off-by-one beat ids) and kind-discrimination — not output register.

**Stop rule fires (correction #5).** This was the one permitted format iteration. It is
spent, and structured classification did **not** clear the gate — it regressed it. Per
the frozen Judgement, the conclusion is a **real kind-discrimination / beat-granularity
ceiling**, which fires the **reserved escalation** (FR-578 model scale, or revisiting
the six-kind taxonomy and the GT beat-granularity), **NOT** a second wording pass on the
classifier. The classifier rewrite is left in place as the executed frozen experiment
(L7 has no production graph; the spike is the artifact). A successor FR should carry the
reserved escalation; this FR is closed as a clean refutation.

## Alternatives Considered

- **Bind `char` to the beat's `subject` (the original FR-598 idea).** Insufficient:
  recall is the gate, and cast-flood cannot lower recall (extra cast only adds
  predictions). Detective protagonist-only recall = 0/8, identical to full-roster — the
  protagonist track itself is broken on *kind*, which subject-binding does not touch.
- **Scale the model.** Refuted by FR-578 (model-invariant 0.09) and by the trace: a
  bigger model writes a *better novel*, not a better classifier. The defect is format.
- **Fix `encode_affect` only.** Refuted by beat-level localization: the encode pass is
  faithful; the wrong kind is already chosen in the prose it consumes.
- **Keep prose but cap length.** Partial — a shorter novel is still a novel; interiority
  and synonym drift survive truncation. Structured classification removes the genre.

## Related

- Evidence (archived trace): [`FR-598-evidence/langsmith-trace-throughline-vs-encode.md`](FR-598-evidence/langsmith-trace-throughline-vs-encode.md)
- `examples/plot_modeller/prompts/affect_throughline.yaml`, `prompts/encode_affect.yaml`
- `examples/plot_modeller/spike_affect.py` (harness — already writes raw prose to `results/l7/throughlines/`)
- `examples/plot_modeller/evaluate.py` (`main_l7`, `_l7_counts` — frozen gate)
- Diagnostics: `logs/fr596-affect-throughline-spike.log`, `logs/l7-recall-breakdown.log`, `logs/l7-kind-localization.log`
- FR-596 (root-cause correction blockquotes), FR-597 (regenerability refutation)
- Diary: `docs/diary/diary-2026-06-26-i-measured-the-output-for-days-before-i-read-it.md`
