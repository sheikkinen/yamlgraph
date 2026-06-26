# I measured the output for days before I read it

**Date:** 2026-06-26
**FR:** FR-596 / FR-597 lineage — L7 affect, diagnosis phase
**Lineage:** FR-578 (affect_recall gate) → FR-596 (per-agent throughline) → FR-597
(regenerability ruler) → *finally `cat`-ing the prose haiku actually produced*

## What happened

`affect_recall = 0.09` sat on the L7 gate. Over multiple sessions I built an
escalating tower of *measurement* on top of that number:

- a "numbers lie" manual inspection (FR-596) that produced an under-determination
  hypothesis,
- a whole regenerability ruler (FR-597, `l7_measure` graph, an entire FR with
  Judgement, four corrections, tests, changelog, diary) to confirm it,
- corpus-pooled probes, sub-axis decompositions (detection vs kind vs toward),
  apples-to-apples recall filters, cast-flood precision arguments.

Every one of those touched the *scores*. Not one of them opened the file the pipeline
actually wrote. The intermediate artifact — `results/l7/throughlines/<genre>/<agent>.md`,
the literal prose haiku emits as its "emotional analysis" — sat on disk, unread, while
I theorized about why its downstream numbers were low.

When I finally `cat`-ed it, the defect was obvious in **ten seconds**: haiku returns a
**352-word literary character study**. "The case she has built collapses in ash." "He
is unmade." "A seed of retaliation." The prompt asks for prose narration of a single
character's arc, and the model dutifully writes a *novel* — and the novelist's
instincts (complete the arc, supply interiority, reach for evocative diction, thread
causality across beats) are precisely what invent the affect (`guilt → Pell` that
isn't there), blur the kinds (`hidden_blessing` for GT's `hope`), and suppress the one
relation that doesn't fit a heroic arc (Marren's own `betrayal → Hagen`).

The user saw it in one read: *"haiku returns a novel as an analysis of the emotions."*
I had been holding the answer key — the raw output — the entire time and grading the
exam by its summary statistics.

## The trap

**`metric_archaeology_before_reading_output`** — when a pipeline's *score* is wrong, the
reflex is to instrument, decompose, and re-measure the score, building rulers to explain
the number. But the number is a lossy projection of an artifact that is sitting right
there in plain text. Reading the artifact is the cheapest, highest-bandwidth diagnostic
available, and I deferred it behind two FRs of metric tooling. The more sophisticated my
measurement got, the further I drifted from the one-line `cat` that would have ended the
investigation on day one.

This is a sibling of `audit_as_ritual` (3+ audits without a fix = ritual) and of the
changelog addendum's `changelog_first_diagnostic`. The shared root: **LLM agents reach
for analysis (generate, measure, theorize) before observation (read the actual thing).**
A ruler is a comfortable thing to build — it is more code, more cleverness, more visible
effort. Opening a `.md` and reading 350 words of prose feels too cheap to be the answer.
It was the answer.

It is doubly damning here because the pipeline *produces LLM prose* as an intermediate.
The output is not a binary blob or a 10MB tensor — it is English. There was never an
excuse. The artifact was literally human-readable and I read its statistics instead.

## The cure

**Read the rawest artifact the pipeline emits before you measure it. The first
diagnostic for a bad score is `cat`, not a new metric.** When a stage's output is text,
reading three samples end-to-end is mandatory and comes *first* — before the score is
even computed, let alone decomposed. Metrics tell you *that* something is wrong; only the
artifact tells you *what*. For LLM pipelines the artifact is usually plain language —
there is no cheaper or higher-fidelity probe in existence, and skipping it to build a
ruler is the agent's continuation-bias (prefer generating over observing) in its most
expensive form.

Concretely: every spike/eval harness over an LLM stage must dump N raw samples to disk
*and* the operator must read them before reading the aggregate. The FR-596 spike already
wrote the prose to `results/l7/throughlines/` — the instrumentation was correct. The
failure was purely behavioral: I did not open what it wrote.

**Seed:** Should an eval harness over an LLM stage *refuse to print the aggregate score
until the operator has acknowledged reading K raw samples* — a forced-observation gate,
the way TDD forces RED before GREEN? Can "read the output" be made mechanical
(harness prints 3 random raw samples first, score withheld behind a `--i-have-read-the-samples`
flag) rather than left to a discipline I demonstrably lack under the pull of building
the next ruler?
