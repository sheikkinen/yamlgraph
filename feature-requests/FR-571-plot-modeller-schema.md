# Feature Request: FR-571 Plot Modeller — Schema extraction and growth

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced — GO (schema + 3 validators built; 14 schema + 8 validator tests green; all downstream layers L1–L5 consume it; 2026-06-24)
**Effort:** 1 day
**Requested:** 2026-06-23
**Plan:** [`plan-implementation-phases.md`](../examples/plot_modeller/docs/plan-implementation-phases.md) Phase 0
**Predecessor:** FR-570 (L4 spike, enforced)
**Blocks:** FR-572 (vocabulary validation), all subsequent pipeline FRs

## Summary

Extract the typed schema and validators from `examples/dungeon_master/api/plot/`
into `examples/plot_modeller/schema/` and `examples/plot_modeller/validators/`,
growing the vocabulary from 4 kinds / 2 affects to 17 kinds / 6 affects with
relational `toward` support and typed beliefs (`held: bool | str`).

## Value statement

The Plot Modeller's schema currently lives inside the Dungeon Master example.
The DM is one consumer, not the home. The Plot Modeller needs its own typed
core so vocabulary growth (4 kinds → 17) does not perturb the DM.

**This is a deliberate fork, not a live extraction (J:C1).** The DM keeps its
4-kind / 2-affect schema as a *different contract* (it models a turn engine, not
a plan compiler); the Plot Modeller gets its own 17-kind / 6-affect schema. The
two diverge permanently. Because the modules will be structurally similar at
birth, the `jscpd` duplicate-detector is expected to flag them — this is
recorded and justified (see "What this FR does NOT do"), not an accident. No DM
code is modified, and the DM is *not* later re-pointed at this schema.

## Problem

The DM's `schema.py` has:
- `FunctionKind`: 4 kinds (villainy, reveal, reconciliation, return)
- `AffectKind`: 2 kinds (loss, guilt)
- `Belief.held`: `bool` only
- No `gloss`, `motivation`, `threatens`, `enables`, `roles`, `toward`

The Plot Modeller's vision document specifies 17 kinds, 6 affects, relational
`toward`, typed `held: bool | str`, and the full function fields. The L4 spike
(FR-570) hardcodes `VALID_KINDS` as a set of strings — it needs to read from
the schema enum instead.

## Proposed solution

### 1. Schema modules

```
examples/plot_modeller/schema/
├── __init__.py          # Public API: PlotPlan, Function, Belief, etc.
├── kinds.py             # FunctionKind enum (17 kinds)
├── affects.py           # AffectKind enum (6 kinds), AffectDelta with toward
├── predicates.py        # Fluent, Belief (held: bool | str)
├── functions.py         # Function model (full fields)
└── plan.py              # PlotPlan model (meta, agents, world, beliefs, goals, functions, policy)
```

#### `kinds.py`

```python
from enum import Enum

class FunctionKind(str, Enum):
    villainy = "villainy"
    lack = "lack"
    mediation = "mediation"
    departure = "departure"
    donor_test = "donor_test"
    provision = "provision"
    struggle = "struggle"
    victory = "victory"
    liquidation = "liquidation"
    return_ = "return"
    pursuit = "pursuit"
    rescue = "rescue"
    recognition = "recognition"
    exposure = "exposure"
    punishment = "punishment"
    reconciliation = "reconciliation"
    death = "death"
```

#### `affects.py`

```python
class AffectKind(str, Enum):
    loss = "loss"
    guilt = "guilt"
    betrayal = "betrayal"
    retaliation = "retaliation"
    hidden_blessing = "hidden_blessing"
    hope = "hope"

class AffectDelta(BaseModel):
    op: Literal["open", "close"]
    char: str
    kind: AffectKind
    toward: str | None = None    # optional relational dimension
```

#### `predicates.py`

```python
class Fluent(BaseModel):
    pred: str              # alive, at, holds, rel, faction
    args: list[str]
    value: bool | str = True

class Belief(BaseModel):
    observer: str
    fluent: Fluent
    held: bool | str       # True, False, or typed ("software", "worthy", etc.)
```

#### `functions.py`

```python
class Motivation(BaseModel):
    agent: str
    goal: str

class Function(BaseModel):
    id: str
    kind: FunctionKind
    gloss: str = ""
    subject: str = ""
    roles: dict[str, str] = {}
    chapter: int = 1
    observers: list[str] = []
    motivation: Motivation | None = None
    threatens: Motivation | None = None
    enables: list[str] = []
    pre_world: list[Fluent] = []
    eff_world: list[Fluent] = []
    pre_belief: list[Belief] = []
    eff_belief: list[Belief] = []
    eff_affect: list[AffectDelta] = []
```

#### `plan.py`

```python
class AffectPolicy(BaseModel):
    unclosed_is_error: bool = True
    partial_goal_failure: bool = False

class PlanMeta(BaseModel):
    title: str = ""
    genre: str = ""
    synopsis: str = ""

class PlotPlan(BaseModel):
    meta: PlanMeta = PlanMeta()
    agents: list[str] = []
    initial_world: list[Fluent] = []
    initial_belief: list[Belief] = []
    goals: list[Fluent] = []
    functions: list[Function] = []
    affect_policy: AffectPolicy = AffectPolicy()
```

All fields have defaults — the schema grows additively.

