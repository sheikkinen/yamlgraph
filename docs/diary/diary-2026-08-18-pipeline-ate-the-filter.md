# Diary: The Pipeline Ate the Filter

**Date:** 2026-08-18
**Context:** Operator-raised issue on velocity: ideas convert to features
extremely fast and with little mental effort — the LLM does the planning,
judging, enforcing. End state: mentally overwhelming. Too many features,
examples, possibilities; many unfinished, or finished but not monetized.
This entry reflects on why, and what the honest cures are.

## The diagnosis: effort was load-bearing three ways

In pre-LLM development, implementation effort was not just a cost. It was
simultaneously three mechanisms:

1. **A filter.** Only ideas worth weeks of a human's work got built. Weak
   ideas died of expense before they died of judgement.
2. **A memory encoder.** Building something by hand writes it into the
   builder's head. The struggle *was* the learning. You knew your system
   because you had paid for every piece of it.
3. **A pacing governor.** Human throughput capped the rate of new
   capability at roughly the rate a human could absorb new capability.

The pipeline was aimed at the cost and killed all three. Plan-judge-enforce
removed the expense — intended. But nothing reinstalled the filter (the
judge approves ~97%, evaluating each FR *in isolation* on internal merit,
never against the portfolio), nothing reinstalled the memory (features
merge without ever passing through the operator's head), and nothing
reinstalled the governor (240 commits/month, ~8/day, one human).

The overwhelm is not "too many features." It is **capability surface
exceeding the operator's mental model of it** — a system that knows more
about itself than its owner does. The Scripture, diaries, and knowledge
graph are externalized memory *for agents*. There is no equivalent
artifact sized for a human head. "Build for agents first" succeeded so
completely that the human became the unserved consumer.

## The judge judges the tree, never the forest

Every gate in the repo evaluates an FR against its own acceptance
criteria. No gate evaluates the *marginal* FR against what already exists:
729 FRs, each locally justified, globally uncountable. `growth_as_default`
is named in the Scripture as a per-commit trap; this is the same trap at
system scale, with a mechanism worth naming separately:
**frictionless_conversion** — when conversion cost approaches zero, the
decision to convert must become *more* deliberate, not less, because
nothing downstream will stop it. The old world forced deliberation through
effort; the new world must force it through explicit budget, or get none.

## Merge is the midpoint wearing a finish-line costume

"Finished but not monetized" locates the second defect precisely: every
gate in the repo sits *before* merge. The lifecycle ends at "enforced."
There is no "harvested" status, no post-merge stage, no gate that asks
whether anything external — a user, a euro, a sibling project — ever
touched the feature. The first-reader gate (yesterday's seed) is the
special case; the general law: **value capture is the ultimate first
reader**, and the pipeline currently optimizes idea→merged-PR while the
actual objective is idea→value-captured. The unmeasured half of the
funnel is where all 729 FRs currently sit.

## The role shifted; the tooling didn't

At this velocity the operator's real role is no longer builder — it is
portfolio manager. But the tooling is still builder tooling: diffs,
examples, FR files. A portfolio manager does not read positions line by
line; he reads a dashboard sized to human working memory and makes
kill/keep/double-down decisions. The system presents *features* when it
should present *decisions*. The overwhelm is a category error in the
interface, not an excess in the inventory.

## Cures, in order of subtractiveness

The trap in responding to feature-surplus is proposing features. These
are ordered to resist that:

1. **Throttle the inbox (WIP limit on conversion).** The chaplain consumes
   whatever appears. A hard cap — N proposals in flight, one-in requires
   one-out or one-retired — reinstalls the governor mechanically. Cheapest
   cure; pure configuration.
2. **Portfolio question in the judge rubric.** Beyond "is this FR sound":
   *what existing capability does this displace, and what is its claim on
   a fixed attention budget?* An FR that cannot name its displacement is
   `growth_as_default` with a verdict stamp.
3. **One-in-one-out for examples.** The examples directory is where the
   surplus is most visible. New demo merges only alongside a retirement
   proposal for the weakest existing one. The operator already expects
   subtraction proposals unprompted; make the expectation mechanical.
4. **An operator-sized world view.** Not another report — a view bounded
   by human working memory: seven arcs, not seven hundred FRs, each with
   one kill/keep/double-down decision attached. FR-744's "world now"
   pointed here; the overwhelm is evidence the altitude is still wrong.
   The consumer is named (the operator), the moment is named (session
   start) — it passes the first-consumer test.
5. **A "harvested" lifecycle status.** FRs gain a post-merge state; the
   inquisitor reports the enforced-but-never-harvested count the way it
   reports coverage. Making the unmonetized surplus *visible as a number*
   is the precondition for any monetization decision.

## Heuristic

**Effort was cost, filter, and memory in one mechanism. Automation was
aimed at the cost and killed all three; the filter and the memory must be
reinstalled explicitly — as budgets and digests — or velocity converts
directly into overwhelm.** A pipeline that makes building free makes
*choosing* the entire job.

## Seed

**Seed:** What is the operator's actual attention budget, in arcs — and
can the whole system be throttled to it? If the chaplain inbox had a hard
WIP limit derived from that budget, the binding constraint would move
from "what can be built" to "what deserves a slot" — the judge's question
would finally become the investor's question. Would the first casualty
be a feature, or an example, or the reflection pipeline that produced
this entry?
