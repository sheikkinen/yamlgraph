# Feature Request: Race Node parse_json and Content Normalization

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-21

## Summary

`type: race` nodes ignore `parse_json: true` and do not normalize list-shaped LLM content. The race winner's raw `AIMessage.content` is written into graph state, breaking downstream consumers that expect a parsed dict.

## Value Statement

Graph authors using `type: race` with `parse_json: true` get the same post-processing semantics as `type: llm`, preventing silent state corruption that currently hard-fails production voice calls.

## Problem

`race_node.py` (`_invoke_candidate`) returns `response.content` directly without any post-processing. Two problems:

1. **`parse_json` ignored**: `parse_json` is never read from `node_config`. The `extract_json()` step that `llm_nodes.py:404` applies is absent. A race node configured with `parse_json: true` writes raw JSON strings into state instead of parsed dicts.

2. **List-shaped content not normalized**: Anthropic Claude models return `AIMessage.content` as `list[ContentBlock]` (e.g., `[{"type": "text", "text": "..."}]`) rather than `str`. This list propagates into state, causing `NoneType`/`AttributeError` in downstream nodes that call `.get()` on the expected dict.

3. **`parse_json` / `output_model` mutual exclusion missing**: In `llm_nodes.py:95-97`, when `parse_json: true` the `output_model` is forced to `None` — structured output and `parse_json` are mutually exclusive. The race node resolves `output_model` unconditionally (line 97-102), so a config with both `parse_json: true` and a prompt-level schema would incorrectly use structured output instead of JSON extraction.

**Observed failure** (call `CA95fbb78c1a360c8d4fe3c07048684615`, 2026-04-21): Race winner was `anthropic/claude-haiku-4-5`. `state["extracted"]` received a list instead of a parsed dict. Downstream `detect_gaps` node called `.get()` on `None`, graph errored, Twilio disconnected the user ~9s after answering.

### Root cause

`race_node.py` does NOT mirror the LLM-node post-processing pipeline:

```python
# llm_nodes.py:95-97 (correct — mutual exclusion):
parse_json = node_config.get("parse_json", False)
if parse_json:
    output_model = None

# llm_nodes.py:404 (correct — post-processing):
if cfg.parse_json and isinstance(result, str):
    result = extract_json(result)

# race_node.py (missing):
# - No parse_json config read
# - No output_model mutual exclusion
# - No list-content normalization
# - No extract_json post-processing
```

The `_normalize_content` function in `tools/agent.py:27` (FR-059) solves the list-content case for agent nodes. Race nodes need the same treatment.

## Proposed Solution

In `yamlgraph/node_factory/race_node.py`:

### 1. Read `parse_json` from config and enforce mutual exclusion

Mirror `llm_nodes.py:95-97`:

```python
parse_json = node_config.get("parse_json", False)
if parse_json:
    output_model = None
else:
    output_model = get_output_model_for_node(...)
```

### 2. Normalize list-shaped content in `_invoke_candidate`

After `response = llm.invoke(messages); return response.content`, normalize list content to string:

```python
content = response.content
if isinstance(content, list):
    content = "".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in content
    )
return content
```

### 3. Apply `parse_json` after winning result

In the `as_completed` loop, after `result = future.result()`:

```python
if parse_json and isinstance(result, str):
    result = extract_json(result)
```

### 4. Treat post-processing failures as losses

If `extract_json` returns `str` when a dict was expected, the candidate loses — append to `errors`, continue to next `as_completed` future:

```python
try:
    result = future.result()
    if parse_json and isinstance(result, str):
        result = extract_json(result)
        if parse_json and isinstance(result, str):
            raise ValueError(f"parse_json: extract_json returned str, not dict: {result[:100]}")
    # ... cancel remaining, return winner
except Exception as e:
    errors.append((candidate, e))
```

### Integration points

| Component | Change |
|-----------|--------|
| `yamlgraph/node_factory/race_node.py` | Add content normalization + `parse_json` support + `output_model` mutual exclusion |
| `tests/unit/test_race_node.py` | Add 3 RED tests (see TDD below) |

No new modules, no new dependencies. Uses existing `extract_json` from `yamlgraph/utils/json_extract.py`.

## Acceptance Criteria

