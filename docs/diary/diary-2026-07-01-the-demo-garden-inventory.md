# The Demo Garden Inventory

**Date:** 2026-07-01
**Context:** Reflective analysis of the examples/ directory — 101 examples accumulated over 5 months.

## Findings

### Scale
- **26 top-level examples** (complex, multi-file applications): 3 are enormous (dungeon_master 24k LOC, plot_modeller 17k LOC, yamlgraph_gen 5k LOC)
- **75 demos** (single-concept showcases)
- Total: 101 examples. The framework has more examples than it has source modules.

### Execution Proof
- 43/75 demos (57%) have `demo-output.log` proving they ran
- 32 demos remain unproven — including **foundational** ones: `router`, `map`, `reflexion`, `subgraph`, `interview`, `interrupt`
- The learning path's demos (the ones most likely to be someone's first touch) are among the unproven

### Node Type Coverage Gaps
The framework has 14 node types. Demo coverage is skewed:
- **Saturated:** `llm` (86 instances), `python` (61), `shell` (73), `tool` (35)
- **Adequate:** `agent` (16), `map` (12)
- **Thin:** `router` (3), `interrupt` (3), `copilot` (4 in demos)
- **Missing:** `passthrough`, `tool_call`, `pipeline` — zero demo presence

### Provider Distribution
- Anthropic (34) and Mistral (33) dominate
- Google (7), OpenAI (6) are minority
- Azure, Vertex, Replicate, Inception, xAI: 1-2 each
- DeepSeek, LMStudio: absent from examples

### Structural Observations
1. **Shell nodes are the workhorse** — 73 instances. More shell than LLM nodes. The framework is being used as a structured task runner as much as an LLM orchestrator.
2. **Top-level examples drift toward mini-applications** — dungeon_master and plot_modeller are products, not demos. They accumulate their own debt.
3. **Demo categories cluster around infrastructure** — 8 watcher2-* demos, 2 a2a-* demos. These exist to prove CI/automation features, not to teach users.
4. **5 demos lack graph.yaml** (a2a_server, hellograph-speed, interrupt, script-retirement, streaming) — they either use alternative entry points or are incomplete.

## Cognitive Trap Observed

**`inventory_by_visibility`** — The README presents all 101 examples as equal-weight items in tables. But the *teaching* value is concentrated in ~15 demos (the learning path + a few key feature demos). The *proof* value is concentrated in the 43 with execution logs. The remaining ~45 are either infrastructure-proving artifacts or aspirational placeholders.

A newcomer reading the examples README encounters a 75-row table and has no signal for "start here" beyond the learning path header. The learning path itself references demos that cannot prove they work.

## Heuristic

**The unproven teacher is worse than no teacher.** A demo in the learning path without `demo-output.log` signals "we don't run our own onboarding" — it's the `gate_checks_shape_not_substance` trap applied to documentation. The directory exists (shape), but the proof is absent (substance).

## Prescription

1. Run the 7 learning-path demos and capture `demo-output.log` for each — this is the minimum viable proof.
2. Consider tiering: "Core Demos" (proven, curated, 15-20) vs "Feature Proofs" (CI artifacts) vs "Applications" (top-level).
3. The `passthrough`, `tool_call`, and `pipeline` node types need at least one demo each, or they should be documented as internal-only.

## Seed

**If shell nodes outnumber LLM nodes in practice, is YAMLGraph converging on a general-purpose task DAG runner with LLM nodes as one capability among many — and if so, should the framework's identity and marketing reflect that?**
