# Diary: FR-296 Watcher FSM Startup Script

**Date:** 2026-04-28
**FR:** FR-296
**Outcome:** Enforced

## Cognitive Process

Straight pattern-transfer: the image-generator-fsm had a proven startup script,
the watcher FSM needed the same structure adapted for its dispatcher-spawns-pipeline
architecture. The plan was obvious — but the judgement found three real bugs in the
FR before enforcement:

1. `statemachine-db reset` doesn't exist — the command is `recreate-database`
2. `pkill -f "statemachine.*watcher"` would kill the UI too
3. `--no-validate` was declared in the usage line but never defined

## Trap Encountered

**quick_confidence** — the FR felt so obvious that the gaps in Phase 1 cleanup
and the phantom `--no-validate` flag nearly made it through without judgement.
The judgement step caught all three. When it feels obvious, judge harder.

## Heuristic

When transplanting a pattern from one project to another, the structural skeleton
transfers cleanly but the CLI surface (flag names, subcommands, PID semantics) does
not. Always validate the exact CLI interface of every tool referenced.

## Seed

Could `statemachine-engine` provide a `start-system` scaffold generator that
reads config files and produces a project-specific startup script automatically?