- [ ] `parse_json = node_config.get("parse_json", False)` read in `create_race_node`
- [ ] When `parse_json: true`, `output_model` forced to `None` (mutual exclusion, mirroring `llm_nodes.py:95-97`)
- [ ] List-shaped `AIMessage.content` (Anthropic content blocks) normalized to `str` before returning from `_invoke_candidate`
- [ ] When `parse_json: true`, `extract_json()` applied to winning result — output is `dict`, not `str`
- [ ] If `parse_json: true` and a candidate's result cannot be parsed to dict, that candidate loses (not returned as winner)
- [ ] Existing race node tests still pass (no regression)
- [ ] Tests added (3 new tests, see TDD section)
- [ ] REQ-YG-233 tagged on all new tests

## TDD

RED tests to add in `tests/unit/test_race_node.py`:

1. **`test_race_node_parse_json_string_result`** — Candidate returns a JSON string `'{"key": "value"}'`. With `parse_json: true`, race node returns `{"key": "value"}` (parsed dict).

2. **`test_race_node_parse_json_list_content`** — Candidate returns `[{"type": "text", "text": '{"key": "value"}'}]` (Anthropic content blocks). With `parse_json: true`, race node flattens to string, then parses to dict.

3. **`test_race_node_parse_json_invalid_candidate_loses`** — First candidate returns non-JSON string `"not json"`. Second candidate returns valid JSON `'{"key": "value"}'`. With `parse_json: true`, first candidate loses, second candidate wins with parsed dict.

## Alternatives Considered

### 1. Move `_normalize_content` to a shared utility

The `_normalize_content` function in `tools/agent.py` handles the same content-block flattening. We could extract it to `utils/` and import from both. However, the race node normalization is a 3-line inline operation scoped to `_invoke_candidate`. Extracting to a shared utility is a valid follow-up but not required for this fix — keeping scope minimal.

### 2. Normalize at the LLM factory level

Wrapping all LLM responses at the factory level would fix the problem globally. However, this violates the boundary principle: `create_llm` returns a LangChain LLM; response shape is a LangChain concern, and different node types may want different handling (e.g., agent nodes need the full content-block list for tool calls). Normalization belongs at the node level, not the provider level.

### 3. Require inline `schema:` for race nodes

Forcing all race nodes to use structured output (Pydantic model via `schema:` in prompt YAML) would bypass `parse_json` entirely. This is too restrictive — some prompts return free-form JSON that doesn't warrant a Pydantic model, and existing graphs use `parse_json: true` without inline schemas.

## Related

