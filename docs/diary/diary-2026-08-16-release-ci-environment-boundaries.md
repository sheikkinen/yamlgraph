# Diary: Release CI Environment Boundaries

**Date:** 2026-08-16
**Release:** v0.5.19 -> v0.5.20

## What happened

The v0.5.19 tag was internally green but failed release CI in three environment
boundaries hidden by the developer machine: adjacent `node_modules` made pure
JavaScript helper imports look dependency-free; the repository checkout path
did not repeat `yamlgraph/yamlgraph`; and an absent route-log env was collapsed
with an explicit `0` disable.

The fixes normalize at those boundaries: lazy-load Playwright only in the CLI
execution path, inspect path components relative to `examples`, and preserve
the distinction between an absent env key and a present off value.

**Heuristic:** A release test must remove ambient conveniences, not merely run
the same command in another directory.

**Seed:** Which optional dependencies currently leak through import-time setup
but remain invisible because the development checkout has every extra installed?
