# Node-Type Usage Census — August 2026

**Feature request:** FR-802
**Corpus:** committed `*.yaml` and `*.yml` files at `3820b520`
**Authority:** evidence for later add, merge, or retirement FRs; not authority to change runtime code, graphs, tests, capabilities, or node types

## Method

The dispatch registry is `NODE_TYPE_HANDLERS` in
`yamlgraph/compile/node_compiler.py`. The registry, not `NodeType` or the
linter allow-list, defines the 13 census rows. `interactive_tool` and
`pipeline` are preprocessing types and are reported separately below.

The structural inventory loads every committed YAML candidate with
`yaml.safe_load_all`, recursively finds `nodes:` mappings, and records typed
entries as `file`, dotted node location, declared `type`, and consumer class.
The recursion includes nested map/subgraph node mappings. Consumer classes are
assigned by committed root: `projects/` = production project,
`examples/demos/` = demo, other `examples/` = example, `graphs/` = root graph,
`tests/` = test fixture, and `.chaplain/` = governance pipeline. Other roots
remain explicit rather than being guessed into a consumer class.

Run from repository root with the project virtual environment. Both commands
are local and make no network calls.

```bash
.venv/bin/python -c 'from yamlgraph.compile.node_compiler import NODE_TYPE_HANDLERS; print(*sorted(NODE_TYPE_HANDLERS), sep="\n")'
```

```bash
.venv/bin/python - <<'PY'
import json
import subprocess
from pathlib import Path

import yaml
from yamlgraph.compile.node_compiler import NODE_TYPE_HANDLERS

files = subprocess.check_output(
    ["git", "ls-files", "*.yaml", "*.yml"], text=True
).splitlines()


def consumer_class(path):
    if path.startswith("projects/"):
        return "production-project"
    if path.startswith("examples/demos/"):
        return "demo"
    if path.startswith("examples/"):
        return "example"
    if path.startswith("graphs/"):
        return "root-graph"
    if path.startswith("tests/"):
        return "test-fixture"
    if path.startswith(".chaplain/"):
        return "governance-pipeline"
    return "other"


def node_rows(value, path, location="document"):
    rows = []
    if isinstance(value, dict):
        nodes = value.get("nodes")
        if isinstance(nodes, dict):
            for name, config in nodes.items():
                if isinstance(config, dict) and isinstance(config.get("type"), str):
                    rows.append(
                        {
                            "file": path,
                            "node": f"{location}.nodes.{name}",
                            "type": config["type"],
                            "class": consumer_class(path),
                        }
                    )
                rows.extend(node_rows(config, path, f"{location}.nodes.{name}"))
        for key, child in value.items():
            if key != "nodes":
                rows.extend(node_rows(child, path, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(node_rows(child, path, f"{location}[{index}]"))
    return rows


rows = []
excluded = []
for path in files:
    try:
        documents = list(yaml.safe_load_all(Path(path).read_text()))
    except Exception as error:
        excluded.append(
            {"file": path, "reason": f"YAML parse error: {type(error).__name__}"}
        )
        continue
    file_rows = []
    for index, document in enumerate(documents):
        file_rows.extend(node_rows(document, path, f"document[{index}]"))
    if file_rows:
        rows.extend(file_rows)
    else:
        excluded.append(
            {"file": path, "reason": "no nodes mapping with typed entries"}
        )

print("REGISTRY\t" + json.dumps(sorted(NODE_TYPE_HANDLERS)))
for row in sorted(rows, key=lambda item: (item["file"], item["node"])):
    print("ROW\t" + json.dumps(row, sort_keys=True))
for row in sorted(excluded, key=lambda item: item["file"]):
    print("EXCLUDED\t" + json.dumps(row, sort_keys=True))
PY
```

## Source Inventory

The corpus contains 966 committed YAML candidates. Structural discovery found
232 graph artifacts and 709 typed entries; 734 candidates were excluded, all
for `no nodes mapping with typed entries`. No candidate failed YAML parsing.
The counted registry entries are distributed across demos, examples, the
governance pipeline, one root graph, and test fixtures. No committed
`projects/` graph artifact was present in this repository snapshot.

