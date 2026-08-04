# Feature Request: FR-769 — Shared Vision Tool (Image → Structured Text)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved with revisions (judged 2026-08-04 — [FR-769-shared-vision-tool.judgement.md](FR-769-shared-vision-tool.judgement.md))
**Effort:** 1–2 days
**Requested:** 2026-08-04
**Prior art:** FR-769-shared-vision-tool.judgement.md is this FR's own judgement. FR-768 (tool manifests) is the companion declaration-reuse FR — this tool is an intended manifest consumer, no overlap in mechanism. FR-128 (yamlgraphication of enforcer), FR-571 (plot modeller schema), FR-381 (batch LLM node) match only on generic nouns (vision/tool/shared) — none concerns image understanding. See also the Prior Art section below (replicate_tool, websearch precedents).
**First consumer / first event:** the DeviantArt posting pipeline — the moment
a freshly generated image needs a title, description, and tags derived *from
the image itself* before upload. Second consumers immediately behind it:
image_pipeline / storyboard / npc output QA (prompt-match verification,
best-of-N selection, character consistency across frames).

## Summary

Add a multimodal image→text tool to `examples/shared/` (companion to
`websearch.py` and `replicate_tool.py`): given an image path/URL and an
instruction prompt, return structured text (description, tags, quality
verdict) via a vision-capable provider. Pure `type: python` tool — **zero
core changes**.

## Value Statement

Image-producing pipelines (four example families) gain eyes: they can verify,
select, and describe their own outputs, and the DeviantArt publishing workflow
becomes automatable end-to-end (generate → inspect → caption → post).

## Problem

No image→text capability exists anywhere in core or examples —
`examples/shared/replicate_tool.py` is generation-only. Consequences:

- **image_pipeline / storyboard / npc / style_convert** generate images blind:
  no prompt-match check, no best-of-N selection, no character-consistency
  check across storyboard frames. A bad generation is discovered by a human,
  downstream.
- **DeviantArt posting** (the AI art pipeline referenced in
  `docs/Analyzing YAML-Driven LangGraph Repositories.md`) requires manually
  authored titles/descriptions/tags per image — the one step that keeps the
  pipeline from running unattended.

## Ideal Result

Any graph can ask a question about an image with one tool call and get a
typed answer. The DeviantArt pipeline runs generate → describe → post without
a human in the captioning loop; image pipelines gate their own outputs
(regenerate on mismatch) instead of shipping blind.

## Proposed Solution

`examples/shared/vision_tool.py`, following the `replicate_tool.py` /
`websearch.py` conventions:

```python
from examples.shared.vision_tool import describe_image

result = describe_image(
    image="outputs/images/concept_3.png",   # path or URL
    instruction="Title, 2-sentence description, and 8 DeviantArt tags.",
)
```

- Provider via the existing `create_llm()` factory with a vision-capable
  model (e.g. `google`/Gemini or `anthropic`); provider selection follows the
  standard priority chain. Image encoded as a base64/URL content part on a
  multimodal message — contained inside the tool, not in core.
- Structured output via Pydantic (`ImageDescription`: `title`, `description`,
  `tags`, optional `matches_prompt: bool` + `notes` for QA use).
- Declared in graphs as a plain `type: python` tool; once FR-768 lands, it
  becomes a manifest-declared shared capability.

Consumer wiring (separate follow-up work, out of this FR's scope beyond one
demo): a `deviantart_post` graph (generate → describe → post via DeviantArt
API tool) and a QA gate node in image_pipeline.

## Provider/Model Support Matrix (folded from judgement R-1)

Initial allowlist, enforced **before** any LLM invocation:

| Provider | Model source | Required env | Unsupported behavior |
|---|---|---|---|
| `google` | `GOOGLE_MODEL` or `gemini-2.0-flash` | `GOOGLE_API_KEY` | `ValueError` naming provider/model and the supported set, raised before the LLM call |
| `anthropic` | `ANTHROPIC_MODEL` or `claude-haiku-4-5` | `ANTHROPIC_API_KEY` | same |

