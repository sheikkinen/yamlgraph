# FR-624: Bump LangGraph Floor to ≥1.2.0

**Status:** Judged ✅
**Priority:** Low
**Type:** Chore (dependency hygiene)
**Effort:** 0.5 day
**Requested:** 2026-06-30
**Judged:** 2026-06-30

## Problem

`pyproject.toml` pins `langgraph>=0.2.0` — a floor set over a year ago. The installed version is 1.0.5, and latest is 1.2.7. The gap between floor and reality means:

1. **CI could regress to ancient versions** on a clean install if pip resolves differently.
2. **We can't rely on 1.x features** without checking at runtime (DeltaChannel fixes, subgraph checkpoint_ns inheritance, stream abort cancellation).
3. **Security patches** in transitive deps (cryptography, tornado, jupyter-server) are only pulled by newer langgraph releases.

## Relevant Fixes in LangGraph 1.0–1.2.7

| Version | Fix/Feature | Impact on YAMLGraph |
|---|---|---|
| 1.2.7 | `DeltaChannel` overwrite supersteps snapshot fix | Affects checkpointed graphs with state annotations |
| 1.2.7 | `Overwrite` survives JSON roundtrips | Correctness for serialized state |
| 1.2.6 | Nested subgraph inherits parent `checkpoint_ns` | FR-030 subgraph support correctness |
| 1.2.6 | Cancel running subgraphs on v3 stream abort | Streaming cleanup |
| 1.2.5 | `updateState` bug for deltaChannel on empty thread | Edge case fix for fresh threads |
| 1.2.3 | `lc_agent_name` on tool-dispatched subagents | Better LangSmith traces |
| 1.2.3 | v3 streaming + WebSocket transport for RemoteGraph | Future MCP/remote graph support |
| 1.2.3 | `ensure_config` merge for callbacks/tags/metadata | Prevents config loss in nested invocations |

## Proposal

1. Bump `langgraph>=1.2.0` in `pyproject.toml`
2. Bump `langgraph-checkpoint-sqlite>=2.0.0` (already correct, verify compatibility)
3. Bump `langgraph-checkpoint-redis>=0.3.0` (already correct, verify compatibility)
4. Run full test suite against 1.2.7
5. Verify installed version in dev venv matches (currently 1.0.5 — needs `pip install -U`)

## Constraints

1. No breaking changes — LangGraph 1.x follows semver; 0.2→1.2 crossed one major but LangGraph's 1.0 was API-stable.
2. Do not pin upper bound. `>=1.2.0` not `>=1.2.0,<2.0.0`.
3. Partner packages (`langchain-anthropic`, `langchain-openai`, etc.) may need corresponding bumps if they declare `langgraph-checkpoint` peer deps.

## Acceptance Criteria

- [ ] `pyproject.toml` declares `langgraph>=1.2.0`.
- [ ] `pip install -e ".[dev]"` resolves to ≥1.2.7 in clean venv.
- [ ] `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` passes.
- [ ] `pytest tests/integration/ -v` passes (if API keys available).
- [ ] No new deprecation warnings from langgraph in test output.

## Related

- FR-030: Subgraph support (benefits from checkpoint_ns fix in 1.2.6)
- FR-131: Prompt caching (benefits from langchain-core version tracking metadata)
- CAP-07: State persistence (DeltaChannel/Overwrite fixes in 1.2.7)

---

## Judgement

**Authority: GRANTED.**

### Assessment

The FR is clear, minimal, and well-scoped. Bumping a dependency floor from 0.2.0 to 1.2.0 when the installed version is already 1.1.6 is pure hygiene — the actual behavioral risk is only the delta from 1.1.6 to 1.2.x, not the full 0.2→1.2 span.

### Corrections

1. **Installed version is 1.1.6**, not 1.0.5 as stated. The real risk surface is narrower than described — only 1.1.6→1.2.x needs verification, not 1.0.5→1.2.7.

### Constraints Accepted

- No upper bound pin. Correct for a project that tracks upstream actively.
- No partner package bumps unless forced by resolver conflict.
- The "no breaking changes" claim is valid for 1.1.6→1.2.x (same major, semver-stable).

### Scope Freeze

- Bump `langgraph>=1.2.0` in `pyproject.toml`.
- Verify test suite passes after `pip install -U langgraph`.
- Do NOT refactor code to use new 1.2.x features in this FR — that's separate work.
- Do NOT add runtime version checks or feature gates.

### Enforcement Order

1. Bump version floor in `pyproject.toml`.
2. `pip install -U langgraph` in dev venv.
3. Run `pytest tests/unit/ -q --no-cov -m "not slow" -n auto`.
4. Check for new deprecation warnings (`pytest ... -W error::DeprecationWarning` or grep output).
5. If green, commit. If red, diagnose and fix within scope (adapter changes only, no new features).
