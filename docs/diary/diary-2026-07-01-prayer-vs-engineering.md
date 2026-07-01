# Prayer vs Engineering — Three Designs to Red Links

**Date**: 2026-07-01
**FR**: FR-643v2 (world expansion pipeline)
**Trap**: `plausible_wrong_answer` + `framework_costume`

## Context

The task: expand a fiction wiki's thin pages into rich, interconnected canon. Three designs were attempted and rejected before the fourth succeeded.

## The Three Failed Designs

**Design 1 (FR-643): The Analyst Loop.** An LLM node diagnoses which pages are thin, decides what's missing, generates expansion tasks. This was "a prayer to the almighty LLM capable of everything" — the thinness criteria are known deterministically (character without backstory, event without participants), so asking an LLM to discover them is paying inference for arithmetic.

**Design 2: Python magic.** The loop logic moved to Python, but the enrichment stayed monolithic — one big prompt tries to deepen everything at once. Framework costume: the graph existed, but the LLM did all the work in a single node.

**Design 3: Linear pipeline.** Overcorrected from the loop rejection — removed the loop entirely. But world expansion IS iterative: deepening Kaelen introduces the Ashfall Pact, which needs its own page, which introduces new characters.

**Design 4 (FR-643v2): Red links.** The Wikipedia insight — content declares its own gaps. When you deepen a character, the LLM returns `new_entities` — references to pages that don't exist yet. These become skeleton pages (depth N+1). The loop continues until no thin pages remain or max_depth is reached. Deterministic selection, LLM deepening, mechanical gap detection.

## Trap Analysis

The core trap was `plausible_wrong_answer` applied to architecture: Design 1 had the right shape (graph with loop, LLM nodes, state management) but wrong substance (LLM doing deterministic work). It passed the shape check — "yes, this is a valid YAMLGraph pipeline" — while being semantically wrong about where intelligence should live.

Secondary trap: `framework_costume`. Design 2 wore the graph as a costume — the graph existed but <50% of nodes used core graph features. The real work happened in one Python node.

## Heuristic

**Separate the known from the unknown.** When building LLM pipelines, enumerate what can be determined mechanically (thinness criteria, reference resolution, deduplication) vs. what genuinely requires inference (expanding backstory, inventing connected events). Mechanical work in Python nodes, creative work in LLM nodes. An LLM doing arithmetic is a prayer; a Python function doing arithmetic is engineering.

## The Red Link Pattern

The expansion pattern has broader applicability beyond fiction wikis:
- **API documentation**: Expand a service description, discover referenced types that lack pages
- **Knowledge bases**: Deepen a concept, surface prerequisite concepts that need entries
- **Codebase exploration**: Document a module, discover undocumented dependencies

The common structure: content production that reveals gaps in surrounding content, with mechanical gap detection and bounded recursion.

## Seed

**Can the red link mechanism become a reusable graph pattern?** A `red_link_expander` subgraph template: reload state → select thin → deepen (map) → collect references → create skeletons → validate → persist → loop. The domain-specific parts (thinness criteria, deepening prompt, page schema) would be injected as configuration. If novel_fandom, API docs, and knowledge bases all follow this shape, it's a pattern worth extracting.
