# Feature Request: Refuse unconstrained objects on Anthropic-bound nodes

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented (2026-09-27) — yamlgraph #732 (`2b62085e`), released in 0.6.2; digest #6 (`9594d910`); production witness run 36375149984 (2026-09-28, 7 stories) (see [Implementation record](#implementation-record))
**Effort:** 2.5 days (framework and parity 1 day; linter extraction 0.5 day; nine ledger rows across six briefs plus the external digest 1 day)
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

### S-1: One walker, one typed finding, two rules (R-2)

`yamlgraph/utils/schema_walk.py` gains one immutable typed result and
one unified entry point:

```python
class SchemaFinding(NamedTuple):
    path: str
    kind: Literal["untyped", "open_object"]

def find_unconstrainable(schema: dict) -> list[SchemaFinding]: ...
```

Traversal is the existing deterministic `_walk` order, each path
emitted once: `$defs` entries under canonical `$defs.<name>...` paths,
a `$ref` occurrence is a stop and never a second finding, compositions
branch, then `properties` and `items`. `untyped` keeps FR-1123's rule
and paths exactly. `open_object` is exactly a concrete subschema whose
`type == "object"` and whose `properties` is absent or an empty
mapping, regardless of `additionalProperties`; an object with at least
one declared property is never open. `find_untyped_subschemas` and a
new `find_open_objects` remain only as tested projections of
`find_unconstrainable` for existing callers and focused tests.

`refusal_message` is per kind, and one error may carry several
findings, each keeping its own path and fix. The untyped fix no longer
recommends `dict` or `list[dict]`. The open-object fix names the path,
the hollowing (`{}` is the only instance), the `output_schema`
properties cure, and the provider alternative:

```
Prompt 'rank_stories' (node 'rank_stories', model 'provider default'):
field 'stories.items' is an object with no declared properties;
Anthropic constrained decoding reduces it to {} and the model can only
answer empty. Declare its properties with the output_schema form
(items: {type: object, properties: {...}}) or use a provider that
accepts open objects.
```

### S-2: The three surfaces, and the linter extracted (R-5)

`bind_structured_output` (an actual Anthropic model under effective
`json_schema`), `refuse_static_anthropic_node` (compile) and the linter
consume `find_unconstrainable`. Non-Anthropic providers and explicit
`function_calling` are untouched; FR-1123's static resolution decides
scope (C-2).

`yamlgraph/linter/checks_prompts.py` is 426 lines on `main`, against
the 450 maximum. The FR-1123 constrainability check and this FR's
extension move to a new `yamlgraph/linter/checks_schema.py` exporting
one `check_unconstrainable_schemas`, wired from `graph_linter.py`;
prompt rendering and complexity checks stay in `checks_prompts.py`,
which ends below 400 lines. E016/W028 keep their issue contract
byte-for-byte for `untyped`; **E017** (statically Anthropic) and
**W029** (provider chosen at run time) identify `open_object` only.
An import-boundary witness and a linter-registration witness prove the
extraction cannot silently drop either class.

### S-3: Parity on content, reference-aware and bounded (R-3)

In `tests/unit/test_fr1123_sdk_parity.py`, the only module importing
the SDK's private transform:

1. Run the existing missing-keyword oracle first; if `transform_schema`
   raises that exact error, compare only `untyped` findings as FR-1123
   does.
2. For a successful transform, enumerate concrete object nodes of the
   source schema by canonical path: `$defs` under `$defs.<name>`, stop
   at `$ref`, never dereference a reference into a second synthetic
   path (C-5).
3. For each source object with absent or empty `properties`, the
   transformed object at the same canonical path must equal
   `{"type": "object", "properties": {}, "additionalProperties": false}`.
4. For each source object with declared properties, the transformed
   object at the same canonical path must preserve exactly the source
   property-name set; transform-added `title`, `required` and
   `additionalProperties` are ignored except where item 3 requires them.

