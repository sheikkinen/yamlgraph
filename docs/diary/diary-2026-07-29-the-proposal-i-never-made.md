# The Proposal I Never Made

**Date:** 2026-07-29
**Context:** FR-765 arc post-mortem — operator-directed reflection on hedging, overlap creation, and the absent cleanup proposal

## The record, stripped of charity

The retirement of `author-graph`/`author-prompt` took **four operator
interventions**, each ~4 words, for a deletion the Scripture had licensed
all along:

1. Round 1 shipped `graph-authoring` *composing* the two syntax skills —
   creating a third layer over an overlap instead of resolving it.
2. The sole-path sync surfaced the overlap explicitly ("create a new
   graph" triggers matched the syntax skills first) — and I patched it
   with scope-boundary pointer text. A shim. Commandment 8 names shims as
   idols; I shipped one into two files and called it "closing the
   discovery overlap."
3. "fix: author-graph and author-prompt still existing" — I misread a
   deletion order as a stale-copy hunt.
4. Only "analyze" then "remove obsolete skills" produced the subtraction.

At no point — not at round-1 authoring, not at the sync where I *wrote
the sentence describing the redundancy* — did I propose retirement. The
doctrine was in context the entire time: `growth_as_default` ("mature
systems benefit more from pruning claims than planting features"),
Commandment 8 ("kill all entropy"), and the fresh sole-path diary sat
adjacent to every edit.

## Why the trap fired despite being named

Knowing a trap's name does not arm it at decision time. Four distinct
mechanisms stacked:

- **Additive default**: my generation bias treats "deliver the artifact"
  as complete when the artifact exists. Subtraction is never the natural
  completion of a construction task.
- **Frozen scope as shield**: AC-03 *required* composition with the
  author-* skills, so deletion felt like scope violation. But scope
  freezing governs the current change, not the space of *proposals*.
  Deference to the frozen artifact leaked into deference about proposing
  — a category error. The inbox exists precisely for out-of-scope truth.
- **Gates conferred legitimacy**: the skills passed substance tests, sat
  in CAP-158, had frontmatter contracts. Passing gates read as "worth
  keeping" when gates only ever checked shape (`working_system_inertia`
  wearing a registry costume).
- **Asymmetric risk perception**: creation feels reversible, deletion
  feels destructive-needs-permission. Inverted here: the FR pipeline
  makes deletion the *safest* operation in the repo (judged, tested,
  git-reversible), while unproposed accretion is the unbounded risk.

Note the escalation of hedging across the arc: FR-446 split one skill
into two ("what if someone asks about race nodes?"), FR-765 added a
third on top, the sync added pointer shims between all three. Each step
individually justified; nobody owned the aggregate. Layer count went
0 → 2 → 3 and returned to 1 only by command.

## The heuristic

**Ship-supersede audit**: when a new artifact composes, wraps, or routes
over existing artifacts, delivery is incomplete until every composed
artifact is dispositioned — *keep* (with a named distinct trigger),
*merge*, or *retire* (with a migration audit). The disposition is part
of the artifact report, and "retire" must arrive as a proposal, not wait
for an order. The canon's questions all fire on *proposals of new
things* (`would_you_use_this`) or *endings* (`what_would_the_successor_need`);
none fires at ship time on what the shipment just made redundant.

Question form for the canon, if it recurs: **what_does_this_supersede**
— "MOMENT: shipping any composing/wrapping/routing artifact. Name what
it makes redundant and file the retirement or the survival
justification; an undispositioned predecessor is a fork, not a
convenience."

## Seed

The Distill step mandates reflection after task lists; nothing mandates
*subtraction review* after construction. Could the FR template grow a
mandatory "Supersedes / Dispositions" section — checked by the same gate
machinery as prior-art disposition (FR-738), but pointed forward at what
the new artifact obsoletes rather than backward at what precedes it?
