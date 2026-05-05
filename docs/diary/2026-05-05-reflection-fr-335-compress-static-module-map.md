# Reflection: FR-335 Compress Static Module Map Output

**Date:** 2026-05-05
**FR:** FR-335
**Tags:** module-map, static-analysis, compression, ast, documentation

## What Was Built

Compressed the static module-map generator (`scripts/generate_module_map.py`) so that
`reference/module-map.md` stays within the ≤250-line agent-readable budget. Three
concrete changes: (1) dependency lists now filter to internal `yamlgraph.*` imports only,
(2) trivial `__init__.py` modules (< 10 lines, ≤ 1 public export) are collapsed to a
single compact line instead of a full `###` section, and (3) exports and dependency
lists are rendered as compact one-line fields rather than nested bullet lists.

## Cognitive Traps Encountered

**Trap: Downstream symptom patch.**
The first instinct was to post-process the generated markdown (line-count filter, truncation).
The correct approach is to normalize at the boundary — fix the generator to produce compact
output, not to trim a verbose artifact after the fact. `the_one_law` applies: normalize at
the entry boundary.

**Trap: Removing signal to hit a number.**
Initial prototype dropped dependency lists entirely, which hit the line budget trivially but
removed the internal graph signal the map was designed to provide. The correct trade-off is
to keep the signal while filtering out the noise (stdlib/third-party imports).

**Trap: Over-generalizing the trivial-module rule.**
The first version of the collapse threshold was set too aggressively (any module < 20 lines),
which collapsed modules with multiple meaningful exports. Anchoring the rule to
`__init__.py` + `< 10 lines` + `≤ 1 export` kept the collapse semantically meaningful.

## Heuristics Learned

**Heuristic:** Line-budget artifacts should be generated compact, not post-processed into
compact form. Apply compression at the generator level so the artifact is always correct
at creation time — no trimming step required downstream.

**Heuristic:** When filtering noise from a list (imports, tokens, lines), define "noise"
precisely by exclusion pattern (`yamlgraph.*` only), not by heuristic length thresholds.
Exclusion patterns are deterministic; length thresholds drift.

## What Went Well

- The parent FR-331 test suite (`test_fr331_static_module_map_tier2_context.py`) continued
  to pass unchanged — the compression stayed within the existing contract surface.
- Red→green TDD cycle was fast: the five AC tests were mechanically derived from the
  acceptance criteria and the fix path was clear from the failing assertions.
- Stdlib-only constraint was trivially preserved because compression required no new
  parsing primitives beyond what was already in the generator.

## Seed

Now that the map fits within 250 lines, the natural next question is:
**Can the map be filtered further at query time — returning only the subset of modules
touched by a given PR's changed files — so an agent receives a 10-20 line scoped view
rather than the full 250-line tree?**

That would close the loop from "static orientation artifact" to "dynamic scoped context"
without requiring any LLM inference — pure structural filter on the existing map.
