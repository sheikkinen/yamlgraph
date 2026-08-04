# Judgement: FR-769 Shared Vision Tool (Image -> Structured Text)

**Prior art:** FR-769-shared-vision-tool.md is the FR under judgement (self-hit). `examples/shared/replicate_tool.py` (generation-only complement) and `examples/shared/websearch.py` (shared-tool precedent) are dispositioned in the FR's Prior Art section; no prior FR proposes image understanding — the FR archive grep returns only research notes.

**Verdict:** APPROVED WITH REVISIONS — the shared-tool direction is real, minimal, and architecture-aligned, but enforcement authority activates only after R-1..R-4 make provider support, traceability, demo evidence, and scope boundaries mechanically testable.

**Reviewed against:** `feature-requests/FR-769-shared-vision-tool.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `ARCHITECTURE.md`; `docs/adr/001-test-requirement-traceability.md`; `examples/shared/replicate_tool.py`; `examples/shared/websearch.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/config.py`; `docs/Analyzing YAML-Driven LangGraph Repositories.md`; `capabilities/CAP-20-contrib-utilities.yaml`; `capabilities/CAP-77-image-generation-pipeline.yaml`; `capabilities/CAP-215-style-convert-pipeline.yaml`; `examples/demos/web-research/graph.yaml`; `examples/demos/web-research/README.md`; `examples/demos/image-that-speaks/graph.yaml`; `examples/demos/image-that-speaks/README.md`.

## What is sound

The problem is real and cited to concrete consumers: FR-769 names the DeviantArt posting pipeline as first consumer and image_pipeline/storyboard/npc/style_convert as follow-on QA consumers (`feature-requests/FR-769-shared-vision-tool.md:8-12`), and the cited repository report records YAMLGraph's provenance in high-throughput generative art pipelines plus a DeviantArt AI art pipeline reference (`docs/Analyzing YAML-Driven LangGraph Repositories.md:5`, `docs/Analyzing YAML-Driven LangGraph Repositories.md:80-85`, `docs/Analyzing YAML-Driven LangGraph Repositories.md:255`).

The proposed boundary is minimal. A shared Python tool under `examples/shared/` with zero core changes matches the three-layer architecture: YAML graphs own orchestration, while Python tools own external API/file side effects (`ARCHITECTURE.md:36-70`). Existing shared-tool precedent exists in `examples/shared/websearch.py`, exposed as a `type: python` tool by the web-research demo (`examples/shared/websearch.py:1-15`, `examples/demos/web-research/graph.yaml:10-15`, `examples/demos/web-research/README.md:38-47`), and the cited image-generation complement is indeed generation-only (`examples/shared/replicate_tool.py:1-7`, `examples/shared/replicate_tool.py:62-138`).

The strategic classification is **Contrib/example**, not a framework primitive: there are multiple example consumers, but the FR correctly avoids a new core `type: vision` node and keeps the first implementation as a plain Python tool (`feature-requests/FR-769-shared-vision-tool.md:16-20`, `feature-requests/FR-769-shared-vision-tool.md:90-99`).

## Required revisions

### R-1: Freeze the supported provider/model contract

Replace the loose phrase "vision-capable provider" with a concrete initial support matrix in the FR. The matrix must name the supported provider/model defaults for this FR, the required environment variables, and the exact failure behavior for unsupported providers or models. It must not require core provider-capability changes.

Minimum fold-in:

| Provider | Initial supported model source | Required env | Unsupported behavior |
|---|---|---|---|
| `google` | `GOOGLE_MODEL` or `gemini-2.0-flash` | `GOOGLE_API_KEY` | raise `ValueError` naming provider/model and supported set before the LLM call when provider/model is outside the allowlist |
| `anthropic` | `ANTHROPIC_MODEL` or `claude-haiku-4-5` | `ANTHROPIC_API_KEY` | same |

This revision is required because the factory supports many providers (`yamlgraph/utils/llm_factory.py:21-35`) and dispatches to text-only/OpenAI-compatible wrappers as well as Google/Anthropic (`yamlgraph/utils/llm_providers.py:187-268`, `yamlgraph/utils/llm_providers.py:368-405`). FR-769's current acceptance criterion requires "non-vision provider raises a clear error" (`feature-requests/FR-769-shared-vision-tool.md:82-83`) but does not define how the tool distinguishes unsupported providers from merely failed model calls.

### R-2: Add a new capability requirement for the shared vision tool

Fold an explicit traceability surface into the FR: add a new `capabilities/CAP-XXX-shared-vision-tool.yaml` deliverable with a new `REQ-YG-XXX` requirement covering `examples/shared/vision_tool.py`, the demo, and Tier 1 tests. The FR must state that all new tests under `tests/unit/` and `tests/integration/` use that REQ marker.

This is required because FR-769 already demands mocked unit tests and a guarded integration test (`feature-requests/FR-769-shared-vision-tool.md:86-87`), while ADR-001 requires `@pytest.mark.req("REQ-YG-XXX")` for Tier 1 tests (`docs/adr/001-test-requirement-traceability.md:11-23`, `docs/adr/001-test-requirement-traceability.md:46-72`). No existing capability cleanly owns shared image-understanding: CAP-20 covers contrib utilities, not `examples/shared` vision tools (`capabilities/CAP-20-contrib-utilities.yaml:1-22`); CAP-77 covers image generation only (`capabilities/CAP-77-image-generation-pipeline.yaml:1-19`); CAP-215 covers style conversion only (`capabilities/CAP-215-style-convert-pipeline.yaml:1-29`).

### R-3: Make the demo mechanically reproducible and bounded

Revise the demo acceptance criterion to name its exact demo path, fixture strategy, and validation commands. The demo may use a committed tiny fixture image or an image generated earlier in the demo, but the FR must state which one. If generation is part of the demo, the FR must specify the API-key guard and still require a committed `demo-output.log` proving a successful run.

Minimum fold-in:

- Demo path: `examples/demos/shared-vision-tool/`.
- Demo command: `yamlgraph graph lint examples/demos/shared-vision-tool/graph.yaml` and one `yamlgraph graph run ... --full` command.
- Demo output: `examples/demos/shared-vision-tool/demo-output.log`.
- No consumer wiring into `examples/image_pipeline/`, `examples/storyboard/`, `examples/npc/`, `examples/style_convert/`, or any DeviantArt posting graph.

This is required because the current "Demo graph in `examples/demos/` exercising the tool on a generated image" criterion (`feature-requests/FR-769-shared-vision-tool.md:84-85`) is not yet mechanically checkable: it does not identify the graph path, whether generation is live or fixture-based, or the commands the enforcer must run.

### R-4: Specify the structured output and error tests precisely

Replace the broad test criterion with the exact test cases the enforcer must write:

1. Local image path is read, encoded into a multimodal message, and sent through a mocked `create_llm()` chat model.
2. URL input is passed as an image URL content part without local file reads.
3. Returned JSON/object content is validated into `ImageDescription`.
4. Missing local path raises `FileNotFoundError` or `ValueError` naming the path.
5. Unsupported provider/model raises `ValueError` naming provider/model and supported set before any LLM invocation.
6. Malformed model output raises a Pydantic validation error rather than returning a partial/success-shaped fallback.

This is required because the FR promises Pydantic output (`feature-requests/FR-769-shared-vision-tool.md:67-68`) and no silent fallback (`feature-requests/FR-769-shared-vision-tool.md:82-83`), but the acceptance criteria do not yet define enough seams for failing tests to be derived directly.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/shared/vision_tool.py` with `ImageDescription` and `describe_image()` |
| D-2 | `tests/unit/test_shared_vision_tool.py` with mocked LLM/provider behavior |
| D-3 | `tests/integration/test_shared_vision_tool.py` guarded by the selected provider API key |
| D-4 | `examples/demos/shared-vision-tool/graph.yaml`, prompts/support files if needed, and `demo-output.log` |
| D-5 | `examples/shared/README.md` update documenting usage, providers, errors, and graph declaration |
| D-6 | `capabilities/CAP-XXX-shared-vision-tool.yaml` and regenerated architecture capability index if hooks require it |
| D-7 | `changelog/unreleased/<fragment>.md` referencing the new REQ |

