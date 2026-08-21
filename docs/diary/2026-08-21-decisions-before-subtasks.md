# Decisions Before Subtasks

**Date:** 2026-08-21
**Context:** GitClaw architecture and refactoring overview

## Reflection

The architecture analysis initially ended with seven open questions. That was
still too passive. The implementation had already answered each question in
code; leaving them open invited every subtask to answer again. The operator's
decisions made the target shape smaller immediately: issue lifecycle is the
request, YAMLGraph classifies and owns semantics, GitOps owns mechanics and
reconciliation, and acceptance only observes.

The refactoring overview became useful only after each subtask included what it
must retire. Without retirement, extraction would add classifier, GitOps, and
task components beside the existing parser, publisher, verifier, and harness.
That would improve the diagram while worsening the repository.

## Heuristic

Architecture questions must become ownership decisions before implementation
planning. Every refactoring subtask must name both the new owner and the old
surface whose final consumer it removes.

## Seed

Can subtask judgements mechanically reject a proposal whose retirement ledger
is empty while it adds another component to an already duplicated lifecycle?
