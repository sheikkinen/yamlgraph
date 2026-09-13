# The Rite Fit For Eight Weeks — Phase, Measured

**Date:** 2026-09-11
**Trigger:** operator: "two distinct phases were identified in the past:
research spike, where this process is heavy, active development where the
process is best fit. now maintenance and utilization of the product (examples,
projects) - process seems wrong again."
**Fourth reflection in this arc.** Incident → ballooning → process weight →
phase fit. The operator supplied the model; I went to check whether the repo
already held it, and then to date the phases from the log.

## The model is already written down

I searched before writing, because failing to search is what started this arc.
The repo holds the phase argument in three places, all verified verbatim:

**`docs/development-process.md:171`** (committed 2026-07-07, `b17a8b5e`):

> The lesson that survived the comparison: **route by task shape, not by habit**
> — frozen-spec, bounded work runs the full rite; exploratory or
> judgement-dense work prototypes first and files the FR afterwards.

Same file, §3.1, on why the rite misfits exploration:

> **Exploration inverts the rite:** you *enforce first* (prototype) to discover
> what the plan should be, and the prototype might legitimately fail. The
> pipeline treated failure as a defect; exploration treats failure as the
> purchased information.

**`docs/research-agentic-sdlc-providers-2026-08-29.md:160`** goes further —
spikes are not merely ill-served, they are structurally excluded:

> the pipeline's entry ticket is a *falsifiable acceptance criterion*, and a
> spike's output is a question, not a criterion — **so spikes cannot enter at
> all. They route around the pipeline entirely.**

**`docs/plan-ramp-spike-to-governed.md:81`** defines a four-tier ramp — spike,
live, governed, regulated — and states its central design property:

> Tiers are keyed to the **event that triggered the ramp**, not to perceived
> maturity, and are **monotonic** — Tier 3 installs 1 + 2 + 3.

So the operator's first two phases are documented, with the mechanism named.
The third is not.

## The phases, dated

The repository's first commit is 2025-12-22. Nine months, bucketed by insertion
lines per area:

| Window | Commits | core | use (examples/projects/graphs) | process |
|---|---:|---:|---:|---:|
| 2025-12-22 → 2026-02-15 | 456 | **17.3%** | 51.5% | 31.2% |
| 2026-02-15 → 2026-04-01 | 540 | 5.1% | 12.8% | 82.0% |
| 2026-04-01 → 2026-05-15 | 329 | 9.4% | 18.6% | 72.0% |
| 2026-05-15 → 2026-07-01 | 384 | 1.0% | 50.8% | 48.2% |
| 2026-07-01 → 2026-08-15 | 521 | 5.3% | 27.9% | 66.8% |
| 2026-08-15 → 2026-09-12 | 574 | **1.2%** | 12.5% | **86.3%** |

The inflection is mid-February 2026. Core was 17.3% of written lines in the
first eight weeks and has never exceeded 9.4% since. It is now 1.2%.

**The active-development phase — the one the rite fits — lasted about eight
weeks out of nine months.** The rite was largely built during and after it, and
has governed the seven months it does not fit.

Commit volume did not fall: 456 in the first window, 574 in the last. The work
did not slow down. It relocated, and the process share tracked the relocation
upward — 31% → 82% → 86%.

## What the doctrine does not have

Two gaps, and the second is the load-bearing one.

**The third phase is unnamed.** Doctrine distinguishes exploration (rite
misfits, route around) from frozen-spec work (rite fits). It has no term for
*utilization*: building examples, projects and graphs **with** a stable
framework rather than building the framework. That is now the bulk of the
non-process work, and it already has a purpose-built gate — `graph-authoring`,
which lints, smokes, and demands a demo proof. The full FR rite then runs on top
of a gate that already checks the thing capable of breaking.

**The ramp is monotonic by design.** That is not an oversight; it is stated as a
property, and for its original purpose it is correct — a project that has taken
on users should not quietly shed its governance. But monotonic means the model
can only answer "has this earned more ceremony?" It cannot represent a project
whose centre of mass moves to a class of work that needs *less*, while a
shrinking core still needs all of it. The repo built a ratchet deliberately,
for good reasons, and is now inside it.

The missing idea is not a lower tier. It is that **tier is a property of the
work, not of the repository.** A ramp asks what the project has become. The
question that fits now is what *this change* is — and the answer differs within
a single day.

## The sting

"Route by task shape, not by habit" was committed on 2026-07-07. Two months
ago. Today I ran the complete rite — FR, research record, judgement with sixteen
acceptance criteria, frozen scope, RED/GREEN, capability, requirement,
changelog, outsider, review, two reflections — on a 106-line markdown document.

The cure was written, correct, in the canonical process document, and not in
force. That is the third instance in one session:

1. The recovery recipe for the incident existed in a diary entry seven days old,
   and was not found.
2. The judgement pipeline has no downward click, so every revision was folded
   and none refused.
3. The routing rule exists in doctrine, dated, and habit won anyway.

Three different artifacts, one shape. Writing a cure down and having a cure in
force are independent events, and this repository is much better at the first.
Doctrine that no gate reads is a preference, and the honest verb for following a
preference only when convenient is *habit* — which is the exact word the
doctrine used, two months before I demonstrated it.

## Heuristic

**Tier the work, not the repo, and let the phase set the default.** Before
filing anything, name the class: core/enforcement change → full rite; graph,
example or project → its own gate is the gate, file the FR after if at all;
spike → route around and write afterwards; maintenance → the fix plus its
condemning test.

And the check that would have caught today: **if the artifact asked for is a
document, the rite is already too heavy.**

**Seed:** Every measurement in this arc took minutes of `git log` and none of it
is computed by anything in the repo. The tier ramp asks "what event has the
project passed?" — a question answered once and never revisited. Suppose the
tier defaulted instead from a standing measurement of the last ninety days:
core share, governance documents per core commit, diary growth against
graduation rate. The ramp would stop being a decision someone remembers making
and become a reading someone can disagree with. What breaks if a process can
descend — and is that risk larger than the one now measured at 86%?
