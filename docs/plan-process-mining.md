# Process Mining Plan for YAMLGraph

**Origin:** FR-362 POC analysis — `minesweeper-001` run (2026-05-10)

## Problem

YAMLGraph executes multi-phase Copilot workflows (watcher, bugfix, enforcement) whose internal structure is entirely unobservable. No OTel, no per-node traces, no process model. The FR-362 POC proved that Copilot CLI OTel spans contain enough signal to reconstruct a labelled process model from a single run — but one run is not a process model. Scaling to genuine process mining requires:

1. Per-node OTel scoping (multi-node graphs produce interleaved, unusable spans today)
2. Semantic event classification beyond raw span names
3. Multi-run stability scoring to distinguish stable steps from incidental choices
4. A mining pipeline that is itself a YAMLGraph graph

## Key findings from FR-362 POC

- **`report_intent` is a free phase segmenter.** Every phase transition emits a `report_intent` span with a human-readable intent label. Phase segmentation requires no ML.
- **Copilot CLI OTel inherits from parent env automatically.** No code changes needed to get spans — `COPILOT_OTEL_FILE_EXPORTER_PATH` in the shell env is sufficient.
- **Multi-node graphs need per-node scoping.** Without it, plan → judge → enforce spans interleave into one file.
- **7 of 15 observed steps are deterministic today** and could graduate from `type: copilot` to `type: tool`/`type: python`.
- **The process model is a DAG with one adaptive loop** (`fix_loop`). Everything else is stable.

See `docs/copilot-instrumentation-poc.md` for the full minesweeper-001 findings.

## Current instrumentation gaps

| Layer | OTel today | Problem |
|---|---|---|
| Copilot CLI internal | ✅ via env var | Works; but single path = interleaved spans across nodes |
| YAMLGraph node execution | ❌ none | Graph-level structure invisible; node durations unknown |
| LangGraph / LangChain | ✅ LangSmith only | Requires cloud credentials; not local-first |
| Watcher graphs | ❌ none | 20+ runs; all dark |

## Proposed FRs

### FR-363 — Per-node OTel scoping in `copilot_node.py`

**Priority: HIGH — prerequisite for all others.**

Add `YAMLGRAPH_OTEL_DIR` env var support to `_execute_cli`. When set, each copilot node subprocess receives:

```bash
COPILOT_OTEL_FILE_EXPORTER_PATH="$YAMLGRAPH_OTEL_DIR/<node_name>.otel.jsonl"
```

No behaviour change when unset. Enables multi-node graphs (watcher: plan → judge → enforce) to produce per-node OTel files that the FR-362 extractor already understands.

**Implementation:** One `env=` parameter added to `subprocess.run` in `_execute_cli`. No new dependencies.

**Acceptance criteria:**
- [ ] When `YAMLGRAPH_OTEL_DIR` is set, each copilot node writes its spans to `<dir>/<node_name>.otel.jsonl`
- [ ] When unset, behaviour is unchanged
- [ ] A watcher enforce run with `YAMLGRAPH_OTEL_DIR` set produces separate files for `plan`, `judge`, and `enforce` nodes

---

### FR-364 — Semantic event classification in the extractor

**Priority: HIGH — enables useful multi-run analysis.**

Extend `scripts/extract_copilot_events.py` to classify tool calls semantically using span attributes (available when `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`):

| New event type | Detection |
|---|---|
| `phase_marker` | `report_intent` span → `gen_ai.tool.call.arguments.intent` |
| `test_run` | `bash` span with `pytest` in command |
| `lint_run` | `bash` span with `ruff` or `yamlgraph graph lint` |
| `file_create` | `create` span |
| `file_edit` | `edit` span |
| `failure` | `bash` result with nonzero exit or exception text |
| `scaffold` | `bash` span with `mkdir` |

Add a multi-run stability scorer: given N run directories, score each event type by frequency across runs. Steps appearing in all N runs with consistent outcomes are candidates for graduation.

---

### FR-365 — Process mining pipeline as a YAMLGraph graph

**Priority: MEDIUM — depends on FR-363 + FR-364 + ≥5 real runs.**

A `graphs/process-mining/graph.yaml` that takes a directory of OTel run journals and produces:
- A candidate `graph.yaml` workflow skeleton
- A conformance report with per-step stability scores
- Node type recommendations per step

```
scan_runs [python]
  → extract_events [map]        ← parallel per-run extraction
  → classify_events [python]    ← semantic classification (FR-364)
  → segment_phases [python]     ← group by phase_marker events
  → cluster_phases [llm]        ← tolerant name matching across runs
  → score_stability [python]    ← frequency scoring
  → propose_nodes [llm]         ← node type recommendations
  → render_skeleton [python]    ← emit candidate graph.yaml
  → write_report [python]       ← conformance table
```

The pipeline is itself the proof that process mining belongs in YAMLGraph.

---

### FR-366 — OTel instrumentation of YAMLGraph node execution

**Priority: MEDIUM — enables unified graph-level + agent-level traces.**

Add OpenTelemetry spans to `node_factory/base.py` wrapping each node call:
- Span name: `execute_node <node_name>`
- Attributes: `node.type`, `node.state_key`, `node.duration_ms`, `node.exit_status`
- Parent span: `invoke_graph <graph_name>`

When `YAMLGRAPH_OTEL_DIR` is set, emit `graph-execution.otel.jsonl` alongside the per-copilot-node files. Requires `opentelemetry-sdk` as a new optional dependency.

This closes the loop: FR-362's extractor then works on the graph-level structure too, not just what happens inside copilot nodes. The watcher's plan → judge → enforce structure becomes observable without any graph changes.

---

## Dependency graph

```
FR-362 (POC, done)
  └─ FR-363 (per-node OTel scoping)      ← implement first
       └─ FR-364 (semantic classification)
            └─ FR-365 (mining pipeline graph)  ← needs 5+ runs
  └─ FR-366 (YAMLGraph node OTel)        ← independent; enhances 363+364
```

## Graduation criterion

A step graduates from `type: copilot` to `type: tool`/`type: python` when:

1. It appears in all N observed runs (frequency = 100%)
2. Its output is structurally identical across runs (exit code, file set, event type sequence)
3. It can be re-expressed without LLM reasoning

The mining pipeline (FR-365) computes these scores automatically.

## The meta-observation

The Copilot agent and YAMLGraph already converge on the same abstraction. The agent uses `report_intent` to announce phases; YAMLGraph uses node names. Process mining closes the loop: observed agent behaviour becomes the specification for the next generation of YAMLGraph nodes. The framework eats its own traces and grows.

**Open question (Seed):** If the mining pipeline produces a `graph.yaml` skeleton and YAMLGraph can run it, the pipeline is also a code-generation pipeline. What is the minimum number of runs before a generated graph is trustworthy enough to run unsupervised?
