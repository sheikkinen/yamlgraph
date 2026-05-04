# Feature Request: FR-323 Vertex Gemini 3.1 hello smoke coverage

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-04

## Judge Verdict: APPROVE

**Analysis:**

1. **Scope clear and minimal:** ✓ Focused only on smoke testing two specific models (Gemini 3.1 Pro/Flash) with hello graph
2. **No contradictions/ambiguities:** ✓ Clear scope boundaries, explicit out-of-scope items
3. **Acceptance criteria measurable:** ✓ Each AC has concrete verification (tests exist, pass, use Express mode, docs updated)
4. **Implementation approach feasible:** ✓ Follows existing integration test patterns from test_providers.py and test_thinking_budget_integration.py
5. **Aligns with architecture:** ✓ Uses established graph_loader.load_graph_config + compile_graph pattern; no new abstractions needed
6. **Single responsibility:** ✓ Pure smoke validation scope - no CLI changes, no auth refactoring, no performance benchmarking
7. **Classification:** **Contrib/example** - 1 specific use case (GitHub #323 request), existing abstractions have small gaps (Express mode coverage for new models)
8. **Acceptance tests compile and fail correctly:** ✓ Tests import successfully, 3 skip (no VERTEX_API_KEY), 1 fails on missing docs (expected)

**Scope frozen.** Authority granted to implement.

## Summary

Add focused integration smoke coverage for `examples/demos/hello/graph.yaml` on `provider: vertex` with Gemini 3.1 Pro and Gemini 3.1 Flash, and document the verified model-name variants needed in project `scp-tenant-dps-dev` when using `VERTEX_API_KEY` (Express mode).

## Value Statement

YAMLGraph maintainers get a repeatable, test-backed proof that newly available Vertex Gemini 3.1 models work in the canonical hello flow, reducing release risk from unverified provider/model combinations.

## Problem

GitHub issue #323 requests explicit smoke validation for Vertex Gemini 3.1 Pro/Flash using:

```bash
yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --var style="holy see of code" --full
```

Current coverage does not fully satisfy that ask:

1. `tests/integration/test_providers.py` only has a generic Vertex execution test and gates on `GOOGLE_CLOUD_PROJECT` (ADC), not Express-mode `VERTEX_API_KEY`.
2. Existing Vertex integration coverage targets prior models (for example, `gemini-2.5-flash` in `tests/integration/test_thinking_budget_integration.py`), not Gemini 3.1 Pro/Flash.
3. Repository docs do not currently record Gemini 3.1 naming differences (for example `gemini-3.1-pro` vs `gemini-3.1-pro-001`) discovered during smoke runs.
4. `yamlgraph graph run` does not expose direct `--provider` / `--model` flags; this smoke path relies on environment-level provider/model selection and should be documented for reproducibility.

## Research: Existing Patterns and Prior Art

1. **Vertex provider support exists and is stable.**
   - FR-213 introduced `provider: vertex`.
   - `yamlgraph/utils/llm_factory.py` includes `"vertex"` in `ProviderType` and dispatches through `_create_vertex_llm`.

2. **Vertex Express mode already exists.**
   - FR-226 introduced `VERTEX_API_KEY` branch.
   - FR-227 and FR-229 hardened env masking behavior in `_create_vertex_llm`.
   - This FR should validate those paths against the new Gemini 3.1 models, not redesign auth.

3. **No dedicated hello-demo Gemini 3.1 smoke test currently exists.**
   - The canonical hello demo graph is present (`examples/demos/hello/graph.yaml`) and is already used as a smoke baseline in docs, but not yet for this model pair.

4. **Topic source file missing in worktree.**
   - Requested source `.chaplain/processing/gh-323.md` is absent in this branch.
   - Canonical source used for planning: GitHub issue #323.

## Objectives

1. Add explicit integration coverage for hello graph on Vertex Gemini 3.1 Pro.
2. Add explicit integration coverage for hello graph on Vertex Gemini 3.1 Flash.
3. Capture and document verified model-name variants and the exact Express-mode env setup used for the smoke.

## Constraints

1. Keep scope to smoke validation and documentation only.
2. Do not change provider factory behavior or auth logic in `llm_factory` for this FR.
3. Do not add new CLI flags (`--provider`, `--model`) in this FR.
4. Tests must be gated for environments without required Vertex credentials.

## Proposed Solution

### In scope

1. Add a dedicated integration test file:
   - `tests/integration/test_fr323_vertex_gemini31_hello_smoke.py`
2. Implement two model-specific smoke tests using hello demo inputs:
   - one for Gemini 3.1 Pro,
   - one for Gemini 3.1 Flash.
3. Run through Vertex Express mode (`VERTEX_API_KEY`) by setting env for provider/model selection during test execution.
4. Document validated model naming (including any required `-001` suffix variants) in hello demo documentation so operators can reproduce the smoke exactly.

### Out of scope

1. Any changes to `yamlgraph graph run` argument surface.
2. Any refactor of Vertex auth/masking internals (already covered by FR-226/227/229).
3. Performance benchmarking or race-node comparisons.

## Acceptance Criteria

- [x] **AC-01:** Integration test exists for hello graph with Vertex Gemini 3.1 Pro and passes when required credentials are present.
- [x] **AC-02:** Integration test exists for hello graph with Vertex Gemini 3.1 Flash and passes when required credentials are present.
- [x] **AC-03:** Tests execute through Express mode (`VERTEX_API_KEY`) instead of ADC-only gating.
- [x] **AC-04:** Documentation records the verified model identifiers used for Pro/Flash (including any `-001` variant differences if observed).
- [x] **AC-05:** Existing Vertex provider tests remain unchanged in behavior; this FR only adds focused coverage/docs.

## Failing Acceptance Tests (RED)

Create:

- `tests/integration/test_fr323_vertex_gemini31_hello_smoke.py`

Planned test cases:

1. `test_ac01_hello_graph_runs_with_vertex_gemini31_pro`
2. `test_ac02_hello_graph_runs_with_vertex_gemini31_flash`
3. `test_ac03_hello_vertex_smoke_uses_vertex_api_key_gate`
4. `test_ac04_hello_docs_capture_verified_gemini31_model_names`

RED commands (expected to fail before implementation):

```bash
pytest tests/integration/test_fr323_vertex_gemini31_hello_smoke.py -q --no-cov
rg -n "gemini-3\.1-(pro|flash)(-001)?" examples/demos/hello/README.md
```

## Alternatives Considered

1. **Rely on existing generic provider integration tests only**
   Rejected: does not prove Gemini 3.1 Pro/Flash specifically, nor Express-mode reproducibility for the hello smoke scenario.

2. **Add only documentation without executable tests**
   Rejected: issue asks for smoke verification; docs alone are not sufficient evidence.

3. **Expand to new CLI flags for provider/model override**
   Rejected: valid future usability enhancement, but not required for this smoke-validation scope.

## Related

- GitHub issue #323: <https://github.com/sheikkinen/yamlgraph/issues/323>
- `examples/demos/hello/graph.yaml`
- `examples/demos/hello/README.md`
- `tests/integration/test_providers.py`
- `tests/integration/test_thinking_budget_integration.py`
- `yamlgraph/utils/llm_factory.py`
- `feature-requests/FR-213-vertex-ai-provider.md`
- `feature-requests/FR-226-vertex-express-api-key-auth.md`
- `feature-requests/FR-227-vertex-express-env-var-masking.md`
- `feature-requests/FR-229-vertex-express-mask-google-api-key.md`
- Topic source requested: `.chaplain/processing/gh-323.md` (not present in this worktree)
