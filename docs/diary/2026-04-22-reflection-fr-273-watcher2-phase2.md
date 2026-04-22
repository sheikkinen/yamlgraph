# Reflection: FR-273 Watcher2 Phase 2 — Diary Copilot Node

**Date:** 2026-04-22
**FR:** FR-273 (Phase 2)
**Author:** Watcher2 pipeline development

## Trap: Model Name Drift

The copilot graph initially used `claude-sonnet-4-5` — a model name that exists in the
yamlgraph LLM factory but not in the GitHub Copilot CLI. The copilot CLI exited 0 with
empty output and no error on stdout. Only stderr carried the "model not available" message,
which was discarded by `capture_output=True`.

**Heuristic:** Copilot CLI model names are a separate namespace from LLM provider models.
Validate model availability before assuming cross-compatibility. The copilot node should
surface stderr errors more visibly.

## Insight: UTF-8 Surrogate Boundary

The `--export-state` path triggered a `'utf-8' codec can't encode characters` error.
This is the **normalize at the boundary** pattern — copilot CLI outputs can contain
invalid UTF-8 sequences from terminal control codes. The export serializer needs
`errors='replace'` or similar protection at the serialization boundary.

## Insight: Phase 2 Proves the Integration

The key value of Phase 2 isn't the diary content — it's proving that:
1. `yamlgraph graph run` works inside a git worktree
2. `--export-state` produces valid JSON after a copilot node
3. The watcher2 orchestrator can invoke an LLM and commit its output

This makes Phase 3 (planning + judging with session chaining) a composition problem,
not a feasibility question.

**Seed:** Should copilot node stderr be captured and surfaced as warnings in the
CopilotResult, so model errors don't silently produce empty output?
