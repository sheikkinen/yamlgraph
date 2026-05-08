---
name: reflexion
description: 'Self-correcting writing via Draft → Critique → Refine loop. Use when: generating essays, reports, documentation, or any content that benefits from iterative self-improvement. The agent drafts, critiques its own output, then refines until quality threshold is met.'
argument-hint: 'Topic or writing task description'
---

# Reflexion (Self-Correction Loop)

A metacognitive writing pattern: Draft → Critique → Refine, repeated until the output meets a quality threshold.

## When to Use

- Writing essays, reports, or documentation
- Generating content where first-draft quality is insufficient
- Any task where self-evaluation improves output
- User asks for "high quality" or "polished" writing

## Procedure

### 1. Draft

Write an initial version addressing the topic. Don't overthink — get ideas down.

**Constraints:**
- Address the topic directly
- Include structure (intro, body, conclusion)
- Aim for substance over polish

### 2. Critique

Evaluate the draft on these dimensions (score 0.0–1.0 each):

| Dimension | Question |
|-----------|----------|
| **Clarity** | Is every sentence unambiguous? |
| **Depth** | Are claims supported with evidence or reasoning? |
| **Structure** | Does the flow build logically? |
| **Conciseness** | Can anything be cut without losing meaning? |
| **Engagement** | Would the reader keep reading? |

**Compute overall score** (average). If score ≥ 0.8 → output the draft. If < 0.8 → continue to Refine.

**Provide specific feedback:** what's weak, what to change, what to keep.

### 3. Refine

Rewrite the draft incorporating the critique feedback. Do not start from scratch — improve the existing structure.

**Rules:**
- Address every specific critique point
- Preserve what was praised
- Tighten prose (shorter is better)

### 4. Loop

Return to Step 2 (Critique) with the refined draft. Maximum 3 iterations — after that, ship what you have.

## Execution (Automated)

```bash
yamlgraph graph run examples/demos/reflexion/graph.yaml --var topic="<TOPIC>" --full
```

## Anti-Patterns

- **Infinite refinement**: Stop at 3 iterations. Diminishing returns.
- **Rewriting from scratch**: Refine, don't replace.
- **Vague critique**: "It's not good enough" is useless. Be specific.
- **Ignoring strengths**: Critique must acknowledge what works.
