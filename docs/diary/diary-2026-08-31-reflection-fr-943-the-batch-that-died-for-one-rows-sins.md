# The Batch That Died for One Row's Sins

**Date:** 2026-08-31
**Context:** FR-943 — census row-level failure containment; the same-day
sequel to FR-940.

## What happened

Four 200-item census batches died on one malformed finding each — after
every LLM call had completed and been paid for (~800 wasted calls). The
FR-940 arc had just taught the ledger to distrust the model's *label*;
this arc taught it to distrust the model's *envelope*. Rev 1 was
REJECTED (research gate + five precision revisions); rev 2 with a
committed research record and the four incidents as a replay fixture
came back APPROVED WITH REVISIONS, and enforcement was RED→GREEN in one
sitting.

## Traps encountered

- **fail_closed_scope_error** (candidate name): FR-892's fail-closed
  contract was correct in *direction* but wrong in *scope* — it applied
  batch-granularity abort to row-granularity failures. Fail-closed is
  not one decision; it is a decision PER BLAST RADIUS. The interesting
  design question is never "fail closed or open?" but "closed at what
  granularity?". The judge sharpened this into ownership taxonomy:
  model-owned locations contain, reducer-owned locations abort.
- **the test helper committed the crime under test**: my
  `_validation_error` fixture omitted `disagreement` (reducer-owned,
  required) — so a test asserting "confidence-rooted errors are
  model-owned" actually produced a MIXED error and failed. The
  classification boundary caught its own witness's malformed envelope.
  Boundary code should be tested with fixtures built by the same
  constructor discipline the boundary enforces.
- **line-cap as design pressure**: AC-16's 450-line cap on `tools.py`
  forced three rounds of compaction ending at exactly 450. The cap did
  its job — `_dispose_finding` (one finding → one disposition) is a
  better seam than the inline loop it replaced — but landing AT the cap
  means the next tools.py change must split the module first.
- **boolean index hole found by spec, not by incident**: the judge's
  `type(index) is int` freeze exposed that today's `isinstance` check
  accepts `True` as index 1. No incident ever witnessed it; the frozen
  contract killed it anyway. Judgement precision finds bugs cheaper
  than production does (spec_kill, again).

## Heuristics

- When a judge rejects for "research missing," the fastest compliant
  path is often extraction, not invention: the six solution classes
  already existed implicitly in the alternatives table and prior-art
  lines; the research record made the disagreement and dispositions
  explicit. Cost: ~20 minutes. The gate's value was forcing S-2's
  preserved disagreement (framework-level containment awaits a second
  consumer) into a citable artifact.
- Guard quirk, third strike: the pytest-pipe guard matches
  `SKIP=pytest ... | tail` as "pytest piped to tail" even when nothing
  pytest-shaped is piped. Route hook output to a log file and read the
  log; never decorate a commit command with head/tail.

## Seed

**Seed:** The census reducer now has three normalization layers (label, envelope,
attribution) hand-built through three FRs in 36 hours. Is this the
shape of a reusable `fail_closed_reduce` contract — a declarative
"model-owned fields / structural fields / evidence field" spec any map
consumer could attach — or is three layers exactly the point at which
the FR-943 research's preserved disagreement (S-2: framework-level
policy after a second consumer) should be re-opened? The second census
consumer decides; watch for it.
