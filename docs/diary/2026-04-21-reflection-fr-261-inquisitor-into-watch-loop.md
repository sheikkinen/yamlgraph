# Reflection: FR-261 Inquisitor Into Watch Loop

**Date:** 2026-04-21
**FR:** FR-261
**Branch:** feat/fr-261-inquisitor-into-watch-loop

## What Was Done

Moved the Inquisitor audit from a pre-commit hook (running on every commit) into the `watch.sh` poll loop (running once per cycle, after enforcement). The pre-commit hook remains as a lightweight gate; the full Inquisitor audit now runs asynchronously in the background, appending findings to `docs/diary/` without blocking the commit flow.

## Cognitive Trap: Infrastructure Self-Exempt

The Inquisitor was running as a pre-commit hook — meaning the tool that audits the codebase for slow/blocking patterns was itself a slow/blocking pattern on every commit. This is the **infrastructure_self_exempt** trap: meta-tooling exempted from the gates it enforces.

Moving it to `watch.sh` means the audit is decoupled from the commit critical path. The pre-commit hook retains a fast shallow check; the deep audit runs out-of-band. Same result, no commit friction.

## Heuristic

**Async audits, sync gates**: Any audit that takes >5 seconds belongs in a background loop, not a synchronous gate. Pre-commit hooks should be fast enough that developers never reach for `--no-verify`. Reserve blocking gates for cheap, deterministic checks (ruff, conflict markers, req coverage). Move expensive, exploratory checks (Inquisitor, jscpd, radon) to the background watch loop.

## Seed

The Inquisitor now runs once per watch cycle. Could it be rate-limited further — e.g., only run if the diff since the last audit exceeds N lines of Python? An audit triggered by a one-line YAML change is wasteful. A line-count threshold on the diff would reduce Inquisitor runs by ~70% while preserving coverage on meaningful changes.
