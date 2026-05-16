# Reflection: The Coherent Design Fallacy — When the Plan Passes the Sniff Test

**Date:** 2026-05-16
**Trigger:** FR-404 (Philosopher's Book) — implemented as full 21-chapter pipeline on first attempt.

## What Happened

FR-404 specified a 21-chapter book pipeline: load traps → plan with copilot → write 21 chapters (sequential map) → epilogue → assemble. The design was internally coherent. Each component made sense. The FR was detailed and reviewed.

Implementation produced a working graph. Tests passed. Demo ran. 21 chapters generated.

But two things were wrong that the tests didn't catch:

1. **`search_diary` and `read_file` tools were defined but never used.** Lint flagged them. The copilot nodes use the CLI backend which has its own tool access — the YAML-declared tools are invisible to them. The key design intent (Philosopher actively searches diary during chapter generation) was silently not happening. The graph passed shape checks; the substance was absent.

2. **The whole thing was too complex to verify incrementally.** The first runnable unit was the complete pipeline. If the chapter quality was poor, was it the prompt? The model? The book_plan context? The missing search tools? The sequential map? Any of 5 components could be the cause.

## The Trap

**`coherent_design_fallacy`**: A complex system whose components are individually plausible passes planning review. The plan is coherent on paper. We build the whole thing before proving any part works in isolation. The first verification is the whole system — which means debugging is a full-system problem.

This is distinct from existing traps:
- `working_system_inertia`: can't see a working system clearly
- `continuation_bias`: defaults to generating rather than asking
- `intent_drift`: plan says X, code does Y

This is the *pre-working* version: **assuming integration will be smooth because the parts fit on the diagram**.

The old adage: *Start with small functional software. Add one thing. Verify still functional. Repeat until big.*

In LLM pipelines this matters more than in traditional software, because:
- Each node adds a new failure mode (prompt, model, tool, schema, timeout)
- LLM outputs are non-deterministic — you need to *see* one chapter before trusting 21
- The integration between copilot nodes and YAML-declared tools is non-obvious

## The Cure

**Incremental verification**: The first working unit should be the smallest meaningful unit. For FR-404 that would have been:

1. `load_trap_list` → returns 21 chapters ✓ (this we got right as a test)
2. `plan_book` copilot → produces a plan for *one* trap ✓ (verify output quality)
3. `write_chapter` copilot → writes *one* chapter using that plan ✓ (verify quality, tool usage)
4. Only then: expand to 21-chapter map

We skipped steps 2 and 3 as standalone verifiable units.

## The Tool Gap Discovery

The lint warning `Tool 'search_diary' is defined but never used` is a `gate_checks_shape_not_substance` instance: the tools were declared (shape present), but the copilot nodes couldn't access them (substance absent). This is the boundary between YAML-declared tools and copilot CLI tool access — a boundary we didn't examine before building on top of it.

## Heuristic

**The first runnable unit should be the smallest meaningful unit, not the complete system.** Coherence on paper does not imply correctness in execution. Each integration point is a potential failure mode — expose them one at a time.

## Seed

If copilot nodes (CLI backend) can't use YAML-declared tools — what is the correct pattern for giving a copilot node access to a specific Python function as a tool? Is the answer: write the tool as a separate YAMLGraph graph and call it as a subgraph? Or is there a copilot tools: declaration that maps differently?
