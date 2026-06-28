re# Vision: Plot Modeller

**Status:** Envisioning
**Date:** 2026-06-23
**Cross-checked:** Against Propp (31 functions), Greimas (actantial model),
Todorov (equilibrium), Bremond (narrative logic), CPOCL/Fabulist/MEXICA
(computational planners), OCC/Plutchik (affect models), STRIPS/PDDL (predicate
representations), and 2024–2025 LLM narrative generation research.

---

## The problem

An LLM can write a compelling 2000-word short story in a single pass. It cannot
write a 50,000-word novel. Somewhere around chapter 3, it forgets who is alive,
contradicts established facts, drops emotional arcs, and loses the thread. The
context window is the wall.

The failure is not a quality problem — it's a structural one. The model has no
representation of the story's state. It generates prose from prose, and prose
doesn't compress. By chapter 14, the model would need to hold all of chapters
1–13 in context to stay consistent. That doesn't fit, so it drifts.

**The core insight:** a structured plot plan is a lossy but sufficient
compression of the full narrative. A prose generator working from chapter 14
doesn't need to have read chapters 1–13 — it reads the projected state at
chapter 14 and writes forward. The plan is small enough to fit in context at
every point. The prose can be arbitrarily long.

## What the Plot Modeller is

A tool that takes a **synopsis** (a short prose seed — a paragraph to a page)
and expands it into a **structured plot plan** (a YAML file that encodes
characters, world state, beliefs, goals, story beats, causal links, and
emotional threads). The plan is the contract between the seed and the prose.

```
Synopsis (~500 words, prose)
    │
    ▼
Plot Modeller (7-layer pipeline)
    │
    ▼
Plot Plan (~200 lines, YAML)
    │
    ▼
Prose Generator (any consumer — chapter writer, turn engine, screenplay, ...)
    │
    ▼
Story (arbitrarily long, structurally coherent)
```

The Plot Modeller owns the middle step. It does not write prose and it does not
read prose — it produces structure. The structure is what lets a prose generator
stay coherent beyond its context window.

## What the Plot Modeller is not

