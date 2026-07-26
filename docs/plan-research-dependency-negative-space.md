# Research: Dependency Negative Space and Missing Platform Components

**Relevance to**: YAMLGraph dependency strategy, replacement analysis, and platform roadmap
**Date**: 2026-07-26
**Inputs**: `pyproject.toml`, `docs/dependency-rationale.yaml`, direct import scan across `yamlgraph/`, `examples/`, `scripts/`, and `tests/`

---

## Summary

YAMLGraph's declared dependency set is mostly coherent for a YAML-first LangGraph framework. The most important finding is not that random packages are missing. The dependency graph exposes missing boundary abstractions: model adapters, vendor-neutral telemetry, reproducible dependency governance, example/runtime packaging, and optional production runtime surfaces.

The core solution is strong at graph orchestration and prompt/schema execution. It is lighter around the application substrate that mature workflow and agent platforms usually accumulate: OpenTelemetry, metrics, lockfiles, plugin packaging, retriever abstraction, round-trip YAML editing, and hosted runtime concerns.

---

## Direct Missing or Underdeclared Dependencies

| Import | Evidence | Current status | Recommendation |
|---|---|---|---|
| `langchain_core` | Imported by core modules and tests for messages, tools, callbacks, runnables, and `BaseChatModel` | Arrives transitively via `langgraph` and provider packages | Add `langchain-core` as an explicit core dependency, or introduce a YAMLGraph-native model interface and confine LangChain to adapters. |
| `litellm` | Imported directly in `yamlgraph/utils/llm_providers.py` for Replicate provider configuration | Arrives through `langchain-litellm` extra | Add `litellm` explicitly to the `replicate` extra, or remove the direct import. |
| `pyarrow` | Imported directly by `examples/rag/index_docs.py` | Arrives through `lancedb` today | Add `pyarrow` to the `rag` extra if the indexing script is supported. |
| `tiktoken` | Imported by `examples/dungeon_master/api/prompt_salience.py` | Not declared | Add a Dungeon Master/example extra or document external install requirements. |
| `unified_planning` | Imported by Dungeon Master plot modules and tests | Not declared | Add a Dungeon Master/example extra if those examples are expected to run under declared extras. |
| `torch`, `torchaudio` | Imported by Chatterbox demo tools | Not declared directly; may be transitive in some Chatterbox installs | Add to `chatterbox` extra when audio synthesis demos are first-party supported. |
| `claude_agent_sdk` | Imported by `examples/agent-sdk-planner/plan.py` | Not declared | Add a dedicated example extra or mark the example externally provisioned. |
| `starlette` | Imported directly by A2A and OpenAI proxy server code | Declared transitively by `fastapi` and `a2a-sdk[http-server]` | Optional explicit declaration in server/protocol extras if following direct-import/direct-dep discipline. |
| `google.protobuf` | Imported by A2A command/client code and tests | Declared transitively by `a2a-sdk` | Usually acceptable, but explicit `protobuf` in `a2a` extra would make the contract honest. |

Low-value candidates:

- `duckduckgo_search`: legacy fallback beside declared `ddgs`; prefer removing fallback rather than adding old package.
- `tomli`: unnecessary under Python `>=3.11` except as a test fallback; stdlib `tomllib` exists.
- `typing_extensions`: one test import; use stdlib `typing.TypedDict` unless the test intentionally exercises extension behavior.

---

## Negative-Space Findings

### 1. Vendor-Neutral Observability Is Missing

YAMLGraph has LangSmith integration, but no OpenTelemetry dependency or semantic event boundary. That means operational truth is currently ecosystem-specific: traces are LangSmith/LangChain-shaped rather than YAMLGraph-shaped.

What is lacking:

- A stable span/event model for graph run, node execution, LLM invocation, tool call, routing decision, retry, interrupt, checkpoint save/load, and verification gate outcomes.
- OTLP export for local, CI, and hosted environments.
- Compatibility with OpenTelemetry GenAI semantic conventions.
- A way to correlate route logs, LangSmith traces, and CLI output under one run identity.

Replacement implication:

- If LangSmith is replaced today, YAMLGraph would need to redesign tracing and callback integration at the same time.
- With an OTEL boundary first, LangSmith can become one exporter rather than the observability spine.

Likely package surface:

```toml
otel = [
    "opentelemetry-api>=1.0.0",
    "opentelemetry-sdk>=1.0.0",
    "opentelemetry-exporter-otlp>=1.0.0",
]
```

### 2. No Native Model Adapter Boundary

The effective runtime contract is LangChain's `BaseChatModel`, `HumanMessage`, `SystemMessage`, `ToolMessage`, callback types, and structured-output behavior. That is productive, but implicit.

What is lacking:

- A YAMLGraph-native request/response shape.
- Provider adapter tests independent of LangChain object classes.
- A declared boundary for streaming chunks, tool calls, usage metadata, structured output, retries, and provider-specific thinking controls.

Replacement implication:

- Replacing any `langchain-*` provider is medium-to-high cost because the target must behave like LangChain.
- Replacing LangChain as a family is a major refactor unless YAMLGraph first defines its own smaller contract.

Candidate shape:

```text
Prompt YAML -> YAMLGraphChatRequest -> ProviderAdapter -> YAMLGraphChatResponse
```

### 3. Reproducible Dependency Governance Is Thin

There is no lockfile or constraints artifact, and `pip-audit` was not installed in the local development environment used for this review.

What is lacking:

- A reproducible resolver output for CI, release, and local verification.
- A local security-audit command that matches CI expectations.
- Explicit package identity for direct imports that currently arrive transitively.

Replacement implication:

- Provider SDK churn can change behavior without a visible dependency diff.
- Reproducing a failure depends on ambient resolver state.

Candidate solutions:

