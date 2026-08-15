# Examples Cleanup Plan — 2026-07-01

The `examples/README.md` references `purgatory/` but it doesn't exist. The inclusion criteria are aspirational, not enforced. This plan establishes purgatory and trims the directory from 101 examples to a defensible set.

**FR-796 execution note (2026-08-15):** The three Tier 1 watcher/script/security witnesses named below were deleted, and the seven watcher2 entries at the start of Tier 3 were relocated to `.chaplain/demos/`. All other plan items remain undispositioned by FR-796.

## Tier 1: DELETE (violate inclusion criteria)

| Example | Reason |
|---------|--------|
| `examples/philosopher/` | Self-declared stub. README says "placeholder." Active code lives in `.chaplain/graphs/`. |
| `examples/agent-sdk-planner/` | Spike artifact (2 files). Proves Anthropic SDK works — no graph.yaml, not a YAMLGraph example. |
| `demos/script-retirement/` | No graph. Proves dead scripts stay dead. A commit history assertion cosplaying as a demo. |
| `demos/security-cve-ignore/` | Validates a temporary pip-audit workaround. Obsolete by definition when CVE is fixed. |
| `demos/watcher2-red-verification/` | Thinnest watcher2 demo (README + graph.yaml). Proves a timestamp bug fix — not a feature. |

## Tier 2: MERGE (duplicates that dilute)

| Keep | Absorb | Action |
|------|--------|--------|
| `demos/hello/` | `demos/hellograph-speed/` | Fold provider comparison as a section in hello's README |
| `demos/map/` | `demos/python-map/`, `demos/fan-out/` | python-map is map with python nodes (not a distinct concept); fan-out is edge syntax variant |
| `demos/prompt-caching/` | `demos/cache/` | cache (LangGraph CachePolicy) and prompt-caching (Anthropic segments) serve same user question — unify |
| `demos/router/` | `demos/promptfoo-router/` | promptfoo-router is an eval suite for the router, not a teaching demo — move to `tests/` |

## Tier 3: RELOCATE to `.chaplain/demos/` (internal infrastructure)

These prove CI/Chaplain/watcher2 features. They're regression proofs, not user-facing teaching:

- `demos/watcher2-changelog-gen/`
- `demos/watcher2-ci-remediation/`
- `demos/watcher2-deduplication-gate/`
- `demos/watcher2-hook-preflight-gate/`
- `demos/watcher2-merged-branch-collision-guard/`
- `demos/watcher2-post-merge-inbox-consumption/`
- `demos/watcher2-remediation/`
- `demos/enforcer/`
- `demos/req-cross-check/`
- `demos/pipeline_audit/`
- `demos/run-analyzer/`
- `demos/system-status/`
- `demos/forensic-failure-diary/`
- `demos/hook_classifier/`
- `demos/code-analysis/`

(15 demos → `.chaplain/demos/`)

## Tier 4: QUARANTINE to `purgatory/` (heavyweight drift)

| Example | Issue | Condition to return |
|---------|-------|---------------------|
| `examples/dungeon_master/` (24k LOC) | A product with its own purgatory. 182 files. | Extract to own repo or prune to <2k LOC reference |
| `examples/plot_modeller/` (17k LOC) | Active research spike, not exemplifying YAMLGraph. 134 files. | Finish FR-570 series and extract |
| `examples/yamlgraph_gen/` (5k LOC) | 2+ months stale. 148 files. May not reflect current schema. | Validate against current YAML spec or delete |
| `examples/rtm-hello/` (103 files) | Teaches requirement traceability — which the main project already does. Contains .coverage/.ruff_cache cruft. | Prune to minimal standalone demo |
| `examples/fsm-router/` | Couples to external `statemachine-engine` project. Breaks if that moves. | Pin dependency or extract |

## Tier 5: FIX (incomplete but valuable)

| Demo | Problem | Fix |
|------|---------|-----|
| `demos/streaming/` | No graph.yaml — raw Python script bypassing YAML paradigm. #1 feature people look for. | Create proper YAML streaming graph |
| `demos/interrupt/` | No graph.yaml at root (uses subdirectory structure). Missing demo-output.log. | Restructure to standard demo layout |
| Learning path demos (router, map, reflexion, subgraph, interview, git-report) | No demo-output.log — unproven execution | Run each and capture output |

## Execution Order

1. **Create `purgatory/` and `purgatory/README.md`** — fulfill the promise in `examples/README.md`
2. **Tier 1: Delete** (5 items) — immediate, no dependencies
3. **Tier 3: Relocate** (15 items) — `git mv` to `.chaplain/demos/`, update MCP discovery patterns
4. **Tier 2: Merge** (4 clusters) — combine READMEs, delete redundant directories
5. **Tier 5: Fix** — run learning path demos, capture demo-output.log
6. **Tier 4: Quarantine** — move to purgatory with README explaining return conditions
7. **Update `examples/README.md`** — remove dead links, trim tables

## Impact

| Metric | Before | After |
|--------|--------|-------|
| Total examples | 101 | ~55 |
| LOC in examples/ | ~55k | ~12k |
| Demos without proof | 32 | 0 (remaining all have demo-output.log) |
| Purgatory exists | No | Yes |

## MCP Discovery Impact

`DEFAULT_GRAPH_PATTERNS` includes `examples/demos/*/*.yaml`. Relocated demos will no longer appear as MCP tools. This is correct — infrastructure demos should not pollute the tool namespace.

Quarantined top-level examples (`examples/*/*.yaml`) will also disappear from MCP. Add `purgatory/*/*.yaml` to patterns only if they're still runnable.
