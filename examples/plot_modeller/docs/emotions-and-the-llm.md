# Emotions and the LLM — an appraisal-theory reading of the L7 affect arc

**Status:** Research note (durable). Distilled from FR-596 -> FR-605 and the
2026-06-26 metacognitive review. Not a spec; it justifies FR-607's direction.

## Thesis

Across the L7 affect arc the model behaved as if **an emotion were a label on a
beat**. Appraisal theory says it is not: an emotion is **an appraisal of an event
relative to a goal** (and, for social emotions, relative to an *agent* and a
*standard*). Every L7 failure we measured is a consequence of detecting the label
while discarding the referent — the goal. The affect layer is therefore not a
sibling of the goal layer; it is a **projection** of it.

## 1. The empirical spine (what the model actually did)

Four stable behaviors, observed over five FRs, two model scales, a per-kind sweep,
and a two-pass split:

- **Detects emotion words well** where present: `loss`/`hope` named 9/9.
- **Blind to relational emotions**: `guilt` 1/4, `betrayal` 0/2 (FR-605 pass-1 set).
- **Collapses endpoints onto the most dramatic beat**: 71% of supported-kind misses
  were `wrong_beat` single-pass; 39% after the two-pass split (FR-605 autopsy).
- **Attaches the right kind to a different but text-valid event** when it "misplaces":
  - horror `loss` = losing Fen (F4, never closes) vs GT entrapment (F1 open -> F6
    close when air is found);
  - quest `hope` = the kingdom saved (F8, the `liquidation` beat) vs the crown
    retrieved (F6, the `victory` beat).

These are not four bugs. They are one fact — *the referent is missing* — seen from
four sides.

## 2. The theory that names the one fact

Appraisal theory (Arnold -> Lazarus -> Roseman -> Scherer; Ortony/Clore/Collins, the
OCC model) holds that emotions are extracted from **evaluations of events**, not from
the events themselves. From Lazarus (1991), an emotion has three inseparable parts:

- **motivational** — *"Is this situation congruent or incongruent with my goals?"*
  (primary appraisal: relevance + congruence);
- **relational** — the person<->environment relationship;
- **accountability** — *"who is to be held accountable: self, other, or chance?"*
  (secondary appraisal).

OCC organizes the same insight into three branches: reactions to **events** (vis-a-vis
**goals**), to **agents' actions** (vis-a-vis **standards**), and to **objects**
(vis-a-vis **attitudes**). Mapped onto our kind set, the whole result falls out of one
structure:

| kind | appraisal (theory) | referent it requires | pipeline layer |
|---|---|---|---|
| `hope` | a goal looks **reachable** | *which goal* | L2 |
| `loss` | a goal/possession is **gone** | *which goal* | L2 |
| `guilt` | **I** am accountable for harm | self + another's goal | L1 + L6 |
| `betrayal` | an **other** defected from a shared goal | other-accountability | L1 + L6 |

Consequences, each matching an observed behavior:

- **The referent mismatch is not an error — it is appraisal theory.** "Loss" is
  undefined until you name the goal it appraises; horror has two valid goals
  ("survive", "keep my companions"). The model chose a different congruence-relation
  than the annotator. The emotion word was never the unit of meaning — the
  **(goal, congruence-flip)** pair is.
- **Relational blindness is the accountability axis.** `guilt`/`betrayal` are exactly
  the emotions whose appraisal lives in *secondary* appraisal (self vs other blame),
  unreadable from one protagonist's beat text. The model fails on precisely the kinds
  the theory says need an **agent** and a **standard** — the L1/L6 signals L7 was
  starved of.
- **Collapse onto the dramatic beat** is what a system does when it has **valence**
  (good/bad intensity) but no **goal trajectory** to say where the appraisal opens and
  closes. Salience is the only signal it has, so it anchors there.

This is why **scale failed** (Sonnet *worse* than haiku, recall 0.071): a bigger model
has a richer lexical/valence surface, but the missing structure is not lexical — it is
the goal model. More fluency on the wrong axis is confident motion in the wrong
direction. SOTOPIA (Zhou et al., 2023) reports the behavioral analogue: even GPT-4's
*goal-completion* in social scenarios falls well below humans. The deficit is
goal-tracking, not emotion vocabulary.

