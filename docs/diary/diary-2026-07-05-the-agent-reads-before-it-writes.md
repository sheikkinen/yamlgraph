# Diary — 2026-07-05 — The Agent Reads Before It Writes

## Context
FR-686 agent-first genesis and worldgen pipelines — first full end-to-end run on committed code.

## Observation

Two pipelines, same architecture (reload → agent → final_gate), radically different tool-call profiles:

| Metric | Genesis | Worldgen |
|--------|---------|----------|
| Iterations | 8 | 41 |
| Duration | ~4 min | ~5.5 min |
| New entities | 1 | 0 |
| Deepened entities | 0 | 21 |
| Tool calls | 17 | 63 |
| Gate result | FAIL (orphan `?`) | PASS |

Genesis was *fast* because the seed canon was already rich — it ran dedup_check 8 times, found everything existed, created one missing entity (ragnar), and declared done. Worldgen was *thorough* — it read 33 pages, wrote 24 deepened versions, and ran ref_check 3 times to verify integrity.

The ratio is revealing: **33 lookups for 24 deepens = 1.4 reads per write**. The agent reads the target entity, sometimes reads a neighbor for context, then writes. This is the agent analog of "measure twice, cut once."

## Trap: Generated Output Overwrites Test Fixtures

The genesis run wrote to `examples/novel_fandom/canon/`, the same directory that tests use as fixtures. When I `git add -A`, the LLM-generated content replaced the curated seed data, breaking 2 tests + causing 36 collection errors.

This is a variant of **workspace_is_not_boundary**: the canon directory serves two masters (test fixtures and pipeline output) without an ownership boundary. The fix was surgical — restore seed, don't commit genesis output — but the root cause is that generated artifacts and test fixtures share the same path.

## Trap: variables Section Only Works for Graph-Tools

The `variables:` section in YAML is injected as `default_variables` into graph-tool invocations (FR-686 fix). But for the top-level graph, the CLI ignores `variables:` entirely — it only reads `--var` args. Running genesis without `--var premise_file=...` failed with "premise_file variable not set" even though the YAML declared a default.

This is **inconsistent boundary behavior**: the same YAML key works at one level but not another. The fix is either: (a) CLI injects `variables:` as initial state defaults, or (b) documentation makes the asymmetry explicit.

## Heuristic

**generated_output_not_fixture**: If a pipeline writes to a directory that tests read from, one of them owns the path — the other is trespassing. Separate generated artifacts from curated fixtures, or the first successful run breaks the next commit.

**variable_injection_symmetry**: If `variables:` works for child graphs (graph-tools), it should work for the top-level graph too. Asymmetric behavior at the same abstraction level is a defect, not a feature.

## Seed

Can the canon directory be split into `canon/seed/` (committed, test fixtures) and `canon/live/` (gitignored, pipeline output)? The reload_canon tool would read from `live/` (falling back to `seed/`), and genesis would write to `live/`. Tests would always read from `seed/`. The ownership boundary becomes a path prefix.