Five structural hits are not dispatch-registry entries and are excluded from
the usage matrix:

| Declared type | File and node | Treatment |
|---|---|---|
| `interactive_tool` | `examples/demos/interactive_tool/graph.yaml`, `document[0].nodes.quiz` | preprocessing type |
| `interactive_tool` | `tests/integration/fixtures/interactive_tool/chatbot.yaml`, `document[0].nodes.chat` | preprocessing type |
| `interactive_tool` | `tests/integration/fixtures/interactive_tool/chatbot_no_end.yaml`, `document[0].nodes.chat` | preprocessing type |
| `pipeline` | `examples/demos/pipeline/graph.yaml`, `document[0].nodes.topics` | preprocessing type |
| `object` | `examples/beautify/prompts/analyze.yaml`, `document[0].output_schema.properties.nodes.items` | schema-shaped false positive; not a graph node |

## Registry Usage

Counts are node entries; `Files` is the distinct graph-artifact count. The raw
file and node-location evidence for every row is in Appendix A.

| Type | Prod | Demo | Example | Governance | Root | Test | Other | Total | Files |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `agent` | 0 | 17 | 7 | 0 | 0 | 0 | 0 | 24 | 22 |
| `copilot` | 0 | 4 | 52 | 11 | 0 | 0 | 3 | 70 | 24 |
| `interrupt` | 0 | 8 | 11 | 0 | 0 | 1 | 0 | 20 | 15 |
| `llm` | 0 | 96 | 118 | 9 | 1 | 36 | 0 | 260 | 152 |
| `map` | 0 | 21 | 25 | 0 | 0 | 1 | 0 | 47 | 39 |
| `passthrough` | 0 | 11 | 10 | 0 | 0 | 3 | 0 | 24 | 15 |
| `python` | 0 | 51 | 133 | 14 | 0 | 3 | 0 | 201 | 85 |
| `race` | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| `router` | 0 | 3 | 2 | 0 | 0 | 0 | 0 | 5 | 5 |
| `subgraph` | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 4 | 4 |
| `tool` | 0 | 15 | 0 | 22 | 0 | 3 | 0 | 40 | 10 |
| `tool_call` | 0 | 5 | 0 | 0 | 0 | 2 | 0 | 7 | 6 |
| `verify` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Incident Density

`incident_count` is the number of cited FR or diary entries whose problem,
fix, or judgement directly concerns the type as a runtime primitive.
`usage_count` is the registry usage total above. Therefore:

$$
\text{incident density} =
\frac{\text{incident count}}{\max(\text{usage count}, 1)}
$$

The pass is deliberately conservative: features, demos, provider/executor
incidents, and generic occurrences of `agent`, `map`, `tool`, or `router` do
not count unless the cited entry changes or diagnoses that node primitive.

