# RED Before Repair

**Date:** 2026-08-21
**FR:** FR-849

## Trap

The desired lifecycle sounded like six commands, but the first real issue
exposed two earlier boundaries before command coverage mattered. Publication
failed after pushing a branch, and Plan produced FR plus judgement while the
desired process requires Plan alone. A discussion-first approach would likely
have started by adding Judge, Test, and Run commands and left both preceding
failures hidden.

The acceptance script also failed in its own observation layer by using an
interactive `gh run watch`. Separating test defects from product defects was
essential: replace the watcher with API polling, but preserve the publisher and
Plan-coupling RED unchanged.

## Heuristic

Drive lifecycle acceptance from the first external event and stop at the first
failed artifact transition. Repair only the witness when observation itself is
broken. Product RED remains immutable evidence for the next judged change.

Let the operator name the target repository. Safety comes from explicit
mutation boundaries and observed artifacts, not from a hardcoded repository
taxonomy that second-guesses the invocation.

## Seed

Can each GitClaw issue operation declare its required input artifact and exact
output artifact so lifecycle composition becomes data rather than parser logic?
