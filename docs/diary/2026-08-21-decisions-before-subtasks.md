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

The process became concrete when the worktree boundary was named. Classification
does not merely choose an operation; it chooses existing/new/no-PR context.
A mechanical runner prepares that context and starts the semantic script with a
no-Git contract. Only after the script exits may GitOps commit and publish.

This is stronger than hiding credentials from the model. It is a temporal
ownership rule: semantic execution and publication never act concurrently in
the same worktree. A task cannot accidentally become its own publisher, and
intake cannot leak request bookkeeping into a product branch.

## Heuristic

Architecture questions must become ownership decisions before implementation
planning. Every refactoring subtask must name both the new owner and the old
surface whose final consumer it removes.

Express “no Git” as a runner-enforced task contract and a post-task GitOps
handoff, not as prompt advice distributed among scripts.

## Seed

Can the worktree result be small enough that GitOps needs only starting identity,
changed files, process result, and publication target, without becoming another
semantic envelope?
