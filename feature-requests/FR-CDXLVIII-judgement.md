# Judgement — FR-448 Agent Node Structured Output via Prompt Schema

**Verdict:** AMEND
**Classification:** framework_primitive
**Judged:** 2026-05-22

## Summary

The core insight is correct: agent nodes bypass `execute_prompt()` and lose structured output. The scope is minimal (one file) and the problem is real (FR-447 demo confirmed). Five issues must be resolved before approval.

## Issues

### 1. Missing second exit path (max-iterations)

The FR only addresses the "no tool calls" exit (line 292) but ignores the max-iterations exit (line 365), which also returns `_normalize_content(last_content)`. Both paths must apply structured output.

The max-iterations path has a wrinkle: the last message may be a `ToolMessage`, not an `AIMessage` with the agent's reasoning. The structured output call there needs the full conversation context anyway, so the same approach works — but it must be explicit in the implementation plan.

### 2. Extra LLM call cost — evaluate try-parse-first

The proposed solution makes a full additional LLM invocation with the entire agent conversation. For a judge agent with 4 iterations and thousands of tokens of tool output, this doubles the output cost and adds significant latency.

**Cheaper alternative not explored:** Try `model_validate_json()` on the existing text response first. Many models produce parseable JSON when the prompt schema is present. Only fall back to the structured output LLM call if parsing fails. This is the `parse_json` pattern already used by LLM nodes.

### 3. `get_output_model_for_node` signature mismatch

Pseudocode shows `get_output_model_for_node(node_config, prompt_config, ...)` but actual signature is `get_output_model_for_node(node_config, prompts_dir, graph_path, prompts_relative)`. Fix the pseudocode.

### 4. `llm_base` undefined

The agent closure only has `llm` (tools bound via `create_llm(...).bind_tools(lc_tools)`). The proposed `llm_base` doesn't exist. Must either:
- Save the base LLM reference before calling `bind_tools`, or
- Create a separate `create_llm()` call for the structured output path

This must be explicit in the implementation approach.

### 5. REQ-YG-XXX placeholder

Acceptance criteria say `@pytest.mark.req("REQ-YG-XXX")`. Assign REQ-YG-409. Create a CAP YAML file.

## What's Good

- Problem statement precise with exact line references (292, 365)
- Root cause correctly identified — agent loop bypasses `execute_prompt()`
- Scope minimal — one file changed
- "Files NOT changed" section correctly identifies no regression risk
- Dependency on `get_output_model_for_node()` correctly identified

## Required Amendments

1. Add max-iterations exit path to scope
2. Evaluate try-parse-first approach (`model_validate_json`) before LLM re-invocation
3. Fix `get_output_model_for_node` signature in pseudocode
4. Clarify `llm_base` — how it's obtained (save pre-bind reference)
5. Assign REQ-YG-409 and create CAP YAML
