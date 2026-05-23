## Verdict: FR-448 — Agent Node Structured Output via Prompt Schema

---

### Evidence Summary

| Source | Key Finding |
|---|---|
| `agent.py` (lines 1–100) | Imports confirm `create_llm`, `load_prompt`, `_normalize_content` are already in scope. No `get_output_model_for_node` import. `llm` is created via `create_llm()` before `bind_tools` — `llm_base` can be saved at that point. |
| `executor.py` (lines 1–100) | `execute_prompt` already accepts `output_model: type[T] \| None` and routes to `with_structured_output`. Pattern is proven and reusable. |
| `node_factory/base.py` (full) | `get_output_model_for_node(node_config, prompts_dir, graph_path, prompts_relative)` is confirmed — 4-arg signature, not the 2-arg pseudocode shown in the FR. |
| Architecture doc | Area 5 "Tool & Agent Integration" (REQ-YG-017–020) owns this. Area 3 "Node Execution" and Area 4 "Prompt Execution" already cover `with_structured_output` for LLM nodes. |
| FR overlap search | No existing FR covers structured output for agent nodes. `FR-447` is the driving use case. `FR-CDXLVIII-judgement.md` appears to be a related but distinct filing. |
| `docs/plan-dogfood-chaplain.md` | Referenced but not read (not cited as a file to evaluate); chaplain Phase 2 is a second downstream consumer, confirming multi-use-case reach. |

---

### Criterion-by-Criterion Evaluation

---

#### 1. Scope — Clear and Minimal?
**FAIL**

The core change is small and well-scoped (one new branch in the final-iteration return path of `agent.py`). However, the FR simultaneously proposes **two mutually exclusive implementation strategies** (re-invoke with `with_structured_output` vs. try-parse-first) without committing to one. The "proposed solution" pseudocode uses one approach; the "alternative" section describes another; the Judge Notes then recommend a third hybrid (try-parse-first, fall back to re-invoke). The implementer arrives at the file with three competing designs and no authoritative choice. The scope of *what to build* is unclear until that decision is locked.

---

#### 2. Contradictions or Ambiguities?
**FAIL**

Four concrete contradictions/ambiguities exist:

| # | Issue | Detail |
|---|---|---|
| A | `get_output_model_for_node` signature | Pseudocode shows `(node_config, prompt_config, ...)`. Actual signature confirmed in `base.py`: `(node_config, prompts_dir, graph_path, prompts_relative)`. Misleads the implementer. |
| B | `llm_base` undefined | The FR says "save the base LLM reference before calling `bind_tools`" in Judge Notes, but the proposed solution code block uses `llm_base` as if it already exists. The agent module does call `create_llm()` first — but this must be made explicit in the implementation approach, not left as a note. |
| C | Max-iterations exit path | Line 365 is flagged in Judge Notes as a second exit path returning text, but the "Proposed Solution" code block only addresses the `not response.tool_calls` path. The criterion "Agent node returns `dict` when prompt has `schema:`" is unachievable without fixing both paths. |
| D | `REQ-YG-XXX` placeholder | Judge Notes assign REQ-YG-409 but the acceptance criteria still say `REQ-YG-XXX`. The CAP YAML is mentioned but not provided. The FR is marked **Amend** precisely because of these issues, yet they remain open. |

---

#### 3. Acceptance Criteria — Measurable?
**PARTIAL PASS**

Three of the five criteria are measurable as written:
- ✅ "returns `dict` (not `str`) when prompt has `schema:`" — `isinstance(result, dict)` is assertable.
- ✅ "returned dict matches the Pydantic model" — `Model(**result)` raises or doesn't.
- ✅ "nodes without `schema:` continue to return text" — regression test is straightforward.

Two are not fully measurable:
- ⚠️ "FR-447 judge demo produces structured `JudgeVerdict` dict when re-run" — integration test is valid but FR-447 must be merged first; this creates an ordering dependency not captured in the criteria.
- ❌ "Tests added with `@pytest.mark.req("REQ-YG-XXX")`" — placeholder REQ ID means the test cannot be written in its final form. A test with a placeholder marker will either fail the marker enforcement check or be written incorrectly.

---

#### 4. Implementation Approach — Feasible?
**PASS** *(with caveats)*

The mechanical change is straightforward and the architecture supports it:
- `get_output_model_for_node` already exists and already handles inline `schema:` blocks.
- `with_structured_output` is already used in `executor.py`; the pattern is proven.
- `bind_tools` and `with_structured_output` mutual exclusivity is correctly identified — the solution of using `llm_base` is the right fix.
- The try-parse-first optimization (Judge Notes item 2) is also architecturally sound and consistent with the `parse_json` pattern elsewhere.

