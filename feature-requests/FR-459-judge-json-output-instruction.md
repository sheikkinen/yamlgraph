# Feature Request: Judge demo JSON output instruction for DeepSeek

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-05-24

## Summary

DeepSeek rejects `response_format` in `with_structured_output()` and the FR-456 JSON fallback only works when the agent's final message contains embedded JSON. DeepSeek's agent produces prose verdicts with no JSON, so the fallback has nothing to parse. Add a prompt instruction telling the agent to include its verdict as JSON in the final message.

## Value Statement

The judge demo works on DeepSeek without relying on `with_structured_output()` API support.

## Problem

FR-456 added a fallback path: when `with_structured_output()` fails and `extract_json` found a dict in the agent's last message, use `model_construct()` for lenient parsing. But DeepSeek's agent writes its verdict as natural language prose — no JSON block — so `extract_json` returns None and the fallback re-raises.

From eval stderr:
```
✓ Agent completed after 7 iterations
HTTP Request: POST https://api.deepseek.com/v1/chat/completions "HTTP/1.1 400 Bad Request"
❌ Error: Error code: 400 - {'error': {'message': 'This response_format type is unavailable now'}}
```

The agent did the analysis (7 iterations, read files, searched code) but never formatted its verdict as JSON.

## Proposed Solution

In `examples/demos/judge/prompts/judge.yaml`, add an explicit instruction in the system prompt telling the agent to output its final verdict as a JSON block matching the schema. This ensures `extract_json` finds the data before the `with_structured_output()` re-invoke is attempted.

```yaml
system: |
  ...existing instructions...

  IMPORTANT: When you have completed your analysis, your final message MUST
  contain a JSON code block with your verdict matching this exact structure:
  ```json
  {
    "verdict": "APPROVE|AMEND|REJECT|SPLIT",
    "classification": "framework_primitive|contrib_example|pattern_documentation|reject",
    "reasoning": "...",
    "criteria_results": [{"criterion": "...", "passed": true, "note": "..."}],
    "issues": []
  }
  ```
```

This is DeepSeek-specific in effect but benefits all models — the cheap `extract_json` path avoids the expensive `with_structured_output()` re-invoke entirely.

## Acceptance Criteria

- [ ] Judge prompt includes JSON output instruction
- [ ] DeepSeek eval produces a valid verdict JSON
- [ ] Other models still work (no regression)
- [ ] Demo output log updated

## Alternatives Considered

- Provider-specific prompt injection at runtime — over-engineered for a demo prompt.
- Force all agents to output JSON — too prescriptive for general agent nodes.

## Related

- FR-456: Structured output JSON fallback (the fallback mechanism this feeds into)
- FR-458: OpenAI strict schema (sibling eval fix)
- `examples/demos/judge/prompts/judge.yaml`: target file
- `examples/demos/judge/eval.sh`: verification harness