Not authorized: core node types such as `type: vision`; changes to `yamlgraph/graph_loader.py`, node compilation, or provider factory APIs; FR-768 manifest work; DeviantArt API posting; QA gate wiring into image_pipeline/storyboard/npc/style_convert; new dependency extras unless the implementation proves an undeclared dependency is actually required; broad provider auto-detection beyond the R-1 allowlist.

## Revised acceptance criteria

- [ ] AC-01: `examples/shared/vision_tool.py` defines `ImageDescription` as a Pydantic model and `describe_image(image: str | Path, instruction: str, *, provider: str | None = None, model: str | None = None) -> ImageDescription`.
- [ ] AC-02: `describe_image()` constructs its chat model through `yamlgraph.utils.llm_factory.create_llm()` only; no direct provider SDK imports are added.
- [ ] AC-03: The FR's supported provider/model allowlist is enforced before invocation; unsupported provider/model raises `ValueError` naming the actual provider/model and supported set.
- [ ] AC-04: Local missing/unreadable images raise a clear exception naming the path; URL inputs are accepted as URL content parts; no error path returns a success-shaped `ImageDescription`.
- [ ] AC-05: Unit tests mock `create_llm()` and cover local path, URL input, structured-output validation, missing path, unsupported provider/model, and malformed model output; every Tier 1 test carries the new `REQ-YG-XXX` marker.
- [ ] AC-06: A guarded integration test runs only when the selected provider API key is present and otherwise skips explicitly.
- [ ] AC-07: `examples/demos/shared-vision-tool/graph.yaml` lints and has a committed `demo-output.log` from the command named in the revised FR.
- [ ] AC-08: `examples/shared/README.md` documents Python usage, graph `type: python` declaration, supported provider/model matrix, required env vars, and failure modes.
- [ ] AC-09: A new capability YAML file declares the shared vision tool requirement and maps it to implementation/tests; architecture capability aggregation is updated if the repository hook requires it.
- [ ] AC-10: A changelog fragment is added under `changelog/unreleased/` with `req:` set to the new requirement ID.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1..R-4 must be folded into `feature-requests/FR-769-shared-vision-tool.md` before implementation begins. | GATE |
| C-2 | The implementation must stay within D-1..D-7 and must not modify core graph compilation/provider APIs. | GATE |
| C-3 | If enforcement discovers multimodal invocation cannot be implemented through the existing LangChain chat-model interface returned by `create_llm()`, stop and return for a new FR rather than adding direct provider SDK calls or core changes. | GATE |
| C-4 | Any change to CI, hooks, judge/review doctrine, or provider factory public API is outside this FR and requires separate human-reviewed authority. | GATE |

Authority granted: after R-1..R-4 are folded into the FR, enforcement may build one `examples/shared` vision Python tool, one bounded demo, traceability, docs, tests, and changelog exactly within the frozen scope above.
