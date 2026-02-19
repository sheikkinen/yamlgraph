# Feature Request: Inline LLM Lint Check

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** COMPLETE
**Effort:** 0.25 days
**Requested:** 2026-02-19
**Implemented:** 2026-02-19

## Implementation (2026-02-19)

**Files created:**
- `scripts/lint_inline_llm.py` (~180 lines) — scanner with import parsing
- `scripts/__init__.py` — module marker for test imports
- `tests/unit/test_lint_inline_llm.py` — 10 tests covering all detection cases

**Files modified:**
- `.pre-commit-config.yaml` — added `inline-llm-check` hook
- `ARCHITECTURE.md` — added CAP-22 and REQ-YG-073
- `scripts/req_coverage.py` — extended ALL_REQS and added CAP-22

**Files deleted:**
- `scripts/spike_fr029_streaming.py` — obsolete FR-029 research
- `scripts/spike_subgraph_streaming.py` — obsolete FR-030 research

**Exclusions built in:**
- `examples/demos/` — demos showing low-level API usage
- `spike_` prefix — research spikes are temporary inline code

## Summary

Detect scripts with `def main()` that import LLM execution functions but NOT graph loading — the code smell of bypassing YAMLGraph's three-layer architecture.

## Problem

The three-layer architecture requires LLM orchestration to live in YAML graphs, not Python scripts. The actual problem is **inline LLM calls that should be graph nodes**, not the existence of `main()` functions.

From the FR-046 diary Seed: "when does a script graduate to a proper graph execution?"

**Answer:** When it has inline LLM calls. The detection should be automated, not a manual registry.

## Proposed Solution

A targeted lint script (~40 lines) that detects the specific smell:

```python
# scripts/lint_inline_llm.py

# For each .py file with `def main(` or `async def main(`:
#   Parse imports
#   LLM_IMPORTS = {execute_prompt, execute_prompt_streaming, ChatAnthropic,
#                  ChatOpenAI, create_llm, llm.invoke}
#   GRAPH_IMPORTS = {load_graph_config, compile_graph, load_and_compile}
#
#   If has LLM_IMPORTS AND NOT GRAPH_IMPORTS → FLAG
```

### Detection Logic

| Imports LLM? | Imports Graph Loader? | Verdict |
|--------------|----------------------|---------|
| ❌ No | ❌ No | ✅ OK — pure side-effect script |
| ❌ No | ✅ Yes | ✅ OK — graph runner |
| ✅ Yes | ✅ Yes | ✅ OK — graph runner with executor |
| ✅ Yes | ❌ No | ❌ FLAG — inline LLM, should be graph |

### Pre-commit Hook

```yaml
- id: inline-llm-check
  name: inline LLM orchestration check
  entry: python scripts/lint_inline_llm.py
  language: python
  types: [python]
  pass_filenames: false
```

## Acceptance Criteria

- [ ] `scripts/lint_inline_llm.py` scans for main functions
- [ ] Detects LLM imports without graph loader imports
- [ ] Pre-commit hook `inline-llm-check` added
- [ ] Exit code 1 if violations found, 0 otherwise
- [ ] `--verbose` flag shows all scanned files
- [ ] Tests: `tests/unit/test_lint_inline_llm.py` with REQ-YG-073

## What This Does NOT Do

- **No registry** — compliant mains don't need documentation
- **No categories** — binary check: smell or no smell
- **No manual audits** — automated detection at commit time

## Implementation Plan

1. Write test cases (RED):
   - File with main + execute_prompt → fail
   - File with main + load_graph_config → pass
   - File with main + both → pass
   - File with main + neither → pass
   - File without main → skip
2. Implement scanner (GREEN) — ~40 lines
3. Add pre-commit hook
4. Verify against current codebase (expect 0 violations)

## Expected Results

Current codebase should pass with 0 violations:
- All graph runners import `load_graph_config`/`compile_graph`
- All side-effect scripts don't import LLM functions
- The one violation (`scripts/diary_digest.py`) was already refactored in FR-046

## Related

- FR-046 diary entry Seed — origin of this question
- CLAUDE.md three-layer pattern — the design principle being enforced
- Rejected: FR-047 original (main registry) — over-engineered

## Judgment Note

Original FR-047 proposed a registry with 20+ MAIN-XXX entries for categorization. Rejected because:
- 95% noise (documenting compliant code)
- The smell is directly detectable
- Registry is maintenance burden

This revision detects the actual problem: inline LLM calls without graph execution.