| Type | Incidents | Usage | Density | Direct incident evidence |
|---|---:|---:|---:|---|
| `agent` | 6 | 24 | 0.250 | `feature-requests/057-agent-messages-quadratic-growth.md` (message accumulation); `feature-requests/059-agent-normalize-content-to-string.md` (provider content normalization); `feature-requests/FR-448-agent-structured-output.md`, `FR-449-agent-structured-output-anthropic-bugfix.md`, `FR-451-agent-temperature-zero-bug.md`, `FR-678-narrow-agent-structured-output-catch.md` (agent compilation/execution defects) |
| `copilot` | 3 | 70 | 0.043 | `feature-requests/FR-266-copilot-node-model-selection.md` (model forwarding); `FR-363-per-node-otel-scoping-in-copilot-node.md` (node subprocess scope); `FR-383-copilot-node-backend-api-fallback.md` (backend failure path) |
| `interrupt` | 4 | 20 | 0.200 | `feature-requests/039-async-interrupt-output-mapping.md` (resume mapping); `060-interrupt-set-response-before-pause.md` (state commit ordering); `FR-210-subgraph-interrupt-state-commit.md` and `FR-797-subgraph-interrupt-propagation-langgraph-1x.md` (interrupt propagation across child boundary) |
| `llm` | 0 | 260 | 0.000 | No conservative node-primitive incident; provider, prompt, and shared executor incidents excluded |
| `map` | 2 | 47 | 0.043 | `feature-requests/069-map-node-timeout.md` (map timeout); `FR-467-conditional-edge-to-map-node.md` (map target compilation) |
| `passthrough` | 1 | 24 | 0.042 | `feature-requests/FR-721-passthrough-output-literal-seeds.md` (literal output semantics) |
| `python` | 1 | 201 | 0.005 | `feature-requests/FR-252-python-node-variables.md` (variable resolution) |
| `race` | 10 | 2 | 5.000 | `feature-requests/FR-264-race-node-parse-json-content-normalization.md` (winner normalization); `FR-267-race-node-timeout-double-wrap-2.md`, `FR-270-race-node-pool-shutdown-blocking.md`, `FR-271-async-race-node-cancellable.md`, `FR-705-race-timeout-candidate-fidelity.md`, `FR-706-race-timeout-loop-liveness.md`, `FR-707-race-sync-bridge-deadline.md`, `FR-709-race-loser-teardown-integration.md`, `FR-720-close-trace-spans-on-loser-cancel.md` (deadline/loser lifecycle); `FR-392-fsm-race-winner-payload-sanitization.md` (winner payload boundary) |
| `router` | 3 | 5 | 0.600 | `feature-requests/107-router-route-field.md` (route-field semantics); `FR-211-router-route-mapping-redirect.md` (route mapping); `FR-272-router-node-race-candidates.md` (candidate dispatch) |
| `subgraph` | 4 | 4 | 1.000 | `feature-requests/030-subgraph-token-streaming.md` (streaming boundary); `FR-210-subgraph-interrupt-state-commit.md` (state commit); `fix-subgraph-interrupt-output-mapping.md` (output mapping); `FR-797-subgraph-interrupt-propagation-langgraph-1x.md` (LangGraph 1.x propagation) |
| `tool` | 0 | 40 | 0.000 | Generic tools, shell tools, and agent-bound tools excluded; no conservative `type: tool` runtime incident found |
| `tool_call` | 2 | 7 | 0.286 | `feature-requests/FR-772-tool-call-inline-dict-args.md` (argument contract); `FR-778-tool-call-on-error-fail.md` (error contract) |
| `verify` | 0 | 0 | 0.000 | No usage and no direct incident found |

Ambiguous non-incidents include research-agent demos, Agent SDK studies,
generic toolbelt work, map/reduce prose, LLM provider incidents, and router
mentions describing application-level routing rather than `type: router`.

## Future Consumers

Only `subgraph` has committed future-demand evidence with a named event.
`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md`
quotes the external ninchat_voice backlog navigator at
`projects/ninchat_voice/backlog.txt:48-58`; this is **secondary evidence**.
The first event is implementation of that backlog navigator. No other type has
a committed future-consumer citation and named first event in this pass.

Current production evidence for `interrupt` and `race` is also secondary:
`docs/diary/2026-08-15-market-research.md` records the production ninchat_voice
consumer while its graph artifacts remain outside this repository corpus.

## Disposition

| Type | Disposition | Evidence and required follow-up |
|---|---|---|
| `agent` | RETIRE | Demo/example-only; no committed production or future consumer. Open a separate FR using the `feature-requests/FR-466-cap-retirement-support.md` Proposed → Deprecated → Retired lifecycle. |
| `copilot` | KEEP | 11 governance-pipeline entries and 3 other operational entries; active governed-pipeline consumer. |
| `interrupt` | KEEP | Committed secondary evidence names current ninchat_voice production use; preserve the primitive. |
| `llm` | KEEP | 9 governance-pipeline entries, the root graph, and broad artifact use; active governed-pipeline consumer. |
| `map` | RETIRE | Demo/example-only; no committed future consumer. Open a separate FR through the FR-466 lifecycle. |
| `passthrough` | MERGE | Target `python`; migrate literal/static state updates to a Python node returning the same update dict in a separately judged FR. |
| `python` | KEEP | 14 governance-pipeline entries; active governed-pipeline consumer. |
| `race` | KEEP | Committed secondary evidence names current ninchat_voice production use; incident density requires hardening, not removal. |
| `router` | MERGE | Target `llm`; both share `_compile_llm_node`. Migrate declared routers to `llm` plus existing conditional-edge routing in a separately judged FR. |
| `subgraph` | KEEP-with-consumer | FR-797 secondary evidence names the backlog navigator and its first implementation event. |
| `tool` | KEEP | 22 governance-pipeline entries; active governed-pipeline consumer. |
| `tool_call` | RETIRE | Demo/test-only with two recent contract incidents and no committed future consumer. Open a separate FR through the FR-466 lifecycle. |
| `verify` | RETIRE | Registered but unused. Open a separate FR through the FR-466 lifecycle before changing code or capabilities. |

