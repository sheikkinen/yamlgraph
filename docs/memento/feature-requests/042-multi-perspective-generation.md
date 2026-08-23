# Feature Request: Multi-Perspective Generation

**Priority:** LOW
**Type:** Feature
**Status:** REJECTED
**Effort:** 3 days
**Requested:** 2026-02-17

## Judgment (2026-02-17)

**Verdict:** REJECT — Config complexity doesn't justify the abstraction.

**Reasoning:** The `perspectives:` config with variants, strategies (best_of, merge, vote, score), and synthesis introduces significant framework complexity. Users can already wire fan-out → synthesize explicitly using existing primitives:

```yaml
nodes:
  gen_constructivist:
    type: llm
    prompt: generate_lesson_constructivist
    state_key: variant_1
  gen_direct:
    type: llm
    prompt: generate_lesson_direct
    state_key: variant_2
  synthesize:
    type: llm
    prompt: synthesize_variants
    state_key: lesson
```

This is 10 lines of YAML vs. learning a new `perspectives:` DSL. The explicit approach is debuggable, traceable, and requires no new framework code.

**The biopsykososiaalinen problem** (from diary) is better solved by writing better prompts or adding variety at the curriculum design level, not by framework-level multi-perspective generation.

**Alternative:** Document multi-perspective pattern as a recipe. Let users wire it when genuinely needed.

## Summary

Generate each item N ways using different perspectives (prompts, models, or parameters), then synthesize the best elements into a final output. When thinking is near-free, single-perspective generation leaves quality on the table.

## Problem

The innovators toolkit already implements multi-perspective generation: 9 parallel frameworks analyzing the same problem from different angles (SCAMPER, TRIZ, First Principles, etc.), synthesized into one report. But no other pipeline uses this pattern. Each lesson, story beat, translation chunk, and medical record is generated from one prompt, one model, one attempt.

The psykologia lesson review identified a concrete symptom: the "biopsykososiaalinen" crutch appeared across all modules because every lesson was generated from the same pedagogical perspective. If each lesson were generated 3 ways — constructivist, direct instruction, inquiry-based — and a synthesizer picked the best elements, the output would be richer and the monoculture would break.

With flash-tier models at $0.001/call, generating 3 variants of 81 lessons costs $0.24 total. The constraint is no longer cost — it's whether the framework makes multi-perspective generation easy to declare.

## Proposed Solution

Add a `perspectives` option to LLM and map nodes:

```yaml
nodes:
  generate_lesson:
    type: llm
    prompt: generate_lesson
    state_key: lesson
    perspectives:
      variants:
        - prompt: generate_lesson_constructivist
          label: constructivist
        - prompt: generate_lesson_direct
          label: direct_instruction
        - prompt: generate_lesson_inquiry
          label: inquiry_based
      synthesize:
        prompt: synthesize_lesson_variants
        strategy: best_of     # or: merge, vote, score
```

Behavior:
1. Each variant prompt is called in parallel with the same input state
2. All variant outputs are collected into a list
3. The synthesize prompt receives all variants and produces the final output
4. The final output is stored in `state_key` as usual
5. Variant outputs are optionally preserved in `state_key_variants` for inspection

### Strategies

- **best_of:** Synthesizer picks the single best variant (cheapest)
- **merge:** Synthesizer combines best elements from all variants (richest)
- **vote:** Multiple LLM calls score each variant, highest wins (most robust)
- **score:** Each variant is scored, top-N are merged (balanced)

## Acceptance Criteria

- [ ] LLM nodes accept optional `perspectives` configuration
- [ ] Variant prompts execute in parallel
- [ ] Synthesizer prompt receives all variants and produces final output
- [ ] At least `best_of` and `merge` strategies are implemented
- [ ] Works with map nodes (perspectives applied per-item)
- [ ] Variant outputs optionally preserved in state for inspection
- [ ] Omitting `perspectives` preserves current single-prompt behavior
- [ ] Tests added with `@pytest.mark.req` tags
- [ ] Documentation updated

## Alternatives Considered

- **Manual fan-out/in:** Users can already wire up multiple LLM nodes and a synthesizer manually. This works but requires 4+ YAML nodes per perspective set — the `perspectives` key reduces it to one.
- **Temperature-based diversity:** Generate N variants from the same prompt with high temperature. Cheaper to configure but produces less meaningful variation than different prompts.
- **Model-based diversity:** Use different models (Anthropic, OpenAI, Mistral) for each variant. Possible as a layer on top — variant config could accept `model` override.

## Related

- Innovators toolkit 9-way diamond pattern (`projects/innovators-toolkit/`)
- Psykologia lesson review: "biopsykososiaalinen" monoculture finding
- Novel generator's multi-loop approach (different pattern but related goal)
- Diary entry: "The Constraint Shift" — Observation 3
