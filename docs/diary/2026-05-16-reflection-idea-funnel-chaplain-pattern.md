# Reflection: The Idea Funnel, Prompt Safety, and the Chaplain as General Pattern

**Date:** 2026-05-16
**Tags:** ideation, decision-making, prompt-ops, chaplain-pattern, eval, production-safety

## What Was Discussed

Three connected threads emerged in a single session:

1. **Prompt safety in production** — most teams still "tweak and hope," lacking a condemning baseline before deploy
2. **The idea funnel asymmetry** — humans prune early by necessity; LLMs can hold the full alternative space
3. **The Chaplain as the formalized answer** — Ideate → Gather → Judge as a decision pattern, not just a code pipeline

## Key Insights

### Prompt Safety Is a Boundary Problem

The "tweak and watch" antipattern persists because teams lack a *red phase* for prompt changes. This is the TDD parallel: you need a failing eval before deploy, not metrics after. The promptfoo example in this repo already implements the cure — eval as a gate, test cases as the committed baseline, `provider.py` as a 37-line bridge from any graph to Promptfoo assertions.

The gap not yet closed: shadow traffic / live traffic splitting. The current pattern is pre-deploy only.

**Heuristic:** Treat prompts as load-bearing contracts, not ephemeral config. Every prompt change needs a versioned artifact and a baseline eval — the same rigor applied to SQL schema migrations.

### The Idea Funnel Asymmetry

Human planning is lossy by cognitive necessity: 2-3 alternatives considered, one picked, the rest unrecorded. The chosen path survives attention constraints, not quality selection. LLMs can hold 20 alternatives simultaneously, implement all to proof-of-concept depth, and prune with evidence rather than intuition.

The bottleneck shifts from *ideation* to *evaluation*. Width without a selection criterion is noise. The funnel needs a drain — an eval gate, a judge node, a condemning test — or you've created a more elaborate version of the same lossy process.

**Trap:** Generating 20 paths and picking the most confident-sounding one is worse than generating 3 carefully. Plausible ≠ correct.

**Heuristic:** When LLMs hold the full idea space, human judgment becomes *comparative* rather than *generative*. "Pick the best of these 10" is a different (and better-suited) cognitive task than "invent a good solution." The workflow inverts: human → judge, LLM → generator.

### The Chaplain Is Already This Pattern

The Chaplain formalizes the same funnel for code:

```
Ideate  →  Plan      (generate alternatives, write FR)
Gather  →  Research  (agents scour codebase, prior art, constraints)
Judge   →  Judge     (adversarial examination, freeze scope, grant authority)
```

The critical element: **Judge is a separate phase with authority to kill.** Most ideation loops skip this — judgment happens implicitly during implementation, when sunk cost is highest and the cost of reversal is real.

What makes the pattern work is that ideation is wide and cheap, gathering is parallelized, and judgment is adversarial by design — it looks for reasons to reject, not reasons to proceed. Only what survives judgment gets implementation authority.

**Trap identified:** The Judge is still an LLM judging LLM output. Adversarial pressure is weaker than it should be. A human Red Hat at the Judge phase — asking "is the pain real?" not "is the solution valid?" — would catch cases where ideation produced a well-structured solution to the wrong problem. This is the unchallenged premise trap from the Knowledge Graph.

## What the Promptfoo Example Demonstrates

In the context of the prompt-safety discussion, `examples/demos/promptfoo-router/` is the closest thing in the repo to "safely test prompt changes":

- `provider.py` → 37-line bridge from any YAMLGraph graph to Promptfoo
- `tests/*.yaml` → committed baseline (deterministic + LLM-as-judge)
- `promptfooconfig.yaml` → wires graph path, output key, test discovery
- CI hook → eval as gate, not hope

Adapting for any graph: copy `provider.py`, point `config.graph` at your graph YAML, write test cases matching your state keys.

## Seeds

**Seed 1:** Can a graph run its own alternatives in parallel, self-evaluate against a rubric, and surface only the top-N for human review — turning ideation into a structured selection problem rather than a generation problem? The `innovation_matrix` graph is a partial answer; the missing piece is the self-evaluation and ranking step.

**Seed 2:** Can the Chaplain pipeline be extracted as a general-purpose decision framework — problem in, judged plan out — applicable outside software engineering? The Ideate → Gather → Judge structure is domain-agnostic. The current implementation is specialized for code only because the tooling (git, pytest, ruff) is code-specific. The pattern is not.

**Seed 3:** Can a graph lint its own prompt changes against a baseline eval set before allowing a deploy? That is a gate, not a hope — and it would close the last mile of the prompt-safety problem for teams using YAML-first prompt management.
Seed: marker echoed