The caveats are:
1. Both exit paths (`not response.tool_calls` at line 292 and max-iterations at line 365) must be addressed. The max-iterations path may have a `ToolMessage` as the last message — the structured call must be constructed from the conversation history, not the last message alone. This is non-trivial and not addressed in the pseudocode.
2. The `llm_base` variable must be explicitly saved before `bind_tools` in the agent factory closure. The FR notes this but the pseudocode does not reflect it.

---

#### 5. Architecture Alignment?
**PASS**

Strongly aligned:
- Sits squarely in **Area 5: Tool & Agent Integration** (REQ-YG-017–020).
- Reuses `get_output_model_for_node` from `node_factory/base.py` — the correct shared utility.
- Mirrors the `with_structured_output` pattern from `executor.py` lines 161–162 — no new pattern introduced.
- Explicitly lists files **not** changed (no scope creep into `executor.py`, `node_factory/base.py`, or existing demos).
- Chaplain Phase 2 and FR-447 are independent consumers — this is not a one-off patch.

---

#### 6. Single Responsibility?
**PASS**

The FR does one thing: extend the agent's final-iteration return path to honour the prompt's `schema:` block. It does not:
- Change how schemas are defined (that's `schema_loader`).
- Change how LLM nodes resolve structured output (that's `executor.py`).
- Change routing or FSM logic (those are downstream consumers, not part of this change).

The bundling of "try-parse-first vs. re-invoke" is a design decision within the same concern, not an orthogonal concern. The responsibility boundary is clean.

---

#### 7. Strategic Classification
**Framework Primitive** ✅ — *confirmed, with evidence*

Three independent consumers are on record:
1. **FR-447 judge demo** (`JudgeVerdict` schema, FSM event routing).
2. **Chaplain Phase 2** (`docs/plan-dogfood-chaplain.md` — structured dict for event routing).
3. **Any future agent node** that defines a `schema:` block — this is a general capability gap, not a one-off.

No existing abstraction covers this: `execute_prompt` handles LLM nodes; agent nodes bypass it entirely. The gap is real, confirmed by reading `agent.py` line 292. Classification as **framework primitive** is correct.

---

#### 8. Acceptance Tests — Compile and Fail for the Right Reasons?
**FAIL**

No acceptance test code is provided in the FR — only a checklist and a note that "unit test with mock LLM verifying dict vs text output" is needed. This means:

- There is nothing to verify compiles.
- There is nothing to verify fails before the fix and passes after.
- The `@pytest.mark.req("REQ-YG-XXX")` placeholder would cause the requirement-enforcement test (`tests/unit/test_requirement_enforcement`) to reject the test or match the wrong requirement.
- The max-iterations exit path has no proposed test at all.

---

### Overall Verdict

| Criterion | Result | Severity |
|---|---|---|
| 1. Scope clear and minimal | ❌ FAIL | Medium — three competing designs, no authoritative choice |
| 2. No contradictions / ambiguities | ❌ FAIL | High — signature mismatch, `llm_base` undefined in pseudocode, second exit path missing, placeholder REQ ID |
| 3. Acceptance criteria measurable | ⚠️ PARTIAL | Medium — 3/5 measurable; REQ placeholder and FR-447 ordering dependency block the rest |
| 4. Implementation feasible | ✅ PASS | — |
| 5. Architecture aligned | ✅ PASS | — |
| 6. Single responsibility | ✅ PASS | — |
| 7. Classification correct | ✅ Framework Primitive | — |
| 8. Acceptance tests compile/fail correctly | ❌ FAIL | High — no test code provided; placeholder marker; second exit path untested |

---

### Decision: **AMEND** (status correctly set; not ready to implement)

The problem is real, the classification is correct, and the architecture supports the solution. The FR is blocked on four concrete defects that must be resolved before implementation begins:

**Required amendments before approval:**

1. **Commit to one implementation strategy.** Choose: *(a)* try `model_validate_json()` on existing response, fall back to `with_structured_output` re-invoke; or *(b)* always re-invoke. Remove the alternative section or demote it to a footnote. The pseudocode must reflect the chosen path.

2. **Fix the `get_output_model_for_node` pseudocode signature** to match the actual 4-arg form: `(node_config, prompts_dir, graph_path, prompts_relative)`. Show where `prompts_dir` and `graph_path` come from inside the agent closure.

3. **Fix the `llm_base` pseudocode.** Show the line `llm_base = create_llm(...)` before `llm = llm_base.bind_tools(tools)` in the agent factory, and use `llm_base` in the structured output call.

4. **Address the max-iterations exit path (line 365) explicitly** in the proposed solution — not just in Judge Notes. Include it in the pseudocode and add a dedicated acceptance criterion and test case for it.

5. **Assign REQ-YG-409** everywhere (acceptance criteria marker, CAP YAML stub). The CAP YAML must be committed alongside the implementation, not left as a note.

6. **Provide skeleton acceptance test code** — even a 10-line mock-LLM unit test that asserts `isinstance(result[state_key], dict)` — so the test can be verified to fail before the fix.
