# Diary: FR-449 Agent Structured Output Anthropic Bugfix

**Date:** 2026-05-24
**FR:** FR-449
**REQ:** REQ-YG-422

## Summary

Agent nodes with inline `schema:` blocks returned prose strings instead of
validated dicts when using Anthropic. Three bugs, one root cause family:
provider boundary normalization.

## Traps Encountered

### 1. Provider Boundary (the real bugs)

**Trap:** `downstream_fix` — symptoms manifested as "agent returns str" but
root cause was three boundary violations:

- **Content blocks:** Anthropic returns `response.content` as `list[dict]`
  (content blocks), not `str`. `extract_json()` crashed with
  `AttributeError: 'list' has no 'strip'` — swallowed by bare `except Exception`.
- **Assistant prefill:** Fallback `structured_llm.invoke(msgs)` fails when
  `msgs` ends with `AIMessage` — Anthropic rejects assistant-last conversations.
- **Schema mismatch:** LLM returns JSON with creative keys (`file_analysis`)
  instead of schema-defined keys (`summary`, `line_count`, `verdict`) —
  `model_validate` raises `ValidationError`, caught correctly, but only if
  the first two bugs are fixed.

**Cure:** Normalize at the boundary. `_normalize_content()` handles content
blocks. `HumanMessage` append before fallback invoke. Both applied at the
entry point of `_try_structured_output()`.

### 2. Stale Install (the phantom bug)

**Trap:** `recent_changes_blindness` — fix worked in unit tests and
programmatic invocation but CLI consistently returned `str`. Spent significant
time investigating: added debug prints, checked LangSmith traces (5 runs all
showing `str`), hypothesized about LangGraph error handling, `extract_json`
behavior, and `output_model` resolution.

**Root cause:** Package was installed as regular `pip install` (not `-e`).
Source edits invisible to CLI — Python loaded stale copy from `site-packages/`.
`inspect.getsource()` was misleading: it reads `.py` source but at runtime
the bytecode came from the installed copy.

**Cure:** `pip install -e ".[dev]"` — then all debug prints appeared, fix
confirmed immediately. `changelog_first_diagnostic` applies: should have
checked install mode as first diagnostic step.

**Heuristic candidate:** When source edits don't take effect at runtime,
check `pip show <pkg>` for `Editable project location` before investigating
the code. Absence of that field = stale install.

### 3. LangSmith as Diagnostic Tool

Checking LangSmith traces earlier would have revealed that zero fallback LLM
calls were being made (only 2 `ChatAnthropic` calls per run, never 3). This
would have immediately pointed to "the fix isn't being executed" rather than
"the fix is broken."

## Fixes Applied

1. `_normalize_content(content)` — joins Anthropic content blocks to str
2. `HumanMessage` append before fallback `structured_llm.invoke()`
3. Bare `except Exception` now logs via `logger.debug`

## Evidence

- **Unit tests:** 5 tests, RED without fix, GREEN with fix (0.10s)
- **E2E CLI:** `analysis: {'summary': '...', 'line_count': 324, 'verdict': 'medium'}`
- **LangSmith trace:** 3 LLM calls (tool request, response, fallback structured),
  `analysis=dict` with correct schema keys

**Seed:** When `inspect.getsource()` and runtime behavior disagree, the abstraction
layer between source and execution (bytecode cache, installed packages,
import hooks) is the suspect. Could a pre-flight check in the CLI detect
stale installs by comparing source mtime vs installed dist-info?