**Strict by config (J:C2).** Every model carries
`model_config = ConfigDict(extra="forbid")`. Pydantic v2 defaults to
`extra="ignore"`, which silently drops unmodeled fields — a ground-truth fixture
with a misspelled or unmodeled key would "parse" while the schema is actually
wrong, making the fixture-parse acceptance test (AC#1) compliance theatre.
`forbid` makes the test bite: an unexpected field is a hard error.

### 2. Validator modules

```
examples/plot_modeller/validators/
├── __init__.py          # validate_plan(plan) → list[Flaw]
├── lifecycle.py         # Monotonic: alive → dead is one-way
├── grounding.py         # Can't reveal what no one was wrong about
└── affects.py           # Affect closure (policy-aware)
```

Extracted from DM's `validate.py` (249 lines). Each validator is a pure
function: takes a `PlotPlan`, returns a list of flaw strings. The top-level
`validate_plan()` composes them all.

### 3. Wire FR-570's validator to the schema

Update `nodes/tools.py` to import `VALID_KINDS` from `schema.kinds` instead of
hardcoding the set:

```python
from schema.kinds import FunctionKind
VALID_KINDS = {k.value for k in FunctionKind}
```

### 4. Parse ground-truth fixtures through the schema

Add a test that loads all 4 (later 5) ground-truth YAML plans into `PlotPlan`
objects. This is the schema's acceptance test — if the plans don't parse, the
schema is wrong.

## Acceptance criteria

1. `PlotPlan.model_validate(yaml.safe_load(plan_file))` succeeds for all 4
   ground-truth fixtures **with `extra="forbid"` set** — i.e. every field in
   every fixture is modeled; an unmodeled or misspelled key fails the test
   (J:C2)
2. `FunctionKind` has exactly 17 members
3. `AffectKind` has exactly 6 members
4. `AffectDelta.toward` is optional (None default)
5. `Belief.held` accepts `True`, `False`, `"software"`, `"worthy"`, **and the
   string `"true"` — which must stay `str`, not coerce to `bool`** (pins the
   `bool | str` union order with a test, J:note)
6. `validate_plan()` catches: lifecycle violation, ungrounded reveal, unclosed
   affect (with policy override)
7. `nodes/tools.py` reads `VALID_KINDS` from the schema, not a hardcoded set
8. All existing DM tests pass unchanged (no DM code is modified)

## What this FR does NOT do

- Does not add `mediation` or `hope` to the ground-truth fixtures (that's FR-572)
- Does not build any pipeline layers (that's FR-573+)
- Does not modify any DM code — the Plot Modeller gets its own schema
- Does not add `causality.py`, `reachability.py`, or `motivation.py` validators
  (those come in Phase 4 when the merge node needs them)
- Does not re-point the DM at this schema — the fork is permanent (J:C1); the
  expected `jscpd` overlap between the two schemas is justified here and, if it
  trips the duplicate gate, suppressed with a one-line reason rather than
  collapsed into a shared module

## Judgement (2026-06-23)

**Verdict: GRANTED with conditions.** The scope is clear, minimal, and the
schema is well-specified. Two conditions must be folded before Enforce, plus
one note.

### C1 — "Extract" here is *copy + grow*, which creates a duplicate (resolve it)

AC#8 forbids modifying DM code, so the DM keeps its 4-kind schema while the
Plot Modeller gets a 17-kind copy. That is duplication, not extraction — and
`jscpd` (Commandment 8) will flag it. Decide explicitly, in this FR, which is
true:

- **(a) True extraction:** the Plot Modeller becomes the home; the DM later
  imports from it. AC#8 then becomes "DM tests pass after the DM is re-pointed"
  — a follow-up FR, but the duplication is temporary and declared.
- **(b) Deliberate fork:** the two schemas diverge permanently (the DM's 4-kind
  set is a different contract). Then record a `jscpd` ignore with a one-line
  justification, and rename the value statement — it is a *fork*, not an
  extraction.

The word "extraction" with "no DM code modified" is internally contradictory.
Pick one. (b) is the cheaper, more honest framing given the DM is "one consumer,
not the home."

### C2 — AC#1 is trivially satisfiable as written (tighten it)

Pydantic v2 defaults to `extra="ignore"`. A ground-truth fixture carrying a
field the schema does not model (say `pre_affect`, or a misspelled key) will
still "parse" — the unmodeled data is silently dropped, and AC#1 passes while
the schema is wrong. The fixture-parse test is the schema's only acceptance
test; it must *bite*. Require **either**:

- `model_config = ConfigDict(extra="forbid")` on the plan models, **or**
- a round-trip equality assertion: `PlotPlan.from_yaml(p.to_yaml())` equals the
  re-loaded raw YAML (no field lost).

Without this, AC#1 is compliance theatre (gate checks presence, not substance).

### Note — `Belief.held: bool | str` coercion is a boundary to test, not assume

Pydantic v2 smart-union on `bool | str` can coerce `"true"`/`"false"` strings or
treat `1`/`0` as bool. AC#5 already names `True`, `False`, `"software"`,
`"worthy"` — good. Add `"true"` (the *string*) to that list and assert it stays
`str`, so the union order is pinned by a test rather than by Pydantic's default.

### Folded conditions

AC#1 → add `extra="forbid"` or round-trip equality. C1 → restate the value
statement as a deliberate fork (option b) **or** add the DM re-point follow-up.
All other ACs are falsifiable and well-formed. Proceed to Enforce: schema +
validators first (RED on the fixture-parse + lifecycle/grounding/affect tests),
then wire `nodes/tools.py` to the enum.
