# Feature Request: FR-795 — Endpoint-Probe Prompt Schema Dialect Repair

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced 2026-08-15 - AC-01..AC-07 delivered; authoring adapter report verified, graph lint and smoke passed, and 20/20 endpoint-probe tests passed (REQ-YG-586)
**Effort:** 0.25 day
**Requested:** 2026-08-14
**First consumer / first event:** any caller of
`yamlgraph.compile.graph_loader.load_and_compile()` on
`examples/api-discovery/steps/endpoint-probe/graph.yaml` (FR-785,
merged) — the graph currently fails to compile at all, discovered while
validating FR-794's manifest-root-confinement fix.

## Summary

`examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml`
declares its output under the native `schema:` dialect
(`yamlgraph/schema_loader.py::build_pydantic_model`) but writes
JSON-Schema-style content inside it: `live_endpoints` is declared as
`type: list` with a nested `items: {type: object, fields: {...}}`
sub-schema. The native dialect has no `items:` concept at all and only
accepts `list[T]` generics for simple `T` — this is a dialect mismatch,
not a supported construct. Loading the graph raises:

```
ValueError: Unknown type: 'list' for field 'live_endpoints'. Supported
types: str, int, float, bool, dict, Any, list[T], dict[K, V]
```

## Value Statement

`endpoint-probe` (FR-785, already merged and shipped) has never actually
been through a real `load_and_compile()` — this repair makes the graph
this repo already ships actually compile and run, closing the gap
between "19/19 tests green" (structural YAML assertions only) and "the
graph works."

## Problem

Two independent output-schema dialects exist in this codebase
(`yamlgraph/schema_loader.py`):

1. **Native `schema:` dialect** (`build_pydantic_model`): `fields:` keyed
   by name, `type:` values are `str`/`int`/`float`/`bool`/`dict`/`Any`/
   `list[T]`/`dict[K, V]`. No `items:` support — nested per-item typing
   is not implemented.
2. **JSON-Schema `output_schema:` dialect** (`build_pydantic_model_from_json_schema`):
   top-level `type: object`, `properties:`, `required:`; array fields
   use `type: array` + `items: {type: ...}` (also only maps `items.type`
   through `JSON_SCHEMA_TYPE_MAP`, so nested per-item property typing
   isn't implemented there either — a `list[dict]`-equivalent result
   either way).