## 3. The metacognitive turn: our metric made the model's mistake about the model

The finding worth keeping is that **our measurement recapitulated the model's failure
one level up.**

- The model labeled emotions by their **surface word** and lost the **referent** (the
  goal).
- We scored the model by **beat-id equality** and lost the **referent** (that two valid
  goals license two valid beats). The `wrong_beat` bucket counted `predicted_id !=
  gold_id` and *named it a placement error* — exactly as the model counted "this beat
  reads as loss" and named it the loss.

Both are the same shape: **an identifier substituted for the thing it refers to.** The
model used the emotion token as a proxy for the appraisal; we used the beat id as a
proxy for the appraisal. Neither proxy carries the goal, so both collapse distinct
referents into one and call the survivors "wrong."

The cure was identical at both levels and embarrassingly cheap: **read the prose.** The
arc — five FRs, two model scales, a per-kind sweep, a two-pass split — was metric
archaeology. The diagnosis that moved the problem came from reading two beat files
against the gold goal. The general law, sharper than the existing Scripture scars
(`read_raw_output_first`, `metric_archaeology_before_reading_output`):

> **A metric computed over identifiers cannot distinguish a referent disagreement from
> an error, so it will always misreport the first as the second.** No placement-prompting
> lever can fix a number that is measuring the wrong thing.

## 4. Implication and the honest boundary

Constructively (and this is what FR-607 encodes): **affect should be derived from the
goal layer, not detected in parallel with it.** A `loss` delta whose referent is
`goal_escape` is a different datum from one whose referent is `goal_keep_companions`,
and scoring should accept either if it is text-grounded. That is appraisal theory made
into a schema: the typed referent is the **goal** (L2), the accountability axis is the
**L1/L6 relation**, the kind is the **valence sign**.

The boundary, stated plainly: none of this shows the model *feels* or *understands*
emotion. It shows the opposite — a strong **emotion-lexicon prior** over a weak
**goal-appraisal model** — and a gate that, by scoring tokens-on-beats, rewarded the
prior and could not see the gap. The real subject of the arc is not emotion. It is
that **asking an LLM to locate an emotion is asking it to track a goal; whichever of
the two lacks the goal model fails in a way that looks like a labeling error and is
actually a referent error.**

## Seed

If emotion is appraisal-of-goal, the affect layer may be a *projection* of the goal
layer: `affect = sign(delta goal_congruence)` at each beat. Could L7 be replaced by a
deterministic reader over L2/L6 goal-state transitions, with the LLM only naming goals
and their congruence flips — moving emotion from a thing to **detect** to a thing to
**compute**, so the gate measures goal-tracking directly (the capability actually in
question)?

## Sources

- Lazarus, R. S. (1991). *Progress on a cognitive-motivational-relational theory of
  emotion.* American Psychologist, 46(8).
- Roseman, I. J. (1996). *Appraisal determinants of emotions.* Cognition & Emotion,
  10(3) — motive-consistency x accountability.
- Scherer, K. R. (2001). *Appraisal considered as a process of multilevel sequential
  checking.* (relevance -> implication/goal-conduciveness -> coping -> normative checks)
- Ortony, Clore & Collins (1988). *The Cognitive Structure of Emotions* (OCC):
  events->goals, agents->standards, objects->attitudes.
- Zhou et al. (2023). *SOTOPIA: Interactive Evaluation for Social Intelligence in
  Language Agents.* arXiv:2310.11667 — LLM social-goal completion below human.

## Related (in-repo)

- `feature-requests/FR-605-l7-two-pass-affect-what-then-where.md` — REFUTED; its
  prose-grounded post-mortem is the empirical basis here.
- `feature-requests/FR-607-goal-anchored-affect-referent.md` — operationalizes the
  typed-referent thesis (GT referent enrichment + goal-anchored isolation spike +
  referent-aware scoring).
- `feature-requests/FR-606-affect-rationale-field.md` — the legibility sibling.
- `docs/diary/diary-2026-06-26-the-emotion-had-the-wrong-referent.md` — the diary
  reflection that seeded this note.
- `examples/plot_modeller/docs/architecture.md` — the L1..L7 layer stack.