This table is binding only as the evidence source that future add, merge, or
retirement FRs must cite or update. It does **not** authorize runtime changes,
graph rewrites, test deletion, CAP retirement, migration, deprecation, or node
removal under FR-802.

## Appendix A — Raw Registry Evidence

The extraction command above emits all 704 registry-aligned rows. These audit
anchors give one literal raw row for every aggregate usage row; the fields are
`type`, `consumer class`, `file`, and dotted `node`. `verify` has no raw hit,
which is itself the evidence for its zero row.

| Type | Class | File | Node |
|---|---|---|---|
| `agent` | demo | `examples/demos/agent-json/graph.yaml` | `document[0].nodes.analyst` |
| `copilot` | governance-pipeline | `.chaplain/graphs/philosopher/graph.yaml` | `document[0].nodes.analyze` |
| `interrupt` | example | `examples/book_translator/graph.yaml` | `document[0].nodes.human_review` |
| `llm` | governance-pipeline | `.chaplain/graphs/world_distill/graph.yaml` | `document[0].nodes.distill` |
| `map` | example | `examples/book_translator/graph.yaml` | `document[0].nodes.translate_all` |
| `passthrough` | example | `examples/rag/graph.yaml` | `document[0].nodes.setup` |
| `python` | governance-pipeline | `.chaplain/graphs/fr_triage/graph.yaml` | `document[0].nodes.read` |
| `race` | demo | `examples/demos/race/graph.yaml` | `document[0].nodes.fastest_answer` |
| `router` | demo | `examples/demos/router/graph.yaml` | `document[0].nodes.classify` |
| `subgraph` | demo | `examples/demos/subgraph/graph.yaml` | `document[0].nodes.summarize` |
| `tool` | governance-pipeline | `.chaplain/demos/watcher2-hook-preflight-gate/graph.yaml` | `document[0].nodes.summary` |
| `tool_call` | demo | `examples/demos/tool-call/graph.yaml` | `document[0].nodes.dispatch` |
| `verify` | none | none | no typed entry found |

## Appendix B — Excluded Candidates

The extraction command above emits every excluded path and its reason. All 734
exclusions have the reason `no nodes mapping with typed entries`; no YAML parse
error occurred. This root-complete inventory proves that the candidate total is
not a hand-maintained graph-path list:

| Root | Excluded candidates | Reason |
|---|---:|---|
| `.chaplain/` | 31 | no nodes mapping with typed entries |
| `.github/` | 8 | no nodes mapping with typed entries |
| `.pre-commit-config.yaml` | 1 | no nodes mapping with typed entries |
| `capabilities/` | 213 | no nodes mapping with typed entries |
| `docs/` | 2 | no nodes mapping with typed entries |
| `examples/` | 469 | no nodes mapping with typed entries |
| `feature-requests/` | 1 | no nodes mapping with typed entries |
| `graphs/` | 1 | no nodes mapping with typed entries |
| `prompts/` | 4 | no nodes mapping with typed entries |
| `tests/` | 4 | no nodes mapping with typed entries |
| **Total** | **734** | |

The five files that passed the structural typed-entry test but did not map to
the dispatch registry are listed individually in Source Inventory, including
the sole schema-shaped false positive. Thus every candidate is represented by
an exact emitted row, an aggregate exclusion row, or an explicit non-registry
structural-hit row.
