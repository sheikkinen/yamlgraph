# Feature Request: Refuse unconstrained objects on Anthropic-bound nodes

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 2 days (framework 1 day; prompt disposition and digest retype 1 day)
**Requested:** 2026-09-27
**First consumer / first event:** `sheikkinen/yamlgraph-daily-digest` at
its next 06:00 UTC run, at the moment `rank_stories` is bound under
`json_schema`: today that node's `stories: list[dict]` reaches the model
as a list of empty objects and the ranker returns `[]` (run
36335550129, 2026-09-27 17:05Z). After this FR the digest's ranker
declares its five story fields and the bind refuses any remaining open
object before a token is spent. Second consumer: `yamlgraph graph lint`
on the 26 committed prompt files that carry `dict` or `list[dict]`.
**Research:** FR-890 route **not run, by operator decision (2026-09-27:
"no research")**. Substitute, per the TEMPLATE's equivalent-record
clause and the FR-1083 precedent: the live spike
[docs/spikes/constrained-object-2026-09-27/README.md](../docs/spikes/constrained-object-2026-09-27/README.md)
(#729; four schema forms, two binding methods, the digest's own prompt
and model, raw outputs committed, plus a raw-API call with the SDK
transform bypassed) and the in-body [Alternatives Considered](#alternatives-considered)
table with an `is_this_a_graph` answer. The policy choice itself was
made by the operator: refuse, do not fall back.
**Prior art:** [FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md)
built the walker, the three refusal surfaces (lint, compile, bind), the
SDK parity test and the static provider resolution this FR extends; it
refuses a *missing type*, recommends `list[dict]` in its message, and
migrated nine fields into that form. This FR adds the second rule the
same walker must know (an object with no `properties`), corrects the
message, widens the parity test from "raises" to "preserves content",
and re-dispositions those nine fields. [FR-998](FR-998-anthropic-constrained-structured-output.md)
forces `json_schema` for Anthropic and permits one forced-tool-call
retry on an unsupported-`output_config` 400 only; this FR does not
touch that policy and adds no fallback (the operator's decision).
FR-1054 added the `output_schema` prompt form in which an object with
declared `properties` becomes a nested model; that form is the cure
this FR points every refusal at. [FR-1121](FR-1121-daily-digest-ranker-schema-loud-failure.md)
retyped the digest's ranker to `list[dict]` under its judgement C-7 on
the "transform does not raise" witness; this FR records that as
FR-1121's deviation and retypes the ranker again, and does not re-open
FR-1121. [FR-905](FR-905-ranked-story-boundary-validation.md) is the
digest boundary that caught the empty ranking; unchanged.
[FR-1124](FR-1124-llm-node-default-on-error.md) is the default
`on_error` question; unrelated surface, named because both arise from
the same incident.

## Summary

Anthropic constrained decoding cannot express an object with unknown
keys: the API rejects `additionalProperties: true`, and the SDK's
transform, which langchain-anthropic applies to every model before the
request, rewrites an object with no declared `properties` into
`properties: {}` plus `additionalProperties: false`, a grammar whose only
instance is `{}`. yamlgraph's `dict`, `dict[str, Any]` and `list[dict]`
produce exactly that object, the framework sends it without comment,
the call succeeds, and the model answers `{}` or `[]`. FR-1123's gate
approves the form (it checks only for a missing `type`), its parity
test approves the form (it checks only whether the transform raises),
its message recommends the form, and its migration moved nine fields
into it. The digest's ranker returned zero stories on its first run on
0.6.1. This FR makes the framework refuse an open object on an
Anthropic-bound node at lint, compile and bind time, names the form that
works, proves the walker against what the transform *produces*, and
dispositions every committed prompt that carries the open form.

## Value Statement

A graph author who types a field `dict` or `list[dict]` on an Anthropic
graph learns at lint time that the provider will hollow it, with the
field named and the `output_schema` fix shown, instead of receiving
empty answers that pass every shape check.

## Problem

From the spike (digest ranker prompt, `claude-haiku-4-5`, 2026-09-27):

| Declared form | `json_schema` wire schema for the field | `json_schema` answer | `function_calling` answer |
|---|---|---|---|
| `stories: list[dict]` | `items: {type: object, properties: {}, additionalProperties: false}` | `{"stories": []}` (2 of 2) | 3 full stories |
| `stories: list[Any]` | transform raises (FR-1123 refuses) | no call | 3 full stories |
| `output_schema`, items with 5 `properties` | `$ref` to a `$defs` entry carrying all five, `required` | 3 full stories | 3 full stories |
| `stories: dict` | `{type: object, properties: {}, additionalProperties: false}` | `{"stories": {}}` | populated map |

Raw API with the transform bypassed and `additionalProperties: true`:
`400 invalid_request_error: For 'object' type, 'additionalProperties:
true' is not supported`. The hollowing is the API's rule; no client
change can keep `dict` semantics under `json_schema`.

The framework's current state on `main` (after #728):

- `yamlgraph/utils/schema_walk.py`: `find_untyped_subschemas` flags a
  missing `type` only; `refusal_message` ends "Declare a concrete type
  (e.g. list[dict], list[str]) or a nested schema."
- `tests/unit/test_fr1123_sdk_parity.py`: parity holds iff the walker
  flags exactly the schemas on which the transform raises; a hollowed
  schema passes.
- `tests/unit/test_fr1123_prompt_census.py`: nine fields pinned to
  `list[dict]` or `dict`.
- `git grep` on `main`: 32 declarations of `type: dict` / `type:
  list[dict]` in 26 files under `examples/**/prompts/`. Which of those
  graphs statically resolve to Anthropic is not yet established per
  file.

## Ideal Result

Under `json_schema` on an Anthropic-bound node, every subschema the
provider would hollow is refused where the schema enters, with the
prompt, node, path and the working form named; the refusal rule and the
SDK transform are proven to agree on *content*, not only on raising;
no committed prompt on an Anthropic-bound graph carries an open object;
the digest declares its five story fields and publishes bulletins with
stories again; and a prompt whose keys are genuinely unknown is either
declared for a provider that supports it or refused, never hollowed.

## Proposed Solution

### S-1: One walker, two rules

`yamlgraph/utils/schema_walk.py` gains, beside `find_untyped_subschemas`:

```python
def find_open_objects(schema: dict) -> list[str]:
    """JSON paths of `type: object` subschemas with no declared `properties`.

    Constrained decoding turns them into `properties: {}` +
    `additionalProperties: false`; the only instance is `{}`.
    """
```

Same traversal as `_walk` (`$defs`, `$ref` stop, compositions,
`properties`, `items`), same order. A subschema with `type: object` and
an empty or absent `properties` mapping is flagged regardless of its
`additionalProperties` value. `find_unconstrainable(schema)` returns
both rule sets as typed findings (`path`, `kind ∈ {untyped,
open_object}`) so the three surfaces call one function.

`refusal_message` is rewritten per kind. For `open_object`:

```
Prompt 'rank_stories' (node 'rank_stories', model 'provider default'):
field 'stories.items' is an object with no declared properties;
Anthropic constrained decoding reduces it to {} and the model can only
answer empty. Declare its properties with the output_schema form
(items: {type: object, properties: {...}}) or use a provider that
accepts open objects.
```

The `list[dict]` recommendation is removed from both kinds' messages.

### S-2: The three surfaces, unchanged in shape

`bind_structured_output` (Anthropic and `CONSTRAINED_METHOD`),
`refuse_static_anthropic_node` (compile) and the linter check call
`find_unconstrainable`. Lint reports `open_object` under new codes
**E017** (statically Anthropic) / **W029** (provider chosen at run
time), so the two classes are distinguishable in a lint report; E016/W028
keep their meaning. Non-Anthropic providers are untouched; the FR-1123
static resolution decides scope.

### S-3: Parity on content, not on raising

`tests/unit/test_fr1123_sdk_parity.py` (the one module importing the
SDK's private transform) gains a second oracle: for every fixture and
every committed prompt schema, run `transform_schema`; for each path the
walker flags as `open_object`, assert the transformed subschema at that
path is `{type: object, properties: {}, additionalProperties: false}`;
for every object path the walker does *not* flag, assert the
transformed subschema keeps every declared property. Fixtures: the
spike's four forms plus FR-1123's set. A schema whose transform raises
is the `untyped` class and stays under the existing oracle.

### S-4: Disposition of the 32 fields in 26 files

A deterministic script (`scripts/fr1125_open_object_census.py`, no
LLM) walks every committed graph, resolves each `llm`/`router` node's
static provider with `resolve_static_provider`, loads its prompt
schema, and lists every `open_object` path with the graph, node,
provider and whether the provider is Anthropic. The ledger is committed
as `docs/issues-<date>-fr1125-census.md`. Disposition:

- **Anthropic-bound (static):** retype to `output_schema` with declared
  `properties`, one `scripts/author.sh` brief per example directory
  under `feature-requests/authoring-briefs/`. The properties come from
  the prompt's own description of the object; where a description names
  no keys, the brief says so and the judge decides between a declared
  minimal shape and moving that node to a non-Anthropic provider.
- **Run-time provider (`{state.x}`):** W029 stands; listed, not edited.
- **Non-Anthropic (static):** listed with the provider; not edited.
  FR-1123's R4 census table is updated to whatever those nine fields
  become.

### S-5: The digest

`sheikkinen/yamlgraph-daily-digest/prompts/rank_stories.yaml` is retyped
to the `output_schema` form with `title`, `url`, `summary`, `relevance`,
`reason` on each item (the spike's form C, which returned three full
stories), through `scripts/author.sh` with
`feature-requests/authoring-briefs/fr-1125-digest-ranker-properties-brief.md`
and `AUTHOR_WORKDIR` at that checkout; `examples/daily_digest/prompts/rank_stories.yaml`
here is retyped identically under its own brief. The digest's FR-1121
transform witness is replaced by a content witness (the transformed
item schema carries the five properties); the FR-905 `RankedStory`
boundary stays. Production witness: the next scheduled run archives and
sends a bulletin whose `Analysed N of M` line and story count are both
non-zero.

### S-6: Records

FR-1121's implementation record gains a deviation entry citing the
spike and this FR (C-7 chose a hollow form on a raise-only witness).
FR-1123's implementation record gains the same. This FR adds FR-1125 to
CAP-164 and reuses `REQ-YG-712`.

### Not in scope

- Any fallback to `function_calling`, per field or per node: rejected by
  the operator; FR-998's single-retry rule is untouched.
- A nested grammar in the `fields` form: FR-1054's `output_schema`
  already expresses declared item properties.
- Auto-rewriting an open object into declared properties: the framework
  cannot know the keys.
- The `on_error` default (FR-1124).

## Acceptance Criteria

- [ ] AC-01: RED first: `find_open_objects` returns `["stories.items"]`
  for the digest's committed `list[dict]` schema and `["stories"]` for
  `dict`, `[]` for the spike's form C; fails on `main` (function
  absent); separate GREEN commit.
- [ ] AC-02: `bind_structured_output` on an Anthropic chat model under
  `json_schema` raises `UnconstrainableSchemaError` naming the path and
  the `output_schema` fix for `list[dict]` and `dict`; on a
  non-Anthropic model it does not call the walker; the message contains
  no `list[dict]` recommendation for either kind.
- [ ] AC-03: `compile_graph` on a fixture Anthropic graph with a
  `list[dict]` prompt raises the same error naming node, prompt and
  path; `graph run` exits non-zero before any node executes.
- [ ] AC-04: lint reports E017 for the static-Anthropic fixture, W029
  for a `{state.x}` provider, nothing for `provider: mistral`, nothing
  for the `output_schema` form with declared properties; E016/W028
  behaviour unchanged.
- [ ] AC-05: the parity test asserts, over the spike's four forms,
  FR-1123's fixtures and every committed prompt schema, that each
  `open_object` path is hollowed by the transform and each unflagged
  object path keeps its declared properties; the private SDK module is
  imported only there.
- [ ] AC-06: the census script and committed ledger list every
  `open_object` path in every committed graph with node, provider and
  class; every static-Anthropic path is retyped through the sole
  authoring route with a committed brief; every other path is listed
  with its reason; `yamlgraph graph lint` over the committed graphs
  reports no E017.
- [ ] AC-07: FR-1123's R4 census expectations are updated to the
  retyped forms and its test passes.
- [ ] AC-08: both ranker prompts (digest, example) use the
  `output_schema` form with the five item properties; the digest's
  content witness proves the transformed item schema keeps all five;
  every FR-905 and FR-1121 test other than the replaced raise-only
  witness passes unchanged.
- [ ] AC-09: the digest's next scheduled run after merge archives and
  sends a bulletin with a non-zero story count; run id and lines
  recorded in this FR.
- [ ] AC-10: FR-1121 and FR-1123 implementation records carry the
  deviation entry; FR-1125 is on CAP-164; new tests carry
  `@pytest.mark.req("REQ-YG-712")`; `python scripts/req_coverage.py
  --strict` passes.
- [ ] AC-11: `schema_walk.py` and `checks_prompts.py` stay under the
  module ceiling or are split; `lint-imports` passes; changelog
  fragment; Distill diary entry with a `**Seed:**`.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Per-field or per-node fallback to `function_calling` when a schema carries an open object | Rejected by the operator (2026-09-27). Would keep `dict` semantics on Anthropic at the price of two decoding methods in one graph and a silent policy split; FR-998 chose one method deliberately. |
| Warn (W-code) instead of refuse | Rejected. The failure mode is a green run with empty answers; a warning is advisory and the digest repository does not lint in CI (`detection_without_enforcement`). |
| Keep `list[dict]` and validate emptiness downstream (FR-905 style) per consumer | Rejected. Guards the symptom at every consumer; the cause is one schema boundary (`downstream_fix`). FR-905 stays as belt. |
| Auto-declare `properties` from the prompt text | Rejected. The framework cannot infer keys; a wrong inference is a quieter version of the same defect. |
| Extend the `fields` grammar with nested item types (`list[Story]`) | Deferred. `output_schema` already expresses it; a second grammar is scope for its own FR if authors reject the JSON-Schema form. |
| Rely on FR-1123's raise-only parity forever | Rejected. This incident is the proof that "does not raise" is not "carries the answer". |

`is_this_a_graph`: the gate is not. The census (S-4) is a deterministic
walk with static provider resolution and no model call, so it is a
script; declaring properties per prompt is authoring under briefs, not
a fan-out.

## Related

- `docs/spikes/constrained-object-2026-09-27/` (probe, raw outputs,
  results).
- `yamlgraph/utils/schema_walk.py`, `yamlgraph/utils/structured_output.py`,
  `yamlgraph/linter/checks_prompts.py`, `tests/unit/test_fr1123_*.py`.
- Digest run 36335550129; digest PRs #4, #5.
- `anthropic/lib/_parse/_transform.py` (SDK 1.3.0) and the API's
  `additionalProperties` rule.