Any provider/model outside the allowlist is rejected up front — the tool
distinguishes *unsupported* (pre-call `ValueError`) from *failed call*
(provider exception propagates). No core provider-capability changes.

## Demo Specification (folded from judgement R-3)

- Path: `examples/demos/shared-vision-tool/`
- Fixture strategy: committed tiny fixture image (no live generation step)
- Commands: `yamlgraph graph lint examples/demos/shared-vision-tool/graph.yaml`
  and one `yamlgraph graph run ... --full` (API-key guarded)
- Evidence: committed `examples/demos/shared-vision-tool/demo-output.log`
- **No consumer wiring** into image_pipeline, storyboard, npc, style_convert,
  or any DeviantArt posting graph under this FR.

## Required Test Cases (folded from judgement R-4)

1. Local image path is read, encoded into a multimodal message, and sent
   through a mocked `create_llm()` chat model.
2. URL input is passed as an image URL content part without local file reads.
3. Returned content is validated into `ImageDescription`.
4. Missing local path raises `FileNotFoundError`/`ValueError` naming the path.
5. Unsupported provider/model raises `ValueError` naming provider/model and
   supported set before any LLM invocation.
6. Malformed model output raises a Pydantic validation error — no
   success-shaped fallback.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `examples/shared/vision_tool.py` defines `ImageDescription` as a
      Pydantic model and `describe_image(image: str | Path, instruction: str,
      *, provider: str | None = None, model: str | None = None) ->
      ImageDescription`.
- [ ] AC-02: `describe_image()` constructs its chat model through
      `yamlgraph.utils.llm_factory.create_llm()` only; no direct provider SDK
      imports.
- [ ] AC-03: The provider/model allowlist is enforced before invocation;
      unsupported provider/model raises `ValueError` naming the actual
      provider/model and supported set.
- [ ] AC-04: Local missing/unreadable images raise a clear exception naming
      the path; URL inputs are accepted as URL content parts; no error path
      returns a success-shaped `ImageDescription`.
- [ ] AC-05: Unit tests mock `create_llm()` and cover the six required test
      cases above; every Tier 1 test carries the new `REQ-YG-XXX` marker.
- [ ] AC-06: A guarded integration test runs only when the selected provider
      API key is present and otherwise skips explicitly.
- [ ] AC-07: `examples/demos/shared-vision-tool/graph.yaml` lints and has a
      committed `demo-output.log` from the commands named above.
- [ ] AC-08: `examples/shared/README.md` documents Python usage, graph
      `type: python` declaration, the provider/model matrix, required env
      vars, and failure modes.
- [ ] AC-09: A new `capabilities/CAP-XXX-shared-vision-tool.yaml` declares
      the shared vision tool requirement and maps it to implementation/tests
      (judgement R-2).
- [ ] AC-10: A changelog fragment is added under `changelog/unreleased/` with
      `req:` set to the new requirement ID.

## Alternatives Considered

- **Vision as a core node type** (`type: vision`): rejected — a python tool
  needs zero core changes; promote to core only if a second shape of demand
  appears (`does_the_platform_already_do_this` inverted: don't build platform
  machinery for one call pattern).
- **Replicate captioning model** instead of multimodal LLM: rejected —
  instruction-following (titles, tags, QA verdicts) needs a prompted LLM, not
  a fixed captioner; and `create_llm()` keeps provider choice open.
- **Manual captioning status quo**: the one human step blocking an otherwise
  automatable pipeline.

## Prior Art (dispositioned)

- `examples/shared/replicate_tool.py` — generation-only; this is its
  read-direction complement, same module conventions.
- No prior FR proposes image *understanding*; FR archive grep for
  vision/multimodal/caption returns only research notes
  (`docs/plan-research-ecosystem-2025-2026.md` lists multimodal pipelines as
  a future pattern — this FR is its first concrete instance).

## Related

- FR-768 (tool manifests) — this tool is an intended early manifest-declared
  shared capability.
- `examples/image_pipeline/`, `examples/storyboard/`, `examples/npc/`,
  `examples/style_convert/` — QA consumers.
