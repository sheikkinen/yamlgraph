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

## Trap: Enforcement blind spot — forbid-terms scope
The `forbid-terms` pre-commit hook searches only `yamlgraph/*.py` for
`TODO|FIXME`. The FR-665 TODO stub lived at
`examples/novel_fandom/nodes/dedup_entities.py` — outside `yamlgraph/`,
invisible to the hook. Double loophole: wrong directory scope AND no YAML
coverage (graph comments could also carry deferred obligations).

The TODO survived from FR-665 enforcement through multiple commits until
FR-684 deleted it. The gate checked presence, not substance — a TODO is a
deferred obligation masquerading as a comment, and the enforcement perimeter
didn't extend to the code that actually uses YAMLGraph.

**Heuristic**: Enforcement hooks must cover the same perimeter as the code
they guard. `examples/` and `scripts/` contain production-grade Python and
YAML that obeys the same doctrine as `yamlgraph/`. A gate that only watches
the library directory is a fence around the garden but not the orchard.

Maps to: `gate_checks_shape_not_substance` + `infrastructure_self_exempt`.

## Trap: Missing docs as enabler of python-hack bypass
Genesis `validate` was wired as `type: python` calling `ref_integrity.py:ref_check`
directly — bypassing the `ref_check.yaml` graph-tool that FR-683 created. The
`type: graph` tool section exists in `reference/graph-yaml.md` (lines 1411-1455)
but describes only agent and tool_call as callers. No guidance exists for using
graph-tools from pipeline gate nodes, and no subgraph-vs-graph-tool decision
guide documents when each pattern applies.

`reference/tool-call-nodes.md` still claims "Only `type: python` tools are
currently supported" — stale since FR-658 enforcement.

The contributing chain: feature enforced → demo written → reference section added →
but no decision guide → implementer (me) defaults to `type: python` because the
docs frame graph-tool as agent-only → genesis validate becomes a python hack →
the very feature the trilogy was supposed to showcase goes unused.

Novel_fandom's value is as a showcase for core features. A `type: graph` tool
that's only exercised in a toy demo (`graph-tool/`) and never in the large-scale
example is a demo, not a proof. The genesis validate node must use graph composition
(subgraph or graph-tool), not shortcut around it.

**Heuristic**: When a feature has no decision guide ("when to use X vs Y"),
implementers default to the simpler pattern they already know. Missing docs
don't just leave a gap — they actively push code toward the legacy path.

Maps to: `detection_without_enforcement` — the feature was detected (exists in
reference) but not enforced (no guidance on when it's mandatory vs optional).

## Seed
Can the `sys.path.insert` shim pattern be automated? Every Python tool loaded
via `spec_from_file_location` that needs sibling imports has the same problem.
A `__init_path__` hook in the tool loader could add the tool's directory to
`sys.path` before execution, eliminating the per-file shim.
