# Feature Request: Compaction Pattern — Example & Documentation

**Priority:** MEDIUM
**Type:** Documentation
**Status:** Judged — Authority GRANTED (2026-06-30)
**Effort:** 0.5 days
**Requested:** 2026-06-28

## Summary

Document and demonstrate the **compaction pattern** using existing YAMLGraph
primitives (guards, conditional edges, llm node, passthrough node, python tool).
No new node type — the pattern is achievable today with existing infrastructure.

## Rationale for Downgrade

Evaluation (2026-06-30) concluded that compaction behavior does not warrant a
first-class node type:

1. **Guards solve the conditional trigger** — `pre` guard with `on_fail: skip`
   fires the LLM call only when state exceeds a threshold.
2. **The behavior is just llm + passthrough** — summarize (llm node) then
   replace state (passthrough with conditional edge). Two existing nodes.
3. **Token counting is a trivial python tool** — 10 lines, reusable.
4. **Framework costume trap** — if 80% of the "compaction node" is calling
   `execute_prompt` with a guard, it's an llm node in a costume.
5. **Hysteresis/fidelity corrections are unvalidated** — building complex
   behavior without proving the base pattern in a real graph risks over-engineering.

If 2+ production graphs adopt the pattern and manual wiring proves painful,
revisit as a first-class node type in a new FR.

## Value Statement

Graph authors learn how to keep long-running graphs within token budgets using
existing primitives, without waiting for new framework code.

## Deliverables

### 1. Demo: `examples/demos/compaction/`

A working graph that demonstrates compaction using existing primitives:

```yaml
# graph.yaml (sketch)
metadata:
  name: compaction-demo
  description: Long-running loop with automatic context compaction

state:
  messages:
    type: list
    reducer: add
  compaction_summary: str
  iteration: int

nodes:
  generate_message:
    type: llm
    prompt: generate_turn
    state_key: messages

  estimate_tokens:
    type: python
    function: tools.token_counter:estimate_tokens
    state_key: token_estimate

  compact:
    type: llm
    prompt: compaction_summary
    variables:
      history: "{state.messages[:-3]}"
    state_key: compaction_summary
    guards:
      pre:
        - check: "state.token_estimate > 2000"
          on_fail: skip
          message: "Below threshold, no compaction needed"

  reset_state:
    type: passthrough
    output:
      messages: "[state.compaction_summary] + state.messages[-3:]"

edges:
  - from: generate_message
    to: estimate_tokens
  - from: estimate_tokens
    to: compact
  - from: compact
    to: reset_state
    condition: "state.compaction_summary"
  - from: compact
    to: generate_message
    condition: "not state.compaction_summary"
  - from: reset_state
    to: generate_message
```

With:
- `tools/token_counter.py` — trivial char/4 heuristic
- `prompts/compaction_summary.yaml` — recall-first summary prompt
- `demo-output.log` proving bounded token usage over N iterations

### 2. Reference doc: `reference/compaction-pattern.md`

Short recipe covering:
- The problem (unbounded state growth)
- The pattern (guard → llm → passthrough reset)
- Token estimation approaches (char/4, tiktoken, provider APIs)
- Keep-tail semantics (slice the last N items verbatim)
- Hysteresis (track `last_compaction_iteration` to avoid re-summarizing summaries)
- When to graduate to a first-class node type

## Acceptance Criteria

- [ ] `examples/demos/compaction/graph.yaml` runs end-to-end with `yamlgraph graph run`
- [ ] `demo-output.log` shows token estimate staying bounded over 10+ iterations
- [ ] `reference/compaction-pattern.md` documents the pattern
- [ ] No new node type code — uses only existing primitives (llm, python, passthrough, guards, edges)

## Future Consideration

If 2+ production graphs adopt this pattern and the multi-node wiring proves
painful or error-prone, create a new FR for a first-class `compaction` node type
that encapsulates the pattern. The Judgement corrections from the original FR
(fidelity floor, hysteresis, conservative estimates) remain valid design
constraints for that future FR.

## Related

- `docs/2026-06-28-research.md` (gap #1)
- Anthropic, *Effective context engineering for AI agents* (Sep 2025) — compaction
- `yamlgraph/executor.py`, `yamlgraph/node_factory/`
- Original judgement preserved below for reference when/if graduating to node type

---

<details>
<summary>Original Judgement (2026-06-28) — preserved for future reference</summary>

Corrections that remain valid if this graduates to a node type:

1. **Fidelity floor**: Never destroy source irrecoverably; write pre-compaction
   state to checkpointer. Keep-tail floor for verbatim recent items. Smoke
   assertion that named entities survive in summary.
2. **Hysteresis**: Compact only new material since last compaction, or set
   post-compaction cooldown to avoid summary-of-summary erosion.
3. **Conservative token estimate**: Heuristic must over-estimate (fire early)
   rather than under-estimate (fire late → window blown).

</details>