`probe.yaml` mixes the two: `schema:` top-level key (dialect 1) with
`type: list` + `items:` content (dialect 2's shape). This was never
caught because `load_and_compile` on this graph always crashed earlier,
at the (now-fixed by FR-794) tool-manifest-loading step, before ever
reaching schema construction.

## Ideal Result

`examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml` uses
the `output_schema:` JSON-Schema dialect (matching the existing,
already-working convention in e.g. `examples/beautify/prompts/analyze.yaml`),
preserving exactly the same three output fields (`live_endpoints`,
`html_pages`, `verdict_hint`) and their intended semantics, so that
`yamlgraph.compile.graph_loader.load_and_compile()` on
`examples/api-discovery/steps/endpoint-probe/graph.yaml` succeeds with
zero other behavior change.

## Proposed Solution

Convert `probe.yaml`'s `schema:` block to `output_schema:`, preserving the
nested `live_endpoints` item contract as JSON-Schema `properties` (the
prompt's semantic guidance for the model, even though the loader
collapses object items to `dict` either way):

```yaml
output_schema:
  type: object
  properties:
    live_endpoints:
      type: array
      description: "Confirmed live API endpoints"
      items:
        type: object
        properties:
          url:
            type: string
            description: "Confirmed endpoint URL"
          status:
            type: integer
            description: "HTTP status code"
          content_type:
            type: string
            description: "Response content type"
          body_preview:
            type: string
            description: "First ~200 chars of response body"
        required:
          - url
          - status
          - content_type
          - body_preview
    html_pages:
      type: array
      description: "URLs returning HTML that need page-analysis"
      items:
        type: string
    verdict_hint:
      type: string
      description: "Optional hint like geo_blocked, auth_required, or null"
  required:
    - live_endpoints
    - html_pages
```

`live_endpoints` items still resolve to plain `dict` at runtime (the
JSON-Schema dialect's `build_pydantic_model_from_json_schema` maps
array `items.type: object` through `JSON_SCHEMA_TYPE_MAP` without
building a nested Pydantic model) — preserving `properties` keeps the
prompt's guidance to the model intact even though the loader doesn't
enforce it, matching the precedent in `examples/beautify/prompts/
analyze.yaml`. `verdict_hint` is omitted from the top-level `required`
list because the authored prompt intended it to be optional (the
native dialect's `required: false` marker doesn't exist in the
JSON-Schema dialect; omission from `required:` is how that dialect
expresses the same intent). This is a prompt artifact change and MUST
go through `scripts/author.sh` per the graph-authoring sole route — no
direct manual edit.

## Alternatives Considered

| Alternative | Why not |
|---|---|
| Extend the native `schema:` dialect to support `items:` | Framework runtime change, out of scope for a prompt-artifact repair; a separate FR if ever pursued. |
| Extend `build_pydantic_model_from_json_schema` to build real nested per-item Pydantic models from `items.properties` | Framework runtime change; also out of scope here — bundling it caused the judge's SPLIT verdict on the FR-794 attempt. |
| Leave `probe.yaml` broken, mark FR-785 as partially-shipped | FR-785 is already merged and "Enforced"; the graph should actually run. |

## Acceptance Criteria

- [x] AC-01: `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml` uses `output_schema:` with top-level properties `live_endpoints`, `html_pages`, and `verdict_hint`; `live_endpoints.items.properties` preserves `url`, `status`, `content_type`, and `body_preview`; `verdict_hint` is omitted from top-level `required`.
- [x] AC-02: `tmp/draft-authoring-report.md` exists, is non-empty, contains headings `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation`, and lists `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml` under authored artifacts.
- [x] AC-03: `yamlgraph graph lint examples/api-discovery/steps/endpoint-probe/graph.yaml` passes, or `tmp/draft-authoring-report.md` records that exact blocked command and reason.
- [x] AC-04: A regression test using `yamlgraph.compile.graph_loader.load_and_compile("examples/api-discovery/steps/endpoint-probe/graph.yaml")` passes without raising on the repaired prompt.
- [x] AC-05: No framework runtime files under `yamlgraph/**` change under this FR.
- [x] AC-06: No API-discovery artifact changes occur outside `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml`.
- [x] AC-07: Changelog fragment and diary reflection are added.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | The prompt edit MUST go through `scripts/author.sh <task-brief.md>`, verified by `tmp/draft-authoring-report.md` substance, never adapter exit code alone. | GATE |
| C-2 | No framework runtime code (`yamlgraph/schema_loader.py` or any other `yamlgraph/**`) may change under this FR — only the prompt artifact. | GATE |
| C-3 | No other API-discovery step graph, tool manifest, or orchestrator file may be touched. | GATE |

## Related

- FR-785 (endpoint-probe — the graph this repairs; merged, currently non-compiling)
- FR-794 (shared Python tool manifest root confinement fix — the sibling defect that unmasked this one; judge rendered a SPLIT verdict separating the two)
- `examples/beautify/prompts/analyze.yaml` (existing working precedent for the `output_schema:` dialect)

**Prior art:** No existing FR addresses this dialect mismatch. FR-794 attempted to bundle this repair into its own scope; the judge's SPLIT verdict (2026-08-14, `feature-requests/FR-794-python-tool-manifest-root-confinement-fix.judgement.md`) required it to re-enter the pipeline as this separate, graph-authoring-scoped FR.

**Judgement revisions folded:** R-1 (preserve nested `live_endpoints` item `properties` — `url`/`status`/`content_type`/`body_preview` — in the JSON-Schema conversion instead of collapsing to a bare `type: object`), R-2 (corrected optionality rationale: the JSON-Schema dialect expresses "optional" via omission from top-level `required:`, not a `required: false` marker) — see `feature-requests/FR-795-endpoint-probe-schema-dialect-repair.judgement.md`.

## Implementation Notes (2026-08-15)

- Added the compile regression witness first; it failed at `resolve_type()` with `Unknown type: 'list'`, confirming the mixed schema dialect as the remaining blocker.
- Ran `scripts/author.sh tmp/fr-795-authoring-brief.md` with `YAMLGRAPH_BIN` bound to the repository venv. The adapter converted only the governed prompt and produced a substantive `tmp/draft-authoring-report.md`.
- Preserved all three output fields and nested endpoint properties; `verdict_hint` remains optional through omission from top-level `required`.
- Verified graph lint, direct `load_and_compile()`, a structured-variable graph smoke, and the full endpoint-probe unit module. No files under `yamlgraph/**` and no other API-discovery artifacts changed.
