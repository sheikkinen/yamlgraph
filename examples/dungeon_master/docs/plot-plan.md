# Plot Plan (v3 Belief Lane)

The plot plan is an optional, typed layer that steers prose generation from a
formal narrative model. When attached, it controls which characters appear
onstage, what the narrator may reveal, and what emotional arcs must resolve.
When absent, the generation pipeline is byte-for-byte v2 (the dormancy
invariant).

## Mental model

A story is a sequence of chapters. Before prose is written, the plot plan
authors the story's *dramatic structure* as a set of **functions** (beats) --
typed events with preconditions and effects on world-truth, character beliefs,
and emotional arcs. The plan is validated against four narrative invariants,
then consumed by two runtime seams that shape every turn.

```
synopsis
  |
  v
[author_plot_plan.yaml]       LLM authors the formal model
  |                           (author -> validate -> repair loop)
  v
parse_plot_plan               tolerant boundary: drop off-alphabet atoms
  |
  v
write_plot_plan               gated write: validate_plan must pass
  |
  v
doc["plot_plan"]              attached to story doc (JSON-serializable dict)
  |
  +---> chapter_open          M1 exclusion: who must NOT appear onstage
  +---> invoke_turn           M4b realize: beat directive merged into instruction
```

## The formal model: `<I, A, G, F, E>`

A `PlotPlan` is a five-part structure (schema in `api/plot/schema.py`):

| Part | Field | What it represents |
|------|-------|--------------------|
| **I** (initial state) | `initial_world`, `initial_belief` | World truths and character beliefs at the start of the story |
| **A** (agents) | `agents` | Characters who perform actions |
| **G** (goals) | `goals` | World truths that must hold at the finale |
| **F** (functions) | `functions` | The authored beats -- typed events with pre/effects |
| **E** (ordering) | `order` | Pairwise before-edges `(A, B)` meaning A must precede B |

### Functions (beats)

Each `Function` is one narrative beat:

```
F1: villainy
  subject: Antagonist    target: Arnulf
  chapter: 1
  eff_world:  []                             -- world-truth: Arnulf is still alive
  eff_belief: [Clan believes alive(Arnulf) = False]  -- but the clan thinks he's dead
  eff_affect: [open loss(Hilde)]             -- Hilde begins grieving
```

A function's `kind` comes from a closed Propp-like alphabet:

| Kind | Meaning |
|------|---------|
| `villainy` | An antagonistic act that changes the world or beliefs |
| `reveal` | A truth is disclosed to one or more observers |
| `reconciliation` | An emotional or relational resolution |
| `return` | A character re-enters the story |

### The belief/world-truth distinction

This is the core insight of the plot model. Two separate layers track reality:

- **World-truth** (`eff_world`): what is objectively true. "Arnulf is alive."
- **Belief** (`eff_belief`): what a character *thinks* is true. "The clan believes Arnulf is dead."

A "presumed dead" arc never kills the character in world-truth. It only
manipulates belief:

```
Ch 1 (villainy):  world: alive(Arnulf)=True   belief: Clan.alive(Arnulf)=False
                  (he's alive, but they think he's dead)

Ch 6 (reveal):    world: alive(Arnulf)=True   belief: Clan.alive(Arnulf)=True
                  (the truth comes out)
```

This distinction drives the exclusion seam: a character who is alive in
world-truth but believed dead by all observers is excluded from appearing
onstage until the reveal.

### Preconditions and effects

Each function declares:

| Field | Purpose |
|-------|---------|
| `pre_world` | World truths that must hold before this beat fires |
| `pre_belief` | Beliefs that must hold before this beat fires |
| `eff_world` | World truths this beat establishes |
| `eff_belief` | Beliefs this beat changes |
| `eff_affect` | Emotional arcs this beat opens or closes |

### Affect deltas (emotional arcs)

Modeled after Lehnert Plot Units. Each `AffectDelta` is an `open` or `close`
operation on a `(character, kind)` pair:

| Kind | Meaning |
|------|---------|
| `loss` | Grief, mourning, perceived absence |
| `guilt` | Remorse, culpability |

An affect opened at Ch 1 must be closed by the end of the story (or explicitly
declared `intentional_open` for tragic/unresolved endings). The validation
check enforces this.

## Authoring pipeline

### 1. LLM authors the plan (`plot_plan.yaml`)

The graph has three nodes:

```
START -> author_plan -> validate_plan --[ok]--> END
                             |
                          [flawed]
                             |
                             v
                        repair_plan -> validate_plan  (loop, max 3 iterations)
```

- **`author_plan`**: LLM node. Prompt (`author_plot_plan.yaml`) receives the
  synopsis as `premise` and outputs a JSON `PlotPlan`. On repair iterations,
  the `flaws` variable is populated with concrete flaw descriptions.
- **`validate_plan`**: Python node. Runs all four narrative invariant checks
  (no LLM). Returns `{ok: bool, flaws: [...]}`.
- **`repair_plan`**: LLM node. Same prompt, but with flaws fed back so the
  LLM can fix them.

The loop budget is 3 iterations. If the budget is spent, the last-authored
plan is emitted (and caught by the write gate).

### 2. Tolerant parse boundary (`parse_plot_plan`)

The LLM's JSON output passes through `parse_plot_plan` (in `api/plot/author.py`),
which applies tolerant normalization:

- Unknown top-level fields: stripped
- Unknown `kind` on a Function: entire function dropped
- Unknown `pred` on a Fluent: fluent dropped
- Unknown affect `kind`: affect delta dropped
- Parse failure: returns empty `PlotPlan()` (never raises mid-pipeline)

This boundary ensures downstream code only sees well-typed atoms from the
closed alphabets.

### 3. Gated write (`write_plot_plan`)

The write seam in `chapter_nav.py` runs `validate_plan` before committing:

```python
def write_plot_plan(doc, plan):
    result = validate_plan(plan)
    if not result.ok:
        raise InvalidPlotPlan(result.flaws)
    doc["plot_plan"] = plan.model_dump()
```

A plan that fails validation never reaches the doc. The gate is bound to the
**write**, not the writer -- every code path that attaches a plan must go
through this function.

### 4. Producer glue (`doc_ops.author_plot_plan`)

The `author_plot_plan` function in `doc_ops.py` orchestrates steps 1-3:

1. Read the synopsis from the doc
2. Run the `plot_plan.yaml` graph
3. Parse through `parse_plot_plan`
4. Write through `write_plot_plan` (which validates)
5. Persist to disk via `story_doc.write`

Called from `generate_story` when `enable_plot_plan=True` (the `--plot-plan`
CLI flag). Graceful degradation: `InvalidPlotPlan` is caught, and generation
continues without a plan.

### Triple validation

The plan is validated three times by design:

1. **Inside the graph's repair loop** -- the LLM's feedback channel
2. **By `write_plot_plan`'s gate** -- the un-bypassable commit guard
3. **Implicitly by `parse_plot_plan`** -- dropping off-alphabet atoms

## Validation checks

Four pure narrative invariants (no LLM, no planning engine):

### 1. Monotonic lifecycle (`lifecycle_violation`)

Once world-truth asserts `alive(c)=False`, no later beat may assert
`alive(c)=True` in world-truth. Dead characters stay dead in reality.

Belief revival is explicitly allowed -- that's what a reveal does.

### 2. Grounded reveal (`ungrounded_reveal`)

A beat that sets `believes(observer, alive(c))=True` must have had a prior
beat (or initial belief) that set that observer's belief to `False`. You
cannot reveal a truth that was never concealed. "Nothing to un-tell" is the
flaw.

### 3. Causal antecedent (`open_condition`)

Every precondition (`pre_world`, `pre_belief`) must exist in the initial
state or be produced by an earlier-ordered beat. A beat that requires
"Hilde believes Arnulf is alive" cannot fire if no prior beat established
that belief.

### 4. Affect closure (`unclosed_affect`)

Every emotional arc opened by a beat must be closed by a later beat. An
`open loss(Hilde)` at Ch 1 must have a matching `close loss(Hilde)` later
in the ordered sequence. Residual open units are flaws, localized to the
opening beat.

Exception: `intentional_open` pairs `[(char, kind)]` are exempt -- for
tragic or deliberately unresolved endings.

## Runtime consumption

### Exclusion seam (M1) -- `chapter_open.py`

On every turn, `compile_opening_onepager` builds the deterministic context
for the chapter. When a plan is attached:

```python
plan = attached_plot_plan(doc)
if plan is not None:
    for char_id in exclusion_set(plan, chapter_index):
        if char_id not in must_exclude:
            must_exclude.append(char_id)
```

