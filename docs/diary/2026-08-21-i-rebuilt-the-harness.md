# I Rebuilt the Harness

**Date:** 2026-08-21
**Context:** GitClaw architecture reflection after FR-849 RED

## Reflection

I recognized that a 439-line cron runner was absurd for starting one graph, then
repeated the same move by writing a 291-line acceptance script for six issues.
The language changed from runtime safety to acceptance evidence, but the
cognitive move was identical: every unknown became another local check, state
variable, polling rule, or artifact parser.

I was optimizing for defensibility inside an architecture vacuum. Each gate had
a reason. Together they created another implementation of the lifecycle. The
script did not merely observe GitClaw; it reconstructed GitClaw from GitHub's
incidental surfaces. That should have been the stop signal.

The operator's short correction - “I tell the repo it works on” - exposed the
pattern sharply. I had invented repository classification and target preflight
despite receiving an explicit parameter. I was replacing operator intent with a
machine-owned policy because policy felt safer than trust. The same bias appears
throughout GitClaw: canonicalize the issue, hash it, filter artifacts, inspect
headings, constrain paths, infer state, and call the accumulation architecture.

The live RED corrected the abstraction. The agent and verifier succeeded. The
publisher pushed a branch and failed creating a PR. The branch contained intake
state plus coupled Plan/Judge output. No amount of another output filter explains
that cleanly. The defect is ownership: intake, semantic lifecycle, and GitOps
share one working tree and no component owns partial publication.

## Heuristic

When an observer needs more than the system under observation to explain the
system's lifecycle, stop adding observation logic. Name the missing operation
contract and owner first.

When every individual gate is defensible but the whole feels shapeless, inspect
composition, not gate quality. Local correctness can be the mechanism by which
global incoherence becomes permanent.

## Seed

What is the smallest task result GitOps needs to publish mechanically while the
issue remains the lifecycle record and acceptance only reports the run and
changed files?
