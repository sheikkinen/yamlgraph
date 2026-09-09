# Agent-file triage: invariant-store, state-log, description

**Arc.** A question about GitHub's public repo count turned into six
exchanges of census mechanics — size distributions across 778k `CLAUDE.md`
files, star pivots, a Mercury-vs-Claude cost model priced to the dollar.
Then the operator named the intent: *analyse agent files and filter out the
best practices*. None of the measurement served it. Ten files read by hand
in under an hour produced a taxonomy the census could not have reached,
because the census was built to describe the distribution and the answer
lives in the tail.

## What the raw record says

Ten files, read end to end, selected first by stars and then by commit count
on the `CLAUDE.md` path itself.

- **`eneskirca/nodeterm`** (306 KB, 1.8k★, 3,445 lines, *four* code fences)
  states the criterion outright — a guard exists because "nobody reading one
  file can see this". Every rule carries its incident with numbers: 28 files
  had the bare-`fs.rename` bug across three spellings; the only signal in a
  6,000-test suite was one store's overlap test, red on Windows for that
  store's whole life. Windows rename fails when the destination is
  momentarily open, so the culprits are the antivirus scanner, the search
  indexer and the file-sync client — meaning data loss is *more* frequent on
  better-protected machines. The helper's negative space is specified (no
  infinite retry, no `ENOENT`/`ENOSPC` retry, no platform branch, because a
  platform branch means the behaviour under test on a Mac is not the
  behaviour shipped). Each invariant names its guard test, and the tmux
  section closes with **"What this does not claim"** — the hazard was never
  traced to a test; two identical runs finished clean.
- **`matiaszanolli/sega-vr-disasm`** (69 commits) records hardware
  invariants that cost crashes: read-during-write undefined, not just
  write-write; SH2 writes buffered, dummy-read to force sync; COMM7 is the
  slave doorbell and broadcasting to it is a proven crash, bug ID cited;
  cache-through address always. Plus a two-strike rule — if a second attempt
  fails for related reasons, stop coding and read.
- **`JetBrains/youtrackdb`** keeps the loaded file small and points at
  `.claude/docs/architecture.md` **with a load condition** — only when the
  change touches storage / Gremlin / parser / generated code.
- **`steveyegge/vc`** opens with how to *find work* (`bd ready`), and its
  review protocol specifies when to **skip** as carefully as when to fire.
- **`ayutaz/piper-plus`** (60 commits, top of the ranking) is a research lab
  notebook: absolute checkpoint paths on one machine, epoch numbers, private
  HF links, dated status blocks. It does flag its own rot — an archive
  section warns that the working branch is elsewhere.
- **`dbrattli/OSlash`** (1 commit, 756★) explains that monads chain
  computations with context and immutability means data does not mutate.
  Every word derivable from the code.

Three unrelated projects — a Sega 32X disassembly, an Electron terminal
canvas, and this repo — independently arrived at the same practices: a
two-strike rule, a distill-to-index protocol, an auditor spawned separately
from the worker, named banned anti-patterns, research-before-implement.
Nobody copied anyone. The convergence is the strongest evidence in the
session that these are forced by the problem, not stylistic.

## The scheme

Every agent instruction file sorts into three classes, and the class
determines whether its bytes earn their context.

- **Invariant-store.** Facts that cost a failure to learn and cannot be
  derived from any single file: prohibitions, named failure modes, negative
  space, working-directory traps, "do not remove" guards. Compounding value.
  Marked by incident provenance (issue IDs, dates, "proven crash",
  "measured, not inferred") and by references to the test that enforces the
  rule.
- **State-log.** Perishable facts: machine-specific paths, checkpoint
  filenames, current epoch, "currently training", branch status. Negative
  value once stale, and stale is the default, because the file is loaded
  into every session while the fact was true for a week.
- **Description.** Architecture summaries, annotated directory trees,
  framework explanations. Derivable by reading the code. Neutral at best —
  it is the `/init` skeleton, and it is most of the corpus by mass.

Value is not proportional to size, stars, or recency. It is proportional to
the invariant-store fraction.

## The trap

**`churn_reads_as_learning`.** Revision count on a knowledge artefact
measures *maintenance*, and maintenance splits two ways that look identical
from outside: invariant accumulation (each commit adds a rule learned from a
failure) and state logging (each commit updates a fact that expired). Only
the first compounds; the second actively costs context. Ranking by commits
put a lab notebook above a hardware-invariant store.

This is `inventory_by_visibility` one level up. That trap says rank by
incidents, not mass. The correction here is that **commit count is a proxy
for incidents, and the proxy was never validated** — I proposed it, ranked
on it, and only found the false-positive mode by reading the top-ranked file.
A proxy adopted without reading its extremes is a shape gate wearing
substance clothing (`gate_checks_shape_not_substance`).

The companion failure is method, and this repo's doctrine names it exactly:
`read_raw_output_first`. Aggregates over 778k files were computed without
opening one. The census would have reported the median file at 9 KB and
mostly `/init` boilerplate — true, and useless, because the practices live
in the outliers every aggregate treats as noise. **For extracting practice,
the distribution is the wrong object; the tail is the object.**

## Heuristic

Triage an agent file by its invariant-store fraction, not its size. Two
questions do it: *could an agent derive this by reading the code?* (if yes,
description) and *will this be false in a month?* (if yes, state-log). What
survives both is the only part paying for its tokens.

Then three practices follow, each observed and each transferable:

1. **Progressive disclosure.** Keep the always-loaded file small; point at
   deep documents with an explicit load condition naming the areas that
   trigger the fetch. Only youtrackdb did this; it is the answer to a file
   that grows past its context budget.
2. **Pair every invariant with its enforcing test, by name.** An invariant
   with no guard is one refactor from silent violation — this repo's own
   `detection_without_enforcement`, applied to doctrine rather than to CI.
3. **Bound the claim.** A "what this does not claim" paragraph separates
   hazard from proven cause. Doctrine here asserts; nodeterm hedges, and the
   hedge is what makes the assertion trustworthy.

Applied to this repo: `CLAUDE.md` plus its `@`-imported
`copilot-instructions.md` load 12,354 tokens into every session, top 3.5% of
the public corpus by size. Content is almost purely invariant-store, which is
the right class — but there is no progressive disclosure, most traps do not
name an enforcing test, and no entry bounds its own confidence.

**Seed:** the three classes are mechanically separable — machine paths,
version-stamped filenames and dated status blocks mark a state-log;
prohibitions, named failure modes and guard-test references mark an
invariant-store. That is a cheap typed map over a frozen corpus, which is
the `corpus_census` graph with two new adapters. Does the same triage run
usefully against *our own* doctrine — scoring each trap and cure for whether
it names an incident, names a guard, and bounds its claim — and would the
resulting three columns be the honest retirement list that
`growth_as_default` keeps asking for?
