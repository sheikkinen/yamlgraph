# Feature-Request Methodology in Historical Context

YAMLGraph's feature-request process is a small-batch descendant of
waterfall-era requirements discipline. It keeps the useful parts of formal
methods--explicit requirements, independent review, verification evidence, and
traceability--but applies them to one change at a time instead of to a whole
project phase.

The shortest description is:

> Per-change requirements baseline -> independent judgement -> scoped
> implementation -> verification -> traceability artifact -> reflection loop.

This makes the process closer to a micro stage-gate system than to a generic
issue tracker or agile story board.

## YAMLGraph's process shape

The local rite is:

1. **Research** - inspect prior art, existing code, rejected FRs, and external
   methods before proposing new work.
2. **Plan** - write a feature request in `feature-requests/` with value,
   problem, ideal result, proposed solution, acceptance criteria, alternatives,
   and related artifacts.
3. **Judge** - run an independent review that approves, amends, splits, or
   rejects the FR. Approved scope is frozen.
4. **Enforce** - write the failing test first, implement the smallest sufficient
   change, and update the FR with implementation decisions.
5. **Validate** - pass tests, pre-commit, CI, changelog, traceability, demo, and
   diary gates as applicable.
6. **Distill** - record the cognitive trap or insight in `docs/diary/`; repeated
   lessons can graduate into doctrine.

The important property is not that a Markdown document exists. The important
property is that the FR becomes the governing contract for the change.

## Closest waterfall-era relatives

| YAMLGraph artifact or gate | Historical analogue | Shared purpose |
|---|---|---|
| Feature request | Software change request / engineering change proposal | Justify a bounded change before implementation |
| Judgement | Change Control Board / design review | Decide go, amend, split, or kill before spending implementation effort |
| Scope frozen | Requirements baseline | Prevent implementation from drifting beyond the approved requirement |
| Acceptance criteria | Verification criteria / acceptance test criteria | Define how completion will be proven |
| RED/GREEN tests | V-model verification side | Pair each requirement with executable evidence |
| CAP -> REQ -> test -> changelog | Requirements Traceability Matrix | Preserve why each artifact exists and how it is verified |
| Chaplain pipeline stages | Stage-gate / phased review | Advance only through explicit decision points |
| FR document | Mini SRS / mini design package | Capture problem, constraints, solution, and verification in one artifact |
| Diary and doctrine feedback | CMM/CMMI-style process improvement | Convert repeated failures into stronger process constraints |

## Methodology comparisons

### Waterfall model

Classic waterfall sequences requirements, design, implementation, integration,
testing, deployment, and maintenance. YAMLGraph borrows the demand that
requirements and acceptance criteria precede implementation, but it rejects the
large batch size. The unit of waterfall is the project phase; the unit of
YAMLGraph is the individual feature request.

YAMLGraph is therefore best described as **micro-waterfall per change**, not as
classic project-scale waterfall.

### Stage-gate / phase-gate

Stage-gate processes divide work into stages separated by decision gates. A gate
is not a status meeting; it is a go/kill/prioritization decision.

YAMLGraph has the same skeleton:

- Plan gate: is the FR coherent and valuable?
- Judge gate: is the scope clear, minimal, and testable?
- Enforce gate: did implementation obey the judgement?
- Validation gate: do tests, hooks, CI, and traceability pass?
- Merge gate: branch protection and required checks decide whether the change
  may enter `main`.

This is the strongest historical match.

### Change Control Board

A Change Control Board evaluates proposed changes against phase, cost, schedule,
quality, and client acceptance. YAMLGraph's Judge plays the lightweight version
of that role. It reviews whether the proposed change is worth doing, whether the
solution is minimal, whether the acceptance criteria are testable, and whether
the scope should be approved, amended, split, or rejected.

The Judge is therefore an automated or assisted CCB, specialized for repository
changes.

### Software Requirements Specification

An SRS establishes agreement on what a system should do before detailed design
and implementation. A YAMLGraph FR is not a full SRS, but it is a **mini-SRS for
one change**. It records the problem, value statement, ideal result, proposed
solution, constraints, acceptance criteria, alternatives, and related artifacts.

YAMLGraph adds local refinements that are uncommon in traditional SRS templates:

- first consumer / first event
- ideal-result-backwards framing
- explicit judgement verdict and finding table
- purge list for speculative interfaces
- diary reflection and doctrine feedback
- mechanical traceability to requirements, tests, changelog, and CI

### MIL-STD-498 and defense documentation

MIL-STD-498 organized software development around formal data item descriptions:
operational concept, requirements specification, design description, test plan,
test description, test report, user manuals, and support artifacts.

YAMLGraph compresses the same idea into repo-native artifacts:

| Formal artifact family | YAMLGraph analogue |
|---|---|
| Operational concept | Value statement, problem, first consumer |
| Software requirements specification | FR proposed solution and acceptance criteria |
| Software design description | Implementation plan, code diff, and FR decisions |
| Software test plan / description | RED tests and acceptance tests |
| Software test report | pytest output, CI result, demo logs |
| Change record | FR status, changelog fragment, diary entry |

The result is documentation discipline without a separate document bureaucracy.

### V-model

The V-model pairs each development definition stage with a verification stage:
requirements with acceptance tests, system design with system tests,
architecture with integration tests, and module design with unit tests.

YAMLGraph mirrors this through TDD and requirement traceability. A requirement is
not complete merely because code exists; it is complete when a test, changelog
entry, and related gates prove the change.

### Requirements traceability

Traditional traceability follows a requirement from origin through design,
implementation, verification, and later change. YAMLGraph's traceability spine is
repo-native:

```text
FR -> CAP -> REQ -> test marker -> changelog fragment -> CI evidence -> diary
```

This gives each implemented behavior a reason for existing and makes missing
verification visible.

### SSADM and structured analysis

SSADM and structured analysis emphasize current-system investigation,
feasibility, alternatives, logical specification, and technical options.
YAMLGraph keeps a lighter version of this in the FR's problem statement,
alternatives considered, ideal result, and proposed solution.

The shared principle is that analysis should remove ambiguity before
implementation starts.

### CMM / CMMI process maturity

CMM and CMMI formalize process maturity: define the process, measure it, improve
it, and make improvement repeatable. YAMLGraph's diary and doctrine loop serves
the same function at repository scale. Repeated failures become named traps,
then cures, then mechanical gates.

## What is different from waterfall

YAMLGraph keeps formal control but changes the economics:

- **Small batch size** - one FR instead of a release-sized requirements phase.
- **Executable verification** - acceptance criteria become tests and CI gates,
  not only sign-off text.
- **Living traceability** - links live in files, test markers, changelog
  fragments, and generated registries.
- **Independent judgement** - planning and judgement are separated to reduce
  anchoring and continuation bias.
- **Reflection feedback** - process failures are not merely recorded; repeated
  ones become future constraints.
- **Kill path is normal** - rejection or split is a successful gate outcome, not
  a process failure.

## Summary

YAMLGraph's FR methodology is best understood as:

> A lightweight, executable, per-feature change-control board plus requirements
> traceability matrix, wrapped in a stage-gate process and verified through
> TDD/CI.

It inherits its bones from waterfall-era requirements engineering, phase gates,
change control boards, V-model verification, and traceability matrices. Its
modern contribution is to make those controls small, automated, repository-local,
and continuously self-correcting.