- Add `uv.lock` or a generated constraints file for tested environments.
- Add `pip-audit` to `dev` or a `security` extra.
- Add a direct-import dependency scan gate that distinguishes core, examples, tests, and scripts.

### 4. Example Applications Outgrew Their Extras

Examples now include real application surfaces: RAG indexing, Dungeon Master planning, Chatterbox audio synthesis, OpenAI-compatible proxy, A2A, telco, and agent SDK experiments. The extras only partially encode these requirements.

What is lacking:

- Per-example dependency groups for examples that are more than tiny demos.
- A rule for whether examples must be runnable from declared extras.
- Dependency tests that install each extra and import/run the owned example entry points.

Replacement implication:

- Example failures can look like framework failures.
- Missing dependencies remain hidden until a user chooses that example path.

Candidate shape:

```toml
[project.optional-dependencies]
examples-rag = ["lancedb", "openai", "pyarrow"]
examples-dungeon-master = ["fastapi", "uvicorn", "tiktoken", "unified-planning"]
examples-chatterbox = ["chatterbox-tts", "torch", "torchaudio"]
```

### 5. Retrieval Is Example-Level, Not Framework-Level

RAG exists through examples and LanceDB/OpenAI embeddings, but the dependency graph does not show a YAMLGraph-native retrieval subsystem.

What is lacking:

- A provider-neutral abstraction for document loading, chunking, embedding, vector storage, retrieval, and reranking.
- A common schema for retrieved documents, citations, source spans, and evidence quality.
- Multiple vector store adapters behind one YAML contract.

Replacement implication:

- Replacing LanceDB is only local to examples today.
- Adding serious RAG support later will require defining retriever boundaries before adding more vector-store packages.

### 6. Round-Trip YAML Authoring Is Not First-Class

PyYAML is sound for execution, but it is not a safe round-trip editor for agent-authored graph files. Comments, formatting, and some authorial structure are not preserved.

What is lacking:

- A graph/prompt authoring layer that preserves comments and formatting.
- Codemods that can safely update YAML files without flattening human intent.
- A distinction between execution parsing and authoring/editing parsing.

Candidate solution:

- Keep PyYAML for execution.
- Add `ruamel.yaml` only for authoring, migration, and codemod commands.

### 7. Production Runtime Is Optional and Fragmented

FastAPI/Uvicorn appear in examples and protocol extras, not as a unified YAMLGraph runtime.

What is lacking:

- A first-class hosted graph server with auth, rate limits, metrics, job queue, secrets, tenant config, health checks, and durable background work.
- A policy for when YAMLGraph should stop at compile/run and when it should own service runtime.

Replacement implication:

- Replacing FastAPI is low-to-medium cost because it is not the framework spine.
- Building a production server is a separate product decision, not a dependency cleanup.

### 8. Plugin Packaging Is Not Visible

YAMLGraph is extensible through Python modules and YAML, but the dependency graph does not show installable plugin discovery.

What is lacking:

- Entry point discovery for third-party node types, tools, providers, validators, exporters, or checkpointers.
- Plugin metadata and compatibility contracts.
- Isolation rules for plugin dependencies.

Candidate solution:

- Add plugin discovery only after a concrete third-party extension need appears. Until then, Python module paths are simpler.

---

## Ranked Recommendations

1. **Add an OpenTelemetry boundary and optional OTEL extra.** This is the highest-leverage platform gap: it turns observability into YAMLGraph-owned operational truth instead of LangSmith-specific integration. Define spans/events before adding exporters broadly.
2. **Declare `langchain-core` explicitly or introduce a YAMLGraph-native LLM adapter contract.** Direct imports make the current implicit contract too important to leave transitive.
3. **Add reproducible dependency governance.** Use a lock/constraints workflow plus local `pip-audit` support. Provider SDK churn is too fast for unconstrained drift.
4. **Create an example dependency taxonomy.** Split serious examples into installable extras or mark them externally provisioned. Do not let example app dependencies masquerade as framework dependencies.
5. **Fix direct-import dependency honesty.** Add or remove `litellm`, `pyarrow`, `torch`, `torchaudio`, `tiktoken`, `unified-planning`, `claude-agent-sdk`, and optionally `starlette`/`protobuf` according to the chosen example policy.
6. **Decide whether retrieval belongs in core.** If yes, define retriever/vectorstore/embedding adapters before adding more RAG packages. If no, keep RAG dependencies example-scoped.
7. **Add round-trip YAML authoring support only for agent/codemod workflows.** `ruamel.yaml` is valuable for editing, not execution.
8. **Defer production runtime unless hosting graphs is a product goal.** FastAPI/Uvicorn are sound extras; auth, queues, metrics, secrets, and tenancy are a separate platform layer.
9. **Defer plugin packaging until a real external plugin consumer exists.** Entry points are useful only when there is a named extension ecosystem to support.

---

## Proposed First Feature Request

Start with an observability and dependency-contract FR, not broad dependency expansion.

Ideal result:

- Every graph run can emit a stable YAMLGraph OTEL trace with graph, node, LLM, tool, route, checkpoint, interrupt, and verification spans.
- LangSmith remains supported, but it is no longer the only operational truth surface.
- Direct imports that are part of core contracts are explicitly declared.
- Local dependency audit is reproducible and runnable.

Minimal path:

1. Add `langchain-core` as a direct dependency.
2. Add `pip-audit` under `dev` or a `security` extra.
3. Add an `otel` extra with OTEL API/SDK/OTLP exporter.
4. Define the first small span schema for graph run and node execution.
5. Wire one opt-in OTEL exporter path behind environment/config, then validate on a hello graph.

Seed: What is the smallest trace schema that would let a future agent diagnose a failed graph run without reading logs or rerunning the graph?
