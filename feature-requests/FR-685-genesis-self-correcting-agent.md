# Feature Request: FR-685 — Genesis Self-Correcting Pipeline (Gate → Route → Fix)

**Priority:** HIGH
**Type:** Refactor
**Status:** Judged ✅ (architecture amended)
**Effort:** 1 day
**Requested:** 2026-07-04
**Judged:** 2026-07-04
**Depends:** FR-658 (graph-as-tool, enforced), FR-667 (genesis stubs, enforced),
  FR-683 (ref integrity graph-tool)

> Original title: "Genesis Self-Correcting via Graph-Tool Validation".
> The Judgement rejected the agent conversion and replaced the mechanism
> with the gate → route → fix pipeline pattern proven in `graph.yaml`.
> This body reflects the amended scope; see Judgement for rationale.

## Summary

Convert genesis from a warn-only linear pipeline to a self-correcting pipeline:
the `validate` gate routes orphan-bearing output to a `fix_stubs` LLM node that
receives the orphan report and repairs `structured_world`, then re-validates —
capped by `loop_limits`. Happy path stays at exactly 2 LLM calls.

## Starting Point

FR-667 delivered a 2 LLM call genesis: `synopsis` (LLM) → `stubs` (LLM) →
`validate` (Python) → `persist` (Python). The `stubs` node is `type: llm` —
it generates structured output in one shot and cannot self-correct. The
`validate` node checks referential integrity and logs warnings but does not
trigger re-generation.

Current genesis produced zero orphan IDs on 2026-07-04. But this is prompt
discipline, not enforcement — a less cooperative model or a more complex premise
could produce orphans. The validate node only warns; it cannot fix.

FR-658 (`type: graph` tool) and FR-683 (`ref_check` graph-tool) provide the
mechanism for self-correction.

## Problem

1. **One-shot generation**: `stubs` is `type: llm`. If the LLM produces
   orphan IDs, the only feedback is a warning in logs. The user must re-run
   genesis manually.

2. **Warn-only gate cannot fix**: The `validate` node detects orphans but
   has no repair path. The gate → route → fix loop (proven in `graph.yaml`:
   `ref_gate` → conditional route → `fix_refs` → re-validate) gives it one.

3. **No self-correction loop**: Even with the `REFERENTIAL INTEGRITY` prompt
   constraint, LLMs can violate it. A model switch (e.g., DeepSeek → a weaker
   model via FR-464 fallback) or a complex premise with many cross-references
   could produce orphans. The pipeline should handle this gracefully.

## Acceptance Criteria

1. **AC-1**: `genesis.yaml` `validate` node becomes a gate: python tool
   `ref_check` from `nodes/ref_integrity.py` (FR-683), writing `gate_result`.

2. **AC-2**: Conditional edge after `validate`: `gate_result.valid` →
   `persist`; else → `fix_stubs`.

3. **AC-3**: New `fix_stubs` node, `type: llm`, prompt `fix_stubs` (pattern:
   `prompts/fix_refs.yaml`), input = `structured_world` + orphan report,
   output → `structured_world` (same schema as `generate_stubs`). Edge back
   to `validate`.

4. **AC-4**: `loop_limits: validate: 3` — hard cap on repair rounds. On limit
   hit, proceed to persist (warn-only safety net preserved).

5. **AC-5**: `persist_genesis.py` still calls `validate_referential_integrity`
   as a final safety net (warn-only). Defense in depth — the fix loop should
   have repaired orphans, but persist confirms.

6. **AC-6**: Happy path exactly 2 LLM calls (synopsis + stubs); each repair
   round exactly +1 (`fix_stubs`). Assert via mock-LLM call count in tests.

7. **AC-7**: Tests with mock LLM: (a) clean stubs → persist, no fix call;
   (b) orphan stubs → `fix_stubs` invoked with orphan report → clean →
   persist; (c) persistent orphans → loop limit → persist with warning.

Note: deletion of `validate_genesis.py` belongs to FR-683 (per its
Judgement), not this FR.

## Implementation Approach

1. FR-683 must be enforced first (provides `nodes/ref_integrity.py` with
   `ref_check(state)`)
2. Add conditional edge after `validate` on `gate_result.valid`
3. Write `prompts/fix_stubs.yaml` — orphan report + `structured_world` in,
   repaired `structured_world` out (same schema as `generate_stubs`)
4. Add `fix_stubs` node (`type: llm`) + edge back to `validate`
5. Set `loop_limits: validate: 3`
6. Update tests — remove TestValidateGenesis (dies with FR-683), add
   TestGenesisFixLoop with mock-LLM call-count assertions

