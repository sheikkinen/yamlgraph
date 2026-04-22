# Reflection: FR-266 Copilot Node Model Selection

**Date:** 2026-04-21
**FR:** FR-266
**Duration:** ~15 minutes

## What Happened

Activated 12 pre-committed RED acceptance tests for FR-266 (copilot node model selection). The implementation was a 3-file surgical change (~15 lines net) that applied the existing LLM node model resolution pattern to copilot nodes.

## Cognitive Trap: Feature Parity as Boundary Contract

The trap was already named in FR-252's diary entry: "Feature parity is a boundary contract." When `model:` works for LLM nodes but not copilot nodes, the inconsistency is a latent defect at the compile-time boundary. The fix was mechanical because the reference implementation already existed in `llm_nodes.py` — the pattern just needed to be applied at `node_compiler.py` where copilot nodes are compiled.

## Insight: Test Setup vs Test Contract

One acceptance test had a setup bug (missing `prompt` field for copilot NodeConfig validation) while the assertion was correct. The distinction between "test setup" and "test assertion contract" matters for RED-phase tests — a failing setup masks whether the assertion itself would fail, which is the whole point of RED.

## Heuristic

**Acceptance tests must fail on the assertion, not on setup.** A RED test that fails during construction proves nothing about the feature contract. Validate that RED tests fail on the _right line_ before considering them ready for the GREEN phase.

## Seed

Could the pre-commit `pytest` hook skip known-RED tests (marked with a `@pytest.mark.red` marker) to avoid blocking unrelated commits while preserving the RED phase contract in CI?
