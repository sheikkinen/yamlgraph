# The Process Is the Product Now — A Measurement

**Date:** 2026-09-11
**Trigger:** operator: "development process itself would need streamlining. e.g.
the dirty main feature was a fix for the process. current process is an overkill
for the graphs that are the usual contents. and the yamlgraph core seldom moves
anymore. investigate."
**Third FR-1047 reflection.** The first was about the incident, the second about
the ballooning. This one is about why the ballooning was not an accident.

## What the log says

Ninety days, `git log` classified by path. No sampling, no estimate.

**Where the commits go** (1336 commits; buckets overlap):

| Bucket | Commits | Share |
|---|---:|---:|
| process (`.github/`, `scripts/`, `feature-requests/`, `docs/`, `capabilities/`, `reference/`) | 1176 | 88% |
| graphs + examples | 337 | 25% |
| **`yamlgraph/` core** | **86** | **6.4%** |

**Where the lines go** (insertions, 90 days):

| Bucket | Lines | Share |
|---|---:|---:|
| process | 304,651 | 60% |
| graphs + examples | 122,781 | 24% |
| tests | 60,262 | 12% |
| **core** | **8,377** | **1.7%** |

No single generated file explains it. The largest single contributor is
`reference/fr-knowledge-graph.yaml` at 17k lines — 5% of the process bucket.
The other 95% is thousands of hand-written governance documents.

**The governance output itself** (90 days, deduplicated):

- 535 new FR plans — **5.9 per day**
- 220 new judgements
- 584 new diary entries — **6.5 per day**
- 1,339 governance documents total

Against 86 commits that touched the core. That is **15.6 governance documents
per core-touching commit.**

**The corpus is accelerating, not settling:**

| Corpus | Total now | Added in last 90d | Quarter-over-quarter growth |
|---|---:|---:|---:|
| FR plans | 917 | 535 | +140% |
| Diary entries | 1408 | 584 | +71% |

Fifty-eight percent of every FR that has ever existed in this repository was
written in the last quarter.

## Where the operator was right, and where I'd correct him

**Right:** the process is calibrated for a repository whose main activity is
core framework change. That repository no longer exists. Core is 1.7% of the
written output and 6.4% of commits, while carrying the same full rite — FR,
research record, judgement, frozen scope, RED/GREEN, capability, requirement,
changelog, diary, outsider, review — as everything else.

**Right:** graphs and examples are the usual contents, at 4× the commit volume
of core. They already have a purpose-built gate in `graph-authoring` — lint,
smoke, demo proof, honest validation record. That gate is mechanical, fast, and
checks the thing that can actually break. Then the full FR rite is applied *on
top of it*.

**One correction.** "Core seldom moves" is not quite what the log shows. 107 of
137 core files were touched in the last 90 days — 78% of the module. What
collapsed is not the frequency but the *depth*: 8,377 insertions across a
25,189-line codebase, spread wide and thin. Core is in maintenance, not
stasis. The distinction matters for what follows: maintenance changes are
exactly the ones the heavy rite serves worst, because the FR takes longer to
write than the fix.

## The part with the sting

FR-1047 was a fix for the process. It was governed by the process. It cost 1449
lines to ship a 106-line document. And the defect it fixed — a cure sitting on
disk, correct and unreachable — is *caused by the process's own output volume*.

The recovery recipe existed in a diary entry written seven days before the
incident. I did not find it. There are 1408 diary entries. At 6.5 new ones per
day, no agent and no human finds the right one by looking; they find it only if
something routes them to it. I "fixed" that with a single line in
`copilot-instructions.md` and called it the cure.

It is not the cure. It is one route, hand-laid, over one of 1408 documents,
added to an instruction file that is itself part of the corpus that must be
read. The Distill step produces knowledge at 6.5 documents/day and graduates it
to the Scripture at a rate of a few entries per quarter. Everything in between
is written, committed, and never read again. The knowledge graph in
`copilot-instructions.md` is the honest part of the diary corpus; it is perhaps
200 lines distilled from 1408 documents — a 0.5% survival rate, and the other
99.5% is still being written every day at full cost.

The rite's Distill step was designed to prevent knowledge loss. At this volume
it *causes* it: the signal is there, and the noise is also there, and they are
the same corpus.

And this entry is document 1409.

## The mechanism

The rite has no term for artifact class. It asks "is this change governed by an
FR?" and never "what kind of thing is this?" So a 106-line skill document, a
YAML graph, a one-line route, and a change to the executor all draw the same
apparatus. Uniformity looked like rigour. What it actually does is price every
change at the cost of the most dangerous change, which makes the cheap and
frequent changes — graphs, docs, maintenance — the ones that subsidise the
ceremony.

Second-order: because the process is expensive, improving the process is
valuable, so process-improvement FRs are worth writing — and there were 122 of
them in 90 days, each one governed by the process it improves, each one
generating its own FR, judgement, tests, and diary entry. The system's most
profitable activity has become its own maintenance. That is not a conspiracy;
it is what happens when the cost of a change is independent of its size and the
process is the largest surface available to change.

## Heuristic

**Price the rite by artifact class, and re-derive the classes from the log, not
from memory.** The weight a change deserves is a function of blast radius, not
of the fact that it is a change. A graph that lints, smokes and produces a demo
proof has been checked by the thing that can catch its defects; adding a judge
and a reviewer on top adds cost and no detection. A change to the executor
deserves all of it.

Corollary, and the one I would act on first: **the Distill step needs a budget.**
A step that emits 6.5 documents a day into a corpus nobody can search is not
preserving knowledge. Either graduation becomes mechanical, or distillation
becomes rarer, or the corpus gets an index that is itself maintained — and the
third option is another process.

**Seed:** The numbers above took four `git log` invocations and about a minute.
Nothing in the rite computes them, and no gate reads them, so the process has
never once been confronted with its own cost. What would it mean for the
repository to carry a standing measurement — commits by artifact class,
governance documents per core commit, diary growth versus graduation rate — and
for *that* number to be the trigger for re-tiering? A process that cannot see
its own weight will keep choosing uniformity, because uniformity is the only
policy that requires no measurement.