## Genesis Flow: Before → After

**Before (FR-667):**
```
load → synopsis (LLM) → stubs (LLM) → validate (Python, warn-only) → persist
```

**After (FR-685):**
```
load → synopsis (LLM) → stubs (LLM) → validate (python: ref_check fn)
     → route: valid → persist
              invalid → fix_stubs (LLM, receives orphan report) → validate
```

## Constraints

- Genesis total LLM calls: exactly 2 in happy path (same as FR-667), +1 per
  repair round, hard-capped by `loop_limits`.
- `stubs` and `fix_stubs` stay `type: llm` with native structured output —
  no agent wrapper, no parse-then-reinvoke fallback path.
- Control flow is deterministic YAML routing, not model cooperation.
- `persist_genesis.py` retains its own ref integrity check as defense in depth.

## Risks

- **Fix regression**: `fix_stubs` rewrites the whole `structured_world`; it
  could repair orphans while corrupting other fields. Mitigated: same output
  schema as `generate_stubs`, re-validation after every fix round, persist
  safety net.
- **Oscillation**: fix introduces new orphans → loops. Mitigated:
  `loop_limits: validate: 3` then proceed with warning.

## Related

- [FR-658](FR-658-graph-as-tool.md) — enables `type: graph` tool
- [FR-667](FR-667-genesis-stub-pipeline.md) — current genesis stubs
- [FR-683](FR-683-ref-integrity-graph-tool.md) — ref_check graph-tool
- [FR-664](FR-664-genesis-referential-integrity.md) — original ref integrity

## Judgement

**Verdict: APPROVED — objective frozen, mechanism REPLACED. The agent
conversion is rejected; the self-correction loop ships as gate → route → fix.**

### Assessment

The objective is sound: warn-only validation cannot fix, and prompt discipline
is not enforcement. But the FR's central cost claim is false and it omits the
dominant alternative already proven in this same example.

### Fatal Findings

1. **AC-6 is arithmetically wrong.** "Genesis remains 2 LLM calls in the happy
   path" — no. The agent loop (`tools/agent.py`) works turn-wise: iteration 1
   generates stubs AND emits the `ref_check` tool call (LLM call #1); the tool
   result is appended; iteration 2 produces the final answer (LLM call #2).
   Happy path = synopsis + 2 agent turns = **3 LLM calls**, with the entire
   `structured_world` JSON emitted twice (once in the tool-call turn's
   reasoning, once in the final answer). Worse: agents cannot combine
   `bind_tools` with `with_structured_output` (FR-448) — the final answer
   goes through `_try_structured_output`, which re-invokes the LLM a third
   agent turn whenever `extract_json` fails validation. Worst happy-path:
   4 LLM calls for output FR-667 gets in 1.

2. **The dominant alternative is unconsidered — and already in the codebase.**
   `graph.yaml` (this same example) runs a proven gate→fix loop:
   `validate` (python `ref_gate`) → conditional route → `fix_refs` (LLM) →
   re-validate, capped by `loop_limits`. Applied to genesis:

   ```
   load → synopsis (LLM) → stubs (LLM) → validate (python: ref_check fn)
        → route: valid → persist
                 invalid → fix_stubs (LLM, receives orphan report) → validate
   ```

   Happy path: exactly 2 LLM calls (true AC-6). Fix path: +1 per repair round.
   `stubs` and `fix_stubs` stay `type: llm` with native structured output — no
   parse-then-reinvoke lottery. Control flow is deterministic YAML, not
   delegated to model cooperation (the FR's own Risk: "agent ignoring the
   tool"). Doctrine: conform before extending; cheapest code is unwritten.

### Amended Acceptance Criteria (frozen)

**Folded into the AC, Implementation, Flow, Constraints, and Risks sections
above** — the body now describes the gate → route → fix mechanism. Mapping
from the original draft: AC-1–AC-3 (agent conversion) replaced by gate/route/
fix nodes; AC-4 (delete `validate_genesis.py`) moved to FR-683 per its
judgement; AC-7 (`max_iterations`) superseded by `loop_limits: validate: 3`;
AC-6 corrected from a false cost claim to an asserted mock-LLM call count.

The `ref_check` **graph-tool** (FR-683) remains the composition primitive for
`deepen_events` in worldgen, where an agent already exists. Genesis does not
need an agent to use the same validation function.

Filename retained for traceability; the mechanism is a self-correcting
*pipeline*, not a self-correcting *agent*.
