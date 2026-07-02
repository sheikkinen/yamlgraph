# Diary: FR-655 — The Prompt Is the Asset

**Date:** 2026-07-02
**FR:** FR-655 (genesis pipeline)
**Trap:** architecture_as_diagram — subgraph invocation as assumed reuse mechanism

## Observation

The original FR-655 proposal assumed Phase 1 would invoke the dungeon_master
graphs as subgraphs (CAP-111/FR-255). The judgement caught this: three separate
graphs with incompatible state schemas can't be chained without state-bridging
glue. But the *value* of those graphs was never in the wiring — it was in the
prompts. Synopsis.yaml, character_roster.yaml, character.yaml — these are the
reusable assets. The graph YAML around them is disposable scaffolding.

## Heuristic

**The prompt is the asset, the graph is the scaffold.** When reusing across
pipelines, copy the prompt file (or symlink it), not the graph. Graph YAML
encodes state routing that's specific to one pipeline; prompt YAML encodes
domain knowledge that transfers.

Corollary: when the user says "expect deprecation of dungeon_master", the
correct action is to copy prompts into novel_fandom's prompts/ directory,
making them self-contained. A reference to an external graph is a dependency;
a copied prompt is an owned asset.

## Cure applied

- Copied 3 DM prompts into `novel_fandom/prompts/genesis_*.yaml`
- Created one new prompt: `structure_world.yaml` (Phase 2)
- No cross-example dependencies — genesis is self-contained

## Seed

Can YAMLGraph support a `prompt_library` concept — a shared directory of prompts
that multiple graphs reference without copying? Like a package registry for
prompts. The duplication is acceptable now (3 files) but won't scale if 10
pipelines need the synopsis prompt.