Fixtures: root objects, nested properties, array items, absent versus
empty `properties`, every supported composition branch, `$defs` plus
`$ref`, `additionalProperties: true`, dict-valued `additionalProperties`,
the spike's four forms, FR-1123's fixtures, and every committed prompt
schema. Any unrelated SDK exception propagates. No production code
imports the private module.

### S-4: The frozen migration ledger (R-1)

`scripts/fr1125_open_object_census.py` (deterministic: every committed
graph under `examples/`, `graphs/`, `.github/`; top-level `llm`/`router`
nodes and map sub-nodes; FR-1123's static provider resolution with the
`PROVIDER` environment variable ignored so the ledger is host-independent;
prompt schema loaded as the linter loads it) produced
[docs/issues-2026-09-27-fr1125-census.md](../docs/issues-2026-09-27-fr1125-census.md)
on 2026-09-27: **41 rows in 33 prompt files — 9 anthropic, 3 runtime,
29 other, 0 errors**. The ledger's mechanical section is reproduced by
the script and checked by a test (AC-08); its dispositions section is
frozen here and in the ledger:

| class | rows | disposition |
|---|---|---|
| anthropic | 9 | 8 × option 1 (declare properties verbatim from the field's description) through five briefs; 1 × option 2 (`questionnaire#classify` → `provider: mistral`; keys are field ids, unknown ahead of time; operator decision 2026-09-27 per C-7) |
| runtime | 3 | W029 stands; not edited |
| other | 29 | not edited; listed |

Briefs, all committed under `feature-requests/authoring-briefs/`:
`fr-1125-book-translator-properties-brief.md` (3 prompts),
`fr-1125-yamlgraph-gen-properties-brief.md` (3 prompts),
`fr-1125-req-witness-audit-properties-brief.md` (1 prompt),
`fr-1125-example-ranker-properties-brief.md` (1 prompt),
`fr-1125-questionnaire-provider-brief.md` (1 graph node), and, for the
external digest, `fr-1125-digest-ranker-properties-brief.md`. Each
brief freezes the exact target schema, consumers and validation
commands; a prompt with more than one consumer (none in the anthropic
class) may be edited only after the ledger shows the narrowed schema
valid for every consumer. FR-1123's R4 census table is updated to the
final types of its retyped rows.

### S-5: The digest and the production gate (R-4)

`sheikkinen/yamlgraph-daily-digest/prompts/rank_stories.yaml` is retyped
to the `output_schema` form with `title`, `url`, `summary`, `relevance`,
`reason` on each item (the spike's form C) through `scripts/author.sh`
with `fr-1125-digest-ranker-properties-brief.md` and `AUTHOR_WORKDIR` at
that checkout; `examples/daily_digest/prompts/rank_stories.yaml` is
retyped identically under its own brief. The digest's FR-1121 raise-only
transform witness becomes a content witness (the transformed `$defs`
item keeps exactly the five keys and requires all five); the FR-905
`RankedStory` boundary stays.

Production witness: the **first post-merge scheduled run that invokes
`rank_stories` with one or more analysed articles**. Recorded in the
digest repository's implementation record and copied here: run id,
analysed count, the content witness, the archived-bulletin line, the
sent-bulletin line, and a non-zero story count. A scheduled run with no
articles is recorded as a legitimate no-input run and does not satisfy
the gate; a ranker-invoking run that returns zero or fails is a failed
gate (C-8). It is supporting operational proof, never a substitute for
the offline content-parity and graph-path tests.

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

The judgement's revised list is binding; it replaces the original
AC-01..AC-11.

- [ ] AC-01: Before production implementation, FR-1125 folds R-1 through R-6, commits `docs/issues-2026-09-27-fr1125-census.md`, resolves every static-Anthropic row to one exact human-approved disposition, names every required authoring brief, and updates its effort estimate.
- [ ] AC-02 (RED): a commit preceding production implementation proves exact `SchemaFinding` results for root `dict`, nested `dict`, `list[dict]`, absent versus empty properties, the five-property ranker schema, `$defs`/`$ref`, compositions, and both `additionalProperties` forms; the failure is missing open-object detection, not import or fixture setup. GREEN lands in a later commit.
- [ ] AC-03: unified findings are deterministic and duplicate-free; projections preserve all existing `find_untyped_subschemas` paths; the untyped message contains no `dict`/`list[dict]` recommendation; the open-object message names the path, hollowing behavior, `output_schema` property cure, and provider alternative.
- [ ] AC-04: `bind_structured_output` raises `UnconstrainableSchemaError` before `with_structured_output` for an actual Anthropic model under effective `json_schema`, with every finding and fix represented. Spies prove no unified walker call for non-Anthropic models or explicit `function_calling`.
- [ ] AC-05: compiling a static-Anthropic fixture with an open object fails before any node executes and names node, prompt, model, path, and kind; `graph run` exits non-zero. A state-derived provider compiles and is protected by the runtime binder.
- [ ] AC-06: lint emits `E016`/`W028` only for untyped findings and `E017`/`W029` only for open-object findings; fixtures cover static Anthropic, unresolved provider, explicit Mistral, both defect kinds in one schema, and a declared-property `output_schema`. Existing FR-1123 linter assertions pass unchanged.
- [ ] AC-07: `tests/unit/test_fr1123_sdk_parity.py` implements the R-3 canonical-path oracle over all named fixtures and every committed prompt schema; no declared property is lost, every flagged open object becomes the exact hollow triple, unrelated SDK errors propagate, and the private SDK import remains confined to that module.
- [ ] AC-08: the census script reproduces the committed ledger exactly from every committed `llm`/`router` graph and reports graph, node, prompt, path, provider resolution, class, and disposition. A mismatch, undocumented row, or static-Anthropic open object fails the census test.
- [ ] AC-09: every graph or prompt edit in the frozen ledger is produced through `scripts/author.sh` from its exact committed brief; each run yields a verified non-empty transient `tmp/draft-authoring-report.md`, and the FR records authored paths, precedent, before/after lint identities, smoke result or exact blocked reason, and repairs.
- [ ] AC-10: both ranker prompts have the exact five-property schema frozen in their briefs; their transformed `$defs` object preserves exactly those five keys and requires all five; FR-905's typed boundary stays unchanged; every retained FR-905 and FR-1121 test passes.
- [ ] AC-11: FR-1123's R4 type assertions are replaced by the exact final types from the folded ledger, and all FR-1123 walker, provider, compile, lint, parity, and census tests remain green without weakened assertions.
- [ ] AC-12: the first qualifying standalone-digest run satisfies R-4 with a non-zero story count and archived/sent evidence; a no-input run does not complete this criterion.
- [ ] AC-13: `checks_prompts.py` is below 400 lines after the R-5 extraction, each affected module remains below 400 lines, `ruff check` on changed Python files, focused FR-1123/FR-1125 tests, the full unit suite, `python scripts/req_coverage.py --strict`, and `lint-imports` all exit 0.
- [ ] AC-14: CAP-164 / REQ-YG-712 names both unconstrainable finding kinds; FR-1121 and FR-1123 record the evidenced deviation; linter/reference documentation, changelog fragment, FR implementation record with RED/GREEN SHAs and exact validation results, and a Distill entry with `**Seed:**` are present.

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

## Judgement fold (2026-09-27)

[Judgement](FR-1125-refuse-unconstrained-objects-anthropic.judgement.md):
APPROVED WITH REVISIONS. Folded the same day:

- **R-1** → S-4: the census was run at planning time and committed as
  `docs/issues-2026-09-27-fr1125-census.md` (41 rows; 9 anthropic); every
  anthropic row has one frozen disposition; the one row whose keys are
  unknown (`questionnaire#classify`, `corrections`) takes option 2,
  `provider: mistral`, by operator decision; six briefs named; effort
  updated.
- **R-2** → S-1: `SchemaFinding`, `find_unconstrainable`, canonical
  traversal, projections, per-kind messages without the `list[dict]`
  recommendation.
- **R-3** → S-3: content parity by canonical concrete-object path, `$ref`
  as a stop, hollow triple for open objects, property-set preservation
  otherwise, bounded fixture set.
- **R-4** → S-5: the production gate is the first ranker-invoking run,
  not the next run.
- **R-5** → S-2: `checks_schema.py` extraction with import-boundary and
  registration witnesses; E017/W029 for open objects only.
- **R-6** → AC list replaced by AC-01..AC-14; CAP-164 / REQ-YG-712
  extended to both finding kinds, no new capability.

### Second wave (2026-09-27, same day): the census was host-dependent

The R-1 ledger was produced on a host whose `.env` sets `PROVIDER=deepseek`;
importing yamlgraph loads that file, so every graph naming no provider
resolved to a non-Anthropic default locally, while on the Linux runner the
built-in default (`anthropic`) applies. The first CI run of the fix PR
therefore found **17 static-Anthropic open-object rows** the ledger had
classed as **other**. The census script now neutralises `PROVIDER` after
the import; the regenerated ledger is the record. Dispositions, per C-7,
with the operator's decisions of 2026-09-27:

| rows | prompts | disposition | brief |
|---|---|---|---|
| 2 | `cwe-classifier/reason_cluster.candidates`, `icpc-2-rfe/reason_cluster.candidates` | option 1 ("EXACTLY these keys" named) | `fr-1125-cwe-classifier-properties-brief.md`, `fr-1125-icpc-2-rfe-properties-brief.md` |
| 2 | `demos/fr-atlas/chunk_themes.themes`, `merge_themes.themes` | option 1 | `fr-1125-fr-atlas-properties-brief.md` |
| 1 | `demos/ramp_rtm/derive_reqs.entries` | option 1 | `fr-1125-ramp-rtm-properties-brief.md` |
| 6 | `novel_fandom/{find_plot_path,fix_plot_path}.beats`, `reconcile_threads.{threads,dropped}`, `threads_from_synopsis.threads`, `throughlines.throughlines` | option 1 | `fr-1125-novel-fandom-properties-brief.md` |
| 1 | `novel_fandom/extract_consequences.ops` (polymorphic) | option 1, **operator decision**: `op` required plus every op-specific field the description names, optional | same |
| 1 | `novel_fandom/semantic_dedup.merge_map` (map keyed by ids) | option 2, **operator decision**: node `compare` → `provider: mistral` | same |
| 4 | `api-discovery/prompts/synthesize` `$defs…sample_response`, `steps/schema-extract/{ckan,openapi,unsupported}.sample_response` (free-form) | option 2, **operator decision**: nodes `synthesize`, `summarize_openapi`, `extract_ckan`, `unsupported_family` → `provider: mistral` | `fr-1125-api-discovery-provider-brief.md` |

Also in the second wave, test-only: `tests/unit/test_router.py`,
`test_issues.py`, `test_router_race.py` compile fixtures against the
framework's `GenericReport` (open `sections`/`metadata` maps) with no
provider; they now pin `PROVIDER=mistral` via an autouse fixture. No
committed graph uses that model. Effort revised: 3 days.

Scope frozen to the judgement's D-1..D-9; conditions C-1..C-8 are
gates. Judge rendered from the author's session via the sole route,
as recorded for FR-1121..FR-1124.

## Related

- `docs/spikes/constrained-object-2026-09-27/` (probe, raw outputs,
  results).
- `yamlgraph/utils/schema_walk.py`, `yamlgraph/utils/structured_output.py`,
  `yamlgraph/linter/checks_prompts.py`, `tests/unit/test_fr1123_*.py`.
- Digest run 36335550129; digest PRs #4, #5.
- `anthropic/lib/_parse/_transform.py` (SDK 1.3.0) and the API's
  `additionalProperties` rule.

## Implementation record

**Enforced 2026-09-27**, branch `fix/fr1125-open-objects`, rebased onto `main` after #730; squash-merged as `2b62085e` (#732). The two second-wave demo-proof commits landed after the auto-merge fired and follow in their own docs PR.

| Step | Commit | Evidence |
|---|---|---|
| RED | `027e45bc` | `tests/unit/test_fr1125_open_objects.py` (25 failures on behaviour: nothing flagged, no E017/W029, check not extracted), `test_fr1123_sdk_parity.py` content oracle (9 failures: hollowed objects unflagged), `test_fr1125_census.py` (9 Anthropic rows remain). |
| GREEN framework | `98663e77` | `schema_walk.SchemaFinding`, `find_unconstrainable` + projections, per-kind messages (no `list[dict]` recommendation); binder and compile on unified findings; `linter/checks_schema.py` extracted (`checks_prompts.py` 373 lines); E016/W028 kept, E017/W029 added; content parity by canonical path; CAP-164 / REQ-YG-712 wording; CONF-492. |
| GREEN lint scope | `19124548` | lint walks map sub-nodes like compile (the baselines showed 1 E017 where the census had 3 Anthropic rows in book_translator); witness `test_ac06_lint_sees_map_sub_nodes`. |
| Migration | `1f47aff8` | six authoring runs, all wrapper-verified this time (real `yamlgraph.exe` on PATH); nine rows per the ledger; questionnaire `classify` → `provider: mistral`; FR-1123 R4 split into fields-form and declared-property tables; ledger regenerated (33 rows, anthropic 0). |
| FR-1121 witness | `b4b67712` | the example ranker's transform witness asserts preserved content. |

Lint identity sets before/after each authoring run (same command; my own
captures): E017 removed from book_translator, yamlgraph_gen,
questionnaire, daily_digest; req_witness_audit had no top-level
diagnostic either way (its row was a map sub-node, which lint now sees);
every other code unchanged. Adapter reports for the six runs list the
briefed artifacts and ran lint, validate and the focused tests
themselves (report copies `tmp/author-report-fr-1125-*.md`, transient).

### Digest (`sheikkinen/yamlgraph-daily-digest`, PR #6)

Authored from `fr-1125-digest-ranker-properties-brief.md` with
`AUTHOR_WORKDIR` at that checkout; the FR-1121 and FR-905 transform
witnesses now assert the five preserved fields. Suite on an isolated
`yamlgraph==0.6.1`: 69 passed, 1 Windows-CRLF-only failure (vendored
hash). Production witness (R-4, C-8): pending the first post-merge
scheduled run that invokes `rank_stories` with articles; record its run
id, analysed count, archived and sent lines, and story count here.

### Deviations and route notes

- Release 0.6.2 preparation: the strict confession hook could not parse
  CONF-492's `Where:` and bold-colon field labels. Normalized the existing
  entry to the established `File` link and `Code` format; no suppression or
  checker change. `python scripts/noqa_coverage.py --strict` then reported
  259 suppressions, 347 documented entries, and zero undocumented suppressions.
- **The "empty lint output" in every earlier adapter report had one
  cause, now removed:** an extension-less `yamlgraph` shim script placed
  first on PATH for the outsider launcher. The adapter runs its
  validation through PowerShell, which opened the shim in a text editor
  instead of executing it. The FR-1121 and FR-1122 records are corrected
  in this commit. With `.venv/Scripts` first on PATH the six FR-1125
  runs validated correctly and the wrapper passed each time.
- A first attempt at the chain was stopped when the shim was found; the
  adapter had edited seven prompt files by then; all were reset with
  `git checkout -- examples/` before the rerun.
- `test_fr702_recap_disposition::test_graph_lint_stays_clean` fails on
  this host because the optional z3 solver is absent (W806 info);
  unrelated, passes on CI.
- `test_ac07_private_sdk_import_lives_in_one_test_module` fails on this
  host on path separators only (task filed); passes on CI.

### Demo proof (req_witness_audit)

The CI demo-proof gate requires a fresh `demo-output.log` for a changed
demo. The constructor (`scripts/req_audit_questions.py`) needs a
`.coverage` database this host lacks, so the narrowest honest smoke was
run instead: one hand-built batch of two real requirements
(REQ-YG-712, REQ-YG-664) through the demo graph on `claude-haiku-4-5`
under constrained decoding with the retyped `audit_batch.yaml`. The run
completed and every verdict carries `req_id`, `witnessed`, `gap` and
`suggestion`; the first verdict's gap ("AST linkage … omits
checks_schema.py, which is declared as a module for this requirement")
is a real observation about this very PR. The previous log was a
postponement marker (FR-1073); this one is a run.

### Second wave enforcement (2026-09-27)

Six more authoring runs in the worktree, one per brief
(`cwe-classifier`, `icpc-2-rfe`, `fr-atlas`, `ramp_rtm`, `novel_fandom`,
`api-discovery`): eleven prompts retyped with declared properties, the
polymorphic `extract_consequences.ops` as a union with `op` required, and
five nodes moved to `provider: mistral`. Five runs passed the wrapper; the
`ramp_rtm` run exited 65 on the known backslash-artifact-path defect with
the edit correct and verified by hand. The `api-discovery` run also
regenerated the ledger's mechanical table (outside its brief; the result
equals the script's output and was regenerated again by the enforcer).
Host-independent census after both waves: **21 rows, anthropic 0**; CI's
17 static-Anthropic rows are gone. Lint under the built-in default on
this host could not reproduce CI's E017 baselines (the worktree's `.env`
is read by the CLI), so the census, not lint, is the before/after
record for this wave: 17 → 0. `PROVIDER=mistral` autouse fixtures in
`test_router.py`, `test_issues.py`, `test_router_race.py`.

### Demo proofs, second wave (ramp_rtm, fr-atlas)

Both demos changed in the second wave, so the CI demo-proof gate needs a
fresh log for each; both were run live on `claude-haiku-4-5` under
constrained decoding with the retyped prompts, `PROVIDER=anthropic` set
explicitly because the worktree's `.env` would otherwise route them to
deepseek.

- `ramp_rtm` on its committed fixture `tests/fixtures/ramp_target`: two
  test files, two map branches, five requirement entries each carrying
  `req_id`, `statement`, `witness_tests`, `confidence`, `status:
  proposed` (`examples/demos/ramp_rtm/demo-output.log`).
- `fr-atlas` on a small project of this week's FR-1121..FR-1125 files
  plus CAP-164 (the full repository is hundreds of calls): chunk themes
  and merged themes carry `name`, `arc`, `fr_ids` / `merged_from`, and
  the atlas was written (`examples/demos/fr-atlas/demo-output.log`,
  engine log lines plus an output summary: the `--full` state dump quotes
  the FR texts, whose incident wording trips the gate's fatal-marker
  scan). The model's first theme, "Schema Validation and Type Safety …
  preventing silent failures and empty results in constrained decoding",
  is this FR describing itself.

### Production witness recorded (2026-09-28)

Manual `workflow_dispatch` run [36375149984](https://github.com/sheikkinen/yamlgraph-daily-digest/actions/runs/36375149984),
2026-09-28 03:49Z, digest `main` at `9594d91` (after #6), yamlgraph
**0.6.2** from PyPI: 32 new articles filtered, `Analysed 32 of 32 - 0
skipped`, `Node rank_stories completed successfully`, bulletin archived
as `digests/2026-09-28.md` with **7 stories**, mail sent, commit
`09527c2` pushed. First bulletin since 2026-09-18. Outcome 1 of the
three-way invariant; the ranker was invoked with articles and returned a
non-zero story count.
