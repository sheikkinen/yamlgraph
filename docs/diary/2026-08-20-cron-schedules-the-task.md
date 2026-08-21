# Cron Schedules the Task

**Date:** 2026-08-20
**FR:** FR-847

## Trap

The scheduler accumulated process supervision, graph discovery, DAG execution,
state interpretation, output rendering, and Git publication because nobody had
named who owned the result. Each addition looked locally useful. Together they
turned a one-command trigger into a second application runtime with 1,052 lines
of production, workflow, and focused test code.

Product decomposition did not reveal this because the responsibilities were
split by feature rather than by owner. The decisive question was not “how do we
modularize cron?” but “who owns the phone call?” Outcaller owns the call and its
structured answer. Cron owns only when its graph starts.

The retained haiku exposed a smaller version of the same error. Cron passed
`date` into the graph, which meant the graph was not actually a runnable task;
it was a partial function completed by scheduler knowledge. The triviality of
running `date +%Y-%m-%d` made the boundary easier to miss, not more defensible.
Current-date resolution belongs in a deterministic graph tool. Python remains
tool implementation for domain behavior, never hidden scheduler orchestration.

## Heuristic

For every scheduled operation, write the boundary as two sentences before
adding infrastructure:

1. The scheduler starts one independently runnable task.
2. The task owns all domain effects, outputs, and failure semantics.

If the scheduler must understand task state, output shape, filenames, or Git
publication, the task contract is incomplete or a separately named composition
application is hiding inside the scheduler.

Apply the same test to “small” inputs: if removing cron makes a task unable to
discover its own current date, the scheduler is still part of the application.

## Seed

Which other YAMLGraph wrappers interpret generic graph output because the task's
actual effect owner has not been named?
