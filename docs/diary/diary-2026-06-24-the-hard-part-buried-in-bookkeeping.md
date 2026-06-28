# The hard part, buried in bookkeeping — FR-585 and the pipeline-wide monolith

*2026-06-24 — reflecting on the L5 decomposition (FR-585) and auditing the whole
plot_modeller prompt suite for the same shape*

## What happened

FR-584 killed the prompt-only fixes for L5's precision wound. The diary that
followed ("the flood and the miss are one gesture") diagnosed the cause as
*attention budget*: the single `assign_pre_eff` call carries ~12 jobs, and the one
that matters — deciding which fluents are salient — starves among the eleven
bookkeeping jobs. FR-585 acts on that: give salience its own call, demote the
mechanical rules to code.

Then the user asked the sharper question: **is L5 special, or is this everywhere?**
So I read all seven prompts in the pipeline and graded each on a single axis —
*does it fuse a discrimination judgement with bookkeeping?*

## The pattern

| prompt | per-unit jobs | verdict |
|---|---|---|
| `extract_glosses` | decompose synopsis → beat (id/gloss/chapter) | **clean** — one judgement |
| `classify_kinds` | one kind + subject per beat (17-kind alphabet) | **clean** — one judgement |
| `extract_goals` | goal predicates (5-pred typing) + goal-vs-incidental salience | at risk — salience tension |
| `extract_agents` | agents **+** initial_world (5-pred typing) **+** initial_belief | monolith — 3 fused sections |
| `assign_causality` | `enables` (forward-only causal graph) **+** motivation **+** threatens | monolith — 3 fused tasks |
| `assign_affects` | 6-kind vocab + op + char + `toward` + **placement salience** + **arc-closure planning** | monolith — L5's exact wound |
| `assign_pre_eff` | the 12-job L5 call | monolith — FR-585 target |

Two findings landed harder than I expected.

**1. The clean prompts are the ones that make exactly ONE judgement per unit.**
`extract_glosses` and `classify_kinds` are not clean because they are short — they
are clean because each produces a single decision (one beat, one kind). Their
"common errors" sections are disambiguation *for that one decision*, not extra
jobs. Length is not the signal; **number of distinct judgements per call is.**

**2. `assign_affects` literally names its own buried treasure.** Mid-prompt it
says: *"PLACEMENT — this is the hard part."* The author already knew where the
model's attention should go. And then the format buries that hard part beneath a
closed vocabulary, a char-membership rule, a relational-arg rule, a *global*
arc-closure planning constraint (every `open` must `close` later, same kind, same
char), and a YAML shape. The one sentence that says "this is the hard part" is
surrounded by five sentences that compete for the same attention. The prompt
diagnoses itself.

## The trap

I had filed the L5 problem as an *L5 problem* — a quirk of formalizing world-state.
It is not. It is a **prompt-construction default**: when an output needs several
typed fields, the path of least resistance is to ask for all of them in one call,
because the schema is one object. But schema cohesion is not attention cohesion. A
single YAML item with `enables` + `motivation` + `threatens` *looks* like one task
because it serializes as one object — yet it fuses causal-graph prediction with two
attribution judgements, three different cognitive acts wearing one bracket.

The monolith hides inside the data model. "It's all per-beat, so it's one prompt"
is the same error as "it's all one function, so it's one responsibility."

## The heuristic

**Count the distinct judgements a prompt asks for, not its fields or its lines. If
a prompt fuses a *discrimination* (salience: which of these matter? / which class
is this?) with *bookkeeping* (typing, naming, serialization, or a global
cross-unit constraint), the discrimination will starve — and no wording fixes a
starved judgement, only a call of its own.** The tell is sharpest when the prompt
itself flags a step as "the hard part" while embedding it among mechanical rules:
that sentence is a confession that the format is fighting the author.

Corollary: a global constraint (arc-closure in affects, forward-only in causality,
cross-beat token reuse in L5) is the most expensive passenger of all, because it
forces the model to hold the whole sequence in mind *while* doing local work. Those
belong in a deterministic post-pass or a dedicated consolidation call, never as a
rider on a per-unit generation prompt.

If FR-585's salience-gate decode proves out on L5, it is not an L5 fix — it is a
**template** the other three monoliths (`assign_affects`, `assign_causality`,
`extract_agents`) can inherit: split the discrimination from the bookkeeping, push
the global constraint to code.

## Seed

Could the pipeline grow a cheap static linter for its own prompts — flag any prompt
whose output schema has ≥ 3 independent fields *or* whose body contains a
global-constraint phrase ("must … later", "every … should … ", "exactly one … and
one …") as a decomposition candidate — so the monolith is caught at authoring time,
the way `radon` catches a function doing too much, instead of after a precision
wound and two killed FRs?