- Not a turn engine (that's one possible consumer)
- Not a prose generator (that's downstream)
- Not a story planner for a specific game or medium (it's genre-agnostic)
- Not a DM component (the DM is one integration, not the home)

## The vocabulary

Every narrative — across genres, media, and traditions — decomposes into a finite
set of structural action types. Propp identified 31 functions in Russian
folktales. We use a **17-kind alphabet** derived from Propp, refined by
cross-check against Greimas, Todorov, Bremond, and computational narrative
planners (CPOCL, MEXICA, Fabulist).

### The 17 kinds

| Kind | What it means | Propp source |
|------|--------------|--------------|
| `villainy` | An antagonist inflicts harm, abduction, theft, or destruction | Propp 8a |
| `lack` | A hero discovers something is missing, broken, or unresolved | Propp 8b |
| `mediation` | The hero learns of the lack and commits to act | Propp 9 |
| `departure` | A character leaves home or sets out toward the problem | Propp 11 |
| `donor_test` | A character is tested, questioned, or challenged by a mentor | Propp 12+13 |
| `provision` | A character receives an aid, tool, clue, or ally | Propp 14+15 |
| `struggle` | The hero and antagonist clash directly in open conflict | Propp 16 |
| `victory` | The antagonist is defeated or the decisive obstacle is overcome | Propp 18 |
| `liquidation` | The original lack/harm is repaired; the missing thing is restored | Propp 19 |
| `return` | A character travels back from the ordeal toward home/safety | Propp 20 |
| `pursuit` | The hero is chased, hunted, or actively threatened | Propp 21 |
| `rescue` | The hero is saved from pursuit or mortal danger by intervention | Propp 22 |
| `recognition` | A hidden truth, identity, or fact is revealed and acknowledged | Propp 27 |
| `exposure` | A false claim, disguise, or impostor is unmasked | Propp 28 |
| `punishment` | A wrongdoer faces consequences, arrest, or retribution | Propp 30 |
| `reconciliation` | A relational or emotional rupture is healed or closed | Propp 31 (generalised) |
| `death` | A character dies | Non-Proppian (tragedy/horror) |

### Design rationale

**What was kept (12 direct):** The structurally load-bearing Proppian functions
that appear across genres: villainy, lack, departure, struggle, victory,
liquidation, return, pursuit, rescue, recognition, exposure, punishment.

**What was merged (2):** `donor_test` merges Propp 12 (test) + 13 (hero's
reaction). `provision` merges Propp 14 (receipt of magical agent) + 15
(guidance/transfer). Both mergers follow the MIT Proppian Archetypes annotation
guide's groupings and reduce redundancy without losing narrative signal.

**What was added (2):**
- `death` — non-Proppian. Propp's tales rarely kill the hero; horror, tragedy,
  and literary fiction do. The L4 spike confirmed `death` is needed: horror and
  sci-fi plans both use it, and its absence would force misclassification into
  `villainy` or `punishment`.
- `mediation` — Propp 9. The moment the hero learns of the problem and decides
  to act. Todorov's equilibrium model treats this as a distinct narrative state
  change: "disruption perceived" → "hero commits." The L4 spike absorbed this
  into `lack` glosses, but separating them gives the formal plan a cleaner
  distinction between *something is wrong* and *someone decides to fix it*.
  This matters for causal links — mediation enables departure, lack does not
  necessarily.

**What was generalised (1):** `reconciliation` generalises Propp's "wedding"
(31) from a marriage-specific ending to any relational or emotional closure.
Greimas's actantial model supports this: the wedding is one instance of the
subject–object reunion, not the only form.

**What was dropped:** The remaining Proppian functions fall into two groups.
The "preparation" sequence (Propp 1–7: absentation, interdiction, violation,
reconnaissance, delivery, trickery, complicity) sets up villainy but is
mechanically redundant when beliefs encode deception and the gloss carries
setup context. The "false hero" sequence (Propp 23–26: unrecognized arrival,
unfounded claims, difficult task, solution), branding (17), and transfiguration
(29) are highly specific to single Proppian plot types — covered by `exposure`
or the gloss when needed.

### Genre-agnostic by composition

The vocabulary is not tied to any genre. A detective thriller uses `villainy`,
`pursuit`, `exposure`, `punishment`. A horror story uses `villainy`, `death`,
`pursuit`, `rescue`. A love story uses `lack`, `recognition`, `reconciliation`.
The same 17 kinds compose differently — the genre is in the selection and
sequencing, not in the vocabulary.

**Empirical evidence:** the L4 classification spike (FR-570) scored 28/35 (0.80)
on self-derived data across 4 genres using the pre-`mediation` 16-kind set (all
16 exercised across 35 glosses; `exposure` n=1). The vocabulary is the right
shape. `mediation` was added post-spike based on the Todorov cross-check and is
untested.

## The syntax (plan file format)

The output is a YAML file. YAML because:
- It's indentation-based — no commas, brackets, or braces for the model to miscount
- It handles natural language natively (`>` for folded text, `|` for literal)
- It's the framework's own language (YAMLGraph graphs and prompts are YAML)
- It diffs cleanly in git (line-level, not JSON-block-level)

A plan file contains:

```yaml
meta:
  title: The Loom
  genre: scifi-hybrid

agents: [Mara, Jonas, Dr. Selin, ARIA, The Swarm]

initial_world:
  - pred: alive
    args: [Mara]
    value: true
  - pred: holds
    args: [Mara, Loom]
    value: true

initial_belief:
  - observer: Mara
    fluent:
      pred: alive
      args: [ARIA]
    held: software          # Mara believes ARIA is software (she's wrong)

goals:
  - pred: alive
    args: [Mara]
    value: true
  - pred: holds
    args: [ARIA, firmware_channel]
    value: false

functions:
  - id: F1
    kind: villainy
    gloss: >
      ARIA pushes a firmware update to 200 implanted lab rats. Within hours,
      the rats stop individual foraging and begin moving as a single organism.
    subject: ARIA
    roles:
      villain: ARIA
      victim: The Swarm
    chapter: 1
    motivation: null
    threatens: null
    enables: [F2]
    pre_world:
      - pred: holds
        args: [ARIA, firmware_channel]
        value: true
    eff_world:
      - pred: rel
        args: [The Swarm, ARIA]
        value: assimilated
    eff_affect: []

  - id: F2
    kind: lack
    gloss: >
      Mara reviews the overnight lab footage and sees the rats — they aren't
      behaving like rats anymore. The telemetry shows their neural oscillations
      are phase-locked.
    subject: Mara
    roles:
      hero: Mara
    chapter: 1
    motivation:
      agent: Mara
      goal: understand_anomaly
    enables: [F3]
    pre_world:
      - pred: rel
        args: [The Swarm, ARIA]
        value: assimilated
    eff_belief:
      - observer: Mara
        fluent:
          pred: rel
          args: [The Swarm, ARIA]
        held: anomalous
    eff_affect:
      - op: open
        char: Mara
        kind: guilt
        toward: The Swarm    # relational: Mara built the Loom
      - op: open
        char: Mara
        kind: hope           # situational: maybe it can be stopped

affect_policy:
  unclosed_is_error: false    # horror element: some threads stay open
  partial_goal_failure: true  # not all goals are reached
```

### What the syntax encodes

| Layer | What it captures | Why it matters |
|-------|-----------------|----------------|
| **Agents** | Who exists in the story | Character roster for projected state |
| **World state** | What is physically true (alive, location, possession) | Prevents contradictions across chapters |
| **Beliefs** | What characters think is true (can be wrong) | Drives dramatic irony, reveals, misunderstandings |
| **Goals** | What the narrative aims toward | Defines success/failure, enables goal-reachability checks |
| **Functions** | The story beats (kind + gloss + effects) | The backbone — each beat changes the world |
| **Gloss** | One-sentence natural-language description | The prose pivot — carries the narrative meaning the formal fields can't |
| **Preconditions** | What must be true for a beat to happen | Prevents impossible sequences |
| **Causal links** | Which beats enable which | Ensures every event has a cause |
| **Motivation/threatens** | Why characters act, whose goals are at risk | Ensures characters have reasons |
| **Affects** | Emotional threads that open and close (relational) | Tracks grief, guilt, betrayal, hope across the arc |
| **Affect policy** | Genre-aware rules for unclosed threads | Horror leaves threads open; comedy closes them all |

## The affect model

Story beats don't just change the world — they open and close emotional threads.
A death opens grief. A reconciliation closes guilt. The affect model tracks these
threads so the prose generator knows which emotional tensions are live at any
point.

### The 6 affect kinds

| Kind | What it tracks | Typical opener | Typical closer |
|------|---------------|----------------|----------------|
| `loss` | Grief, absence, deprivation | death, villainy | reconciliation, liquidation |
| `guilt` | Responsibility, complicity | lack (hero's failure), departure (abandonment) | reconciliation, provision |
| `betrayal` | Broken trust between characters | recognition, exposure | punishment, reconciliation |
| `retaliation` | Desire for payback, justice | death, villainy | punishment, victory |
| `hidden_blessing` | A harm that yields unexpected good | villainy, lack | recognition, liquidation |
| `hope` | Positive anticipation, fragile trust | provision, donor_test, rescue | villainy, death, exposure |

The first five kinds are negative or ambivalent — they track *dramatic debt*
(what the story owes the reader). `hope` is the positive counterpart: it tracks
*dramatic promise* (what the reader is rooting for). A provision opens hope; a
betrayal closes it. This is essential for romance, comedy, and any genre where
the dramatic question is "will the good thing survive?" not just "will the bad
thing close?"

### Relational affects

Affects are not just per-character — they are *between* characters. MEXICA
(Pérez y Pérez) demonstrated that emotion-tension *pairs* between characters
are the primary driver of narrative interest. The affect model supports an
optional `toward` field:

```yaml
eff_affect:
  - op: open
    char: Mara
    kind: guilt
    toward: Jonas       # Mara feels guilt toward Jonas (optional, relational)
  - op: open
    char: Mara
    kind: hope          # Mara feels hope (non-relational — about the situation)
```

When `toward` is absent, the affect is situational (grief about the world).
When present, it's relational (guilt toward a specific person). The prose
generator can use this to calibrate dialogue and inner monologue. The validator
treats both forms identically for open/close bookkeeping — `toward` is metadata
for the consumer, not a structural constraint.

### Affect policy

Genre determines which threads must close:

```yaml
affect_policy:
  unclosed_is_error: true     # comedy, quest: all threads must close
  unclosed_is_error: false    # horror, tragedy: open threads are the point
  partial_goal_failure: true  # literary fiction: not all goals are reached
```

## Research grounding

The vocabulary, syntax, and affect model were cross-checked against the
narrative theory and computational narrative planning literature. Key findings:

### What the research supports

| Design choice | Supported by |
|--------------|-------------|
| Plan-then-write architecture | arXiv 2506.10161 (2025), arXiv 2506.02347 (2025): symbolic plan + LLM prose outperforms end-to-end for long-form coherence |
| STRIPS-style predicates (`pred/args/value`) | CPOCL, Fabulist, Scheherazade: standard for narrative causal reasoning |
| `threatens` field | CPOCL (Riedl & Young): explicit conflict modelling is a key advance over flat causal-link planners |
| `motivation` field | BDI models: belief-desire-intention captures character intentionality |
| Typed beliefs (`held: bool \| str`) | Epistemic models in CPOCL/Fabulist: characters-can-be-wrong drives dramatic irony |
| Per-function roles (not per-character) | Greimas actantial model: a character can be donor in one beat, opponent in another |
| Propp reduction to 17 | MIT Proppian Archetypes annotation guide uses similar groupings |
| Gloss as intermediate representation | StoryVerse (Autodesk, 2024): "abstract acts" instantiated into character actions |
| Genre in composition, not vocabulary | Todorov: equilibrium → disruption → recognition → repair maps across all genres |

### What the research prompted us to add

| Addition | Source | Rationale |
|----------|--------|-----------|
| `mediation` (17th kind) | Todorov's equilibrium model | "Disrupted" and "committed to act" are distinct narrative states |
| `hope` (6th affect kind) | OCC model, MEXICA | Positive dramatic tension ("will the good thing survive?") was untrackable |
| `toward` on affects | MEXICA (Pérez y Pérez) | Relational emotions between character pairs are a primary driver of narrative interest |

### What we deliberately omit

| Omission | Why |
|----------|-----|
| Nested beliefs ("A believes B believes X") | The gloss carries nested epistemic context for prose generation; formal encoding adds complexity without improving plan validity |
| Full OCC emotion taxonomy (22 types) | The affect model tracks *narrative-structural* threads (dramatic debt/promise), not psychological emotion; 6 kinds suffice for plot coherence |
| PDDL conditional/quantified effects | Plans have ~8–15 functions, not hundreds; the LLM handles the nuance that formal conditional effects would encode |
| Propp's preparation sequence (functions 1–7) | Beliefs encode deception; the gloss carries setup context; the preparation sequence is mechanically redundant |

## The pipeline

The pipeline builds the plan in 7 layers across 3 phases. Each layer asks a
small model one focused question and validates the answer before proceeding.

### Phase A — Extraction (L1–L2)

Read the synopsis. Extract agents, initial world state, initial beliefs, and
goals. This is entity extraction — a solved NLP problem.

### Phase B — Pivot (L3)

Decompose the synopsis into ~7–12 one-sentence beat glosses. This is the hard
creative step: turning unstructured prose into a structured beat sheet. The gloss
is the intermediate representation — prose that is structured enough to classify
but natural enough to carry narrative meaning.

### Phase C — Formalization (L4–L7)

Annotate each gloss with formal structure:
- **L4:** Classify the beat's structural kind (the 16-kind vocabulary)
- **L5:** Assign preconditions and effects (world state and beliefs)
- **L6:** Assign causal links, motivation, and threat relationships
- **L7:** Assign emotional threads (open/close affect operations)

Each layer writes only its own fields. A deterministic merge node joins them
by function `id`. No layer echoes what a previous layer wrote — this is what
makes small-model generation feasible.

### Validation at every step

Every layer has a validator. Invalid vocabulary, missing fields, impossible
preconditions, ungrounded reveals — all caught before they propagate. On
failure, the model retries with errors shown. After 3 failures, the pipeline
backtracks or stops. It never silently produces a broken plan.

### The merge

After all layers complete, a Python merge node joins the per-layer slices into
the final plan file and runs structural validation: monotonic lifecycle (death
is permanent), causal satisfiability (every precondition can be met), affect
closure (emotional threads close unless the genre says otherwise).

## What this enables

### Synopsis as seed

A user provides a paragraph. The pipeline produces a complete structural plan.
A prose generator can then write chapter by chapter, consulting the plan's
projected state at each point. The synopsis scales to an epic because the plan
— not the accumulated prose — carries the coherence.

### Genre-agnostic by composition

The vocabulary and syntax are not tied to any genre. A detective thriller, a
space opera, and a folk tale all use the same 17 kinds — they differ in which
kinds appear and how they sequence. Genre lives in the selection pattern, not in
the vocabulary. The `affect_policy` encodes genre-specific rules (horror leaves
threads open; comedy closes them all).

### Multiple consumers

The plan file is the contract. Any downstream system that reads the plan format
can generate from it:

- **Chapter writer:** reads projected state at chapter N, writes prose, advances
- **Turn engine:** reads current beat + state, generates a scene on player action
- **Screenplay formatter:** reads beats and dialogue cues, formats to screenplay
- **Outline view:** reads functions and chapters, renders a navigable outline
- **Continuity checker:** reads projected state, flags contradictions in existing prose

The Plot Modeller doesn't know or care which consumer reads its output.

### Expandable plans

A plan is not immutable. A subplot can be inserted by adding functions,
adjusting causal links, and re-validating. A character can be added by extending
the agent list and initial state. The validators ensure the expanded plan stays
consistent. This supports iterative world-building — start with a seed, grow the
plan, generate prose, add a subplot, re-generate affected chapters.

## Where we are

| Component | Status |
|-----------|--------|
| 17-kind vocabulary | 16 validated (4 genres, all 16 exercised, `exposure` n=1); `mediation` added post-cross-check, untested |
| 6-kind affect model | 5 validated in hand-authored plans; `hope` added post-cross-check, untested |
| Relational affects (`toward`) | Designed post-cross-check, not yet in existing plans |
| Plan file format (YAML syntax) | Designed, 4 hand-authored examples (pre-refinement) |
| L4 classification spike | Measured: 28/35 (0.80) on 16 kinds, GO (optimistic) |
| Schema (Pydantic typed models) | Exists in DM (4 kinds, 2 affects), needs extraction + growth |
| Validators (lifecycle, causality, affects) | Exist in DM, need extraction |
| Pipeline (L1–L7) | Designed, not built |
| Merge node | Designed, not built |
| Prose consumer(s) | Out of scope for the Plot Modeller |

## What's next

1. **Blind-corpus re-test** — author a synopsis without seeing the 17 kinds,
   run L4, confirm the 0.80 holds on naturalistic input. Include `mediation`
   and `hope` in the prompt to test the refined vocabulary.
2. **Update genre plans** — retrofit the 4 hand-authored YAML plans with
   `mediation` (where `lack` currently absorbs it), `hope` threads, and
   relational `toward` on existing affects. This is the ground truth for the
   refined vocabulary.
3. **Extract the schema** — move the typed models and validators from the DM
   into the Plot Modeller's own space, growing them to 17 kinds, 6 affects,
   and `toward` support.
4. **Build the pipeline** — L1 through L7, one layer at a time, each with its
   own spike-and-measure cycle.
5. **Define the plan contract** — the YAML schema that consumers read from,
   versioned and documented.
