# Diary: FR-673 + FR-674 + FR-676 — Three FRs, interleaved enforcement

**Date:** 2026-07-03
**FRs:** FR-673, FR-674, FR-676
**Duration:** ~45 min enforcement

## What happened

Enforced three FRs in one pass, interleaving FR-674 (module split) when FR-673's field additions pushed `graph_schema.py` to 531 lines — 81 over the ceiling.

**FR-676** (async retry parity): Added retry loop with `asyncio.sleep` backoff and FR-464 structured-output fallback to `invoke_async`. Moved `_build_schema_hint` from `executor.py` to `executor_base.py` (shared, no layer violation). Three RED tests, all GREEN.

**FR-673** (extra=forbid on NodeConfig): Added 20+ missing fields covering all node types (interrupt, passthrough, python, subgraph, map limits, tool call). Changed `extra="allow"` to `extra="forbid"`. Added `validate_graph_schema()` call to `validate_config()` so Pydantic validates at load time, not just in CLI lint. Fixed cost-router `set:` → `output:` (was silently ignored — exactly the bug class this FR targets).

**FR-674** (module split): Extracted `CacheConfig`, `VerificationConfig`, `GuardConfig` + rule classes to `models/guard_schema.py` (110 lines). Updated 3 importers directly — no re-exports.

## Cognitive trap encountered

**partial_remediation**: The `extra="forbid"` change required a complete field audit — not just the 5 obvious missing fields from the subagent's first pass. The systematic audit (grep all `.get()` in node factories + python scan of all graph YAML files) found 11 more including `max_items` (34 uses!), `max_retries`, `tool_results_key`. Without the full audit, 34 graphs would have broken.

**gate_checks_shape_not_substance**: Adding `validate_graph_schema()` to `validate_config()` was essential. The Pydantic schema existed but was only called from CLI `validate`/`lint` — not from the load path. The gate existed but wasn't in the critical path.

## Insight

The interleaved enforcement pattern worked well: FR-674 split was triggered by FR-673's bloat, not scheduled separately. The split was a 5-minute mechanical extraction once the seam was obvious. One commit for all three FRs keeps the history coherent — each FR's tests prove its claims, the commit proves they compose.

The cost-router `set:` bug is the poster child for `extra="forbid"`: a passthrough node with `set:` instead of `output:` silently did nothing. The graph appeared to work because downstream nodes didn't depend on `provider_used` being set.

## Seed

Now that NodeConfig validates all keys, could the linter's node-key checks be retired? They're now redundant with load-time validation. Or do they add value beyond what Pydantic catches (e.g., semantic checks like "map node shouldn't have prompt")?
