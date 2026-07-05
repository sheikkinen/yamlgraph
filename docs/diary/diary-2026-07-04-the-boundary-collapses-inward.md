# Diary — 2026-07-04 — The Boundary Collapses Inward

## Context
Enforced FR-683, FR-684, FR-685 — a trio that moves validation and dedup
from Python hacks to YAML graph-tools, completing the graph-as-tool
integration (FR-658) for the novel_fandom pipeline.

## What Happened
Three FRs enforced in one session:

1. **FR-683**: Extracted `validate_referential_integrity` from `persist_genesis.py`
   into `ref_integrity.py`. Created `ref_check.yaml` graph-tool. Deleted
   `validate_genesis.py` — the importlib hack that loaded validation from
   persist_genesis via dynamic import.

2. **FR-685**: Added gate→route→fix loop to genesis. Conditional edge after
   `validate`: valid→persist, invalid→`fix_stubs` (LLM)→validate. Loop limit 3.
   Happy path stays at 2 LLM calls; each repair round adds exactly 1.

3. **FR-684**: Created `semantic_dedup.yaml` graph-tool with LLM prompt
   (includes ulf/ulfs false positive as negative example). Rewired worldgen:
   dedup→router (threshold 5)→semantic_dedup subgraph→apply_merge→create_skeletons.
   Registered `dedup_check` for deepen_events agent. Removed `_LLM_DEDUP_THRESHOLD`
   and TODO stub from `dedup_entities.py`.

## Cognitive Trap: tool_call vs subgraph
Initially reached for `type: tool_call` to invoke the semantic_dedup graph-tool
from a worldgen node. But `tool_call` resolves tool name dynamically from state
(designed for LLM-driven dispatch), not for static composition. `type: subgraph`
with `input_mapping`/`output_mapping` is the correct pattern for deterministic
graph composition. The FR's amended AC-3 said "tool_call" but the underlying
need was "invoke a child graph with mapped state" — which is exactly what
subgraph does.

**Heuristic**: When the tool name is known at author time, use `subgraph`.
When the tool name comes from LLM output at runtime, use `tool_call`.

## Trap: Existing tests as contracts
The trilogy test `test_genesis_has_two_llm_nodes` hardcoded `["stubs", "synopsis"]`.
Adding `fix_stubs` broke it. The test was asserting implementation shape (exactly N
LLM nodes) rather than capability (happy path uses 2 LLM calls). Updated to assert
the full set including the repair node.

## Observation: importlib elimination
`validate_genesis.py` existed only because `persist_genesis.py` couldn't be
imported normally (loaded via `spec_from_file_location`). FR-683 replaced it
with a `sys.path.insert` shim + direct import. The importlib chain
(persist_genesis → validate_genesis → persist_genesis) was a Rube Goldberg
machine for a sibling import. The fix is 3 lines of sys.path manipulation.

## Seed
Can the `sys.path.insert` shim pattern be automated? Every Python tool loaded
via `spec_from_file_location` that needs sibling imports has the same problem.
A `__init_path__` hook in the tool loader could add the tool's directory to
`sys.path` before execution, eliminating the per-file shim.