- **FR-232**: Race node type (parent feature, `race_node.py`)
- **FR-059**: Normalize agent `response.content` to string (same bug class for agent nodes)
- **REQ-YG-233**: Race node requirement in `ARCHITECTURE.md`
- `yamlgraph/node_factory/llm_nodes.py:95-97` — reference `parse_json` / `output_model` mutual exclusion
- `yamlgraph/node_factory/llm_nodes.py:404` — reference `parse_json` post-processing
- `yamlgraph/utils/json_extract.py` — `extract_json()` utility
- `yamlgraph/tools/agent.py:27` — `_normalize_content()` (FR-059 fix)
- Issue: [sheikkinen/yamlgraph#147](https://github.com/sheikkinen/yamlgraph/issues/147)

## Research Brief

### Competitive Landscape

No competing framework offers a built-in "first-wins race" primitive with response normalization:

| Framework | Parallel primitive | Semantics | Content normalization | JSON parse |
|-----------|-------------------|-----------|----------------------|------------|
| **LangGraph** | `add_edge([n1,n2], n3)` | Fan-in (wait ALL) | ❌ | ❌ |
| **LangChain** | `with_fallbacks()` | Sequential on error | ❌ | ❌ |
| **CrewAI** (49K★) | `async_execution=True` | Concurrent, not racing | ❌ | ❌ |
| **AutoGen** (57K★) | `GroupChat` | Message handoff | ❌ | ❌ |
| **OpenAI Agents SDK** | Agent handoff | Sequential | N/A (single provider) | ❌ |
| **Google ADK** | None | Sequential | N/A (Gemini only) | ❌ |
| **LiteLLM** (44K★) | Router fallback | Sequential on error | ✅ (all → OpenAI format) | ❌ |

**LiteLLM** normalizes all provider responses to OpenAI format (including Anthropic content blocks → string), but offers sequential fallback, not first-wins racing. Using LiteLLM at the provider layer would solve content normalization globally, but would require replacing `langchain-anthropic` / `langchain-google` with `litellm` as the LLM backend — a much larger change than this FR's scope.

**Verdict:** Documenting an existing solution is not an option — no framework solves this. The race primitive is unique to YAMLGraph. The fix is a 3-point gap-fill on an existing node type.

### Existing Abstractions

| Abstraction | Location | Overlap |
|-------------|----------|---------|
| `_normalize_content()` | `yamlgraph/tools/agent.py:27` | **Identical problem** — FR-059 fixed the same Anthropic content-block list bug for agent nodes. 3-line inline function. |
| `parse_json` + mutual exclusion | `yamlgraph/node_factory/llm_nodes.py:95-97` | **Exact pattern to mirror** — reads `parse_json`, forces `output_model = None`. |
| `parse_json` post-processing | `yamlgraph/node_factory/llm_nodes.py:404` | **Exact pattern to mirror** — `if cfg.parse_json and isinstance(result, str): result = extract_json(result)`. |
| `extract_json()` | `yamlgraph/utils/json_extract.py` | **Reusable utility** — already imported by `llm_nodes.py`. No new code needed. |
| `get_output_model_for_node()` | `yamlgraph/node_factory/base.py` | Already imported by `race_node.py` — just needs `parse_json` guard before the call. |

The fix reuses existing utilities (`extract_json`, `_normalize_content` pattern) and mirrors an existing pattern (`llm_nodes.py:95-97, 404`). No new abstractions required.

### Diary Precedents

1. **FR-059 reflection** (`docs/diary-2026-02-20.md`, `feature-requests/059-agent-normalize-content-to-string.md`) — **Same bug class.** Anthropic `AIMessage.content` as `list[ContentBlock]` broke agent nodes. Fixed with `_normalize_content()` in `tools/agent.py:27`. The race node is the second occurrence of this exact provider boundary trap.

2. **FR-232 reflection** (`docs/diary/2026-04-18-reflection-fr-232-race-node-type.md`) — Documents the `ThreadPoolExecutor` choice for sync-first codebase. Seed asks about streaming partial tokens. No mention of `parse_json` gap — the omission is the bug.

3. **FR-195 reflection** (`docs/diary/2026-03-13-reflection-fr-195.md`) — `extract_json` array-first search trap: when the result contains arrays inside objects, `extract_json` finds the array first. Relevant risk: if a `parse_json: true` race node returns JSON with nested arrays, `extract_json` may produce unexpected results. The existing `callsite_fix` cure applies — if this bites, fix at the race node caller, not the shared utility.

4. **Knowledge graph patterns** — `the_one_law` ("normalize at the boundary where external data enters") cited 30+ times in diary. The provider boundary (Anthropic list content) is the textbook case. `downstream_fix` trap (7/25 FR reflections) warns against guarding downstream of the symptom — the fix correctly normalizes in `_invoke_candidate` (the entry boundary), not in downstream consumers.

5. **`partial_remediation` trap** — FR-059 fixed agent nodes but left race nodes unfixed. This FR is the second occurrence. The diary pattern predicts this: "Fix all occurrences, not just cited one."

### Usage Evidence

- **Graphs using `type: race`:** 1 (`examples/demos/race/graph.yaml` — does NOT use `parse_json`)
- **Graphs using `parse_json`:** 6 YAML files across `examples/` (questionnaire, cost-router, tavily_rag, fi_domain_crawl)
- **Graphs in `graphs/` using race:** 0
- **Project graphs using race:** 0 in-repo (production `ninchat_voice` uses it externally — the failing caller)
- **Real-world use cases beyond proposal:**
  - Any multi-provider race node where the prompt returns free-form JSON (no inline `schema:`)
  - Any race node where Anthropic is a candidate (content-block list is deterministic on Claude models)
  - Voice/real-time pipelines where race latency matters and structured output adds latency overhead

### Classification Signal

- **Abstraction level:** primitive (bug fix on existing framework primitive CAP-91)
- **Recommended approach:** **build** — this is a gap-fill on an existing node type, not a new abstraction. The fix mirrors established patterns (`llm_nodes.py:95-97,404`) using existing utilities (`extract_json`). Estimated 0.5 days. Documenting a workaround is not viable — the caller cannot normalize after the race node returns, because the race node writes directly to `state_key`.
- **Key risk:** `extract_json` array-first search (FR-195 trap) could silently produce wrong results for JSON containing top-level arrays; mitigated by the "candidate loses on parse failure" semantics proposed in §4.