`exclusion_set(plan, chapter)` returns characters whose `alive` belief is
`held=False` for any observer at or before `chapter`, with no later restore
within that range. These characters are excluded from the onepager -- they
cannot appear onstage until the reveal.

The seam is additive: it can only add exclusions, never remove v2 constraints.

### Beat instruction (M4b) -- `turn_ops.py`

On every turn, `invoke_turn` checks for an attached plan:

```python
plan = attached_plot_plan(doc)
if plan is not None:
    beat = beat_instruction(plan, chapter_index)
    instruction = merge_beat_instruction(instruction, beat)
```

`beat_instruction(plan, chapter)` renders the authored beat(s) for that
chapter as a prose directive, focalized on belief (never revealing
world-truth). The directive is merged additively into the turn instruction
that steers the LLM.

A chapter with no beats returns `""` -- the merge is a no-op and the turn
instruction is unchanged.

## Activation

The plot plan is opt-in:

```bash
# CLI flag
python examples/dungeon_master/scripts/generate.py \
  --premise "..." --out outputs/test --plot-plan

# Shell wrapper (env var)
PLOT_PLAN=1 examples/dungeon_master/scripts/generate_and_review.sh \
  outputs/test "..." 256
```

When the flag is off (or absent), `author_plot_plan` is never called, no plan
is attached, and both runtime seams pass through unchanged. This is the
dormancy invariant -- the v3 infrastructure is strictly additive.

## Projection functions (`api/plot/project.py`)

Pure read-only functions over a `PlotPlan`:

| Function | Returns |
|----------|---------|
| `ordered_functions(plan)` | Topologically sorted beats (by `order` edges, ties by chapter) |
| `chapter_cast(plan, chapter)` | Characters involved in beats at that chapter |
| `exclusion_set(plan, chapter)` | Characters believed dead at that chapter (for M1 seam) |
| `belief_at(plan, chapter)` | `(observer, char) -> held` map of alive-beliefs at that chapter |
| `protected_set(plan)` | Characters appearing in `goals` (survival invariants) |

## The floodmark fixture

The canonical test fixture (`api/plot/floodmark.py`) encodes a "presumed dead"
arc:

```
Initial:  alive(Arnulf)=True       Clan.believes(alive(Arnulf))=True

F1 (villainy, Ch 1):
  eff_belief: Clan.believes(alive(Arnulf))=False    -- clan thinks he's dead
  eff_affect: open loss(Hilde)                      -- Hilde grieves

Fr (reveal, Ch 6):
  eff_belief: Clan.believes(alive(Arnulf))=True     -- truth comes out
  eff_affect: close loss(Hilde), open guilt(Hilde)  -- grief ends, guilt begins

Ff (reconciliation, Ch 6):
  eff_affect: close guilt(Hilde)                    -- guilt resolved
```

Arnulf is alive in world-truth the entire time. Only belief changes. The
exclusion seam keeps Arnulf offstage in chapters 2-5 (between the villainy
and the reveal). The realize seam injects the beat directives at chapters 1
and 6.

Nine variant fixtures test each validation check and edge case: lifecycle
violation (world-truth revival), ungrounded reveal (nothing to un-tell),
open condition (missing antecedent), unclosed affect (dropped confrontation),
and more.

## File map

```
api/plot/
  schema.py       PlotPlan, Function, Fluent, Belief, AffectDelta, PlanFlaw
  project.py      Pure projections: ordered_functions, exclusion_set, belief_at, ...
  validate.py     Four narrative invariant checks + validate_plan
  author.py       parse_plot_plan (tolerant boundary) + graph Python node
  realize.py      beat_instruction + merge_beat_instruction (M4b)
  floodmark.py    Canonical fixture + 9 named variants
  __init__.py     Re-exports

api/chapter_nav.py    write_plot_plan (gated write), attached_plot_plan (typed read)
api/doc_ops.py        author_plot_plan (producer: graph -> parse -> gate -> persist)
api/chapter_open.py   Exclusion seam (M1): exclusion_set unioned into must_exclude
api/turn_ops.py       Realize seam (M4b): beat_instruction merged into instruction

plot_plan.yaml              Authoring graph (author -> validate -> repair)
prompts/author_plot_plan.yaml   LLM prompt for plan authoring

scripts/generate.py         --plot-plan flag, calls author_plot_plan after cast derivation
scripts/generate_and_review.sh   $PLOT_PLAN env var passthrough
```
