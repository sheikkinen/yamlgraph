# LLM-as-Gate Pattern

Use this pattern when deterministic checks can verify shape/status, but you also need a semantic decision about meaning.

- Deterministic or mechanical gates (for example `grep`, file existence, and exit code checks) are great for objective pass/fail conditions.
- They do not validate semantic meaning.
- For semantic meaning checks, use an LLM node with structured output and route on that output.

No new framework node type, action type, or primitive is required. Compose existing YAMLGraph primitives (`llm` + `router` + edges).

## Prompt schema (semantic verdict)

```yaml
# prompts/semantic-gate.yaml
schema:
  name: SemanticGateDecision
  fields:
    verdict:
      type: str
      description: "pass|fail"
      enum: [pass, fail]
    reason:
      type: str
      description: "why the item passes or fails semantically"
```

## Graph pattern (`type: router` + `route_field: verdict`)

```yaml
name: llm-as-gate
start: evaluate

nodes:
  evaluate:
    type: llm
    prompt: semantic-gate
    state_key: gate_result

  route_verdict:
    type: router
    route_field: verdict
    routes:
      pass: continue_flow
      fail: fail_path

  continue_flow:
    type: llm
    prompt: continue-flow
    state_key: output

  fail_path:
    type: llm
    prompt: remediation
    state_key: remediation_output

edges:
  - from: evaluate
    to: route_verdict
  - from: continue_flow
    to: END
  - from: fail_path
    to: END
```

## When to use semantic vs deterministic gates

Use deterministic gates first when requirements are objective (exit code, file presence, string match via `grep`).

Use a semantic LLM gate when the decision requires interpretation: correctness of intent, quality of reasoning, policy alignment, tone fit, or factual sufficiency. In practice, use both: deterministic checks for hard constraints, semantic gate for meaning.

## Composition guidance

1. **Chaining gates:** run multiple semantic gates in sequence (for example relevance -> correctness -> policy) and stop on the first fail.
2. **Fail-path fallback:** route `fail` to a fallback branch that revises input, asks for clarification, or triggers a human review interrupt.
3. **Retry behavior:** keep retry semantics at the LLM evaluation node (for transient model/provider issues), not in router logic. The router should only route on `verdict`.
