# Judgement: FR-1125 Refuse unconstrained objects on Anthropic-bound nodes

**Verdict:** APPROVED WITH REVISIONS — the Anthropic-bound open-object refusal is a sound extension of FR-1123, but authority activates only after the FR freezes the current-tree migration ledger and human dispositions, defines typed findings and a reference-aware content oracle, splits the near-limit linter module deliberately, and replaces the input-dependent production gate.

**Reviewed against:** `feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md`; `docs/spikes/constrained-object-2026-09-27/README.md`; `docs/spikes/constrained-object-2026-09-27/results.json`; `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md`; `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.judgement.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md`; `feature-requests/FR-1054-nested-object-schemas-reach-the-provider.judgement.md`; `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md`; `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.judgement.md`; `feature-requests/FR-905-ranked-story-boundary-validation.md`; `feature-requests/FR-1124-llm-node-default-on-error.md`; `feature-requests/TEMPLATE.md`; `feature-requests/authoring-briefs/fr-1125-example-ranker-properties-brief.md`; `feature-requests/authoring-briefs/fr-1125-digest-ranker-properties-brief.md`; `yamlgraph/utils/schema_walk.py`; `yamlgraph/utils/structured_output.py`; `yamlgraph/linter/checks_prompts.py`; `tests/unit/test_fr1123_sdk_parity.py`; `tests/unit/test_fr1123_prompt_census.py`; `capabilities/CAP-164-structured-output-fallback.yaml`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect is real, provider-specific, and supported by direct evidence rather than inference. The spike uses the digest's prompt and model and shows `list[dict]` transformed to an object with empty `properties` and returning `[]` twice, while the declared five-property `output_schema` returns three complete stories; the raw API independently rejects `additionalProperties: true` (`docs/spikes/constrained-object-2026-09-27/README.md:22-56`). The findings correctly distinguish a successful-but-hollow transform from FR-1123's loud missing-type rejection and identify the former as a semantic-content loss (`docs/spikes/constrained-object-2026-09-27/README.md:60-87`). This satisfies the substitute research record in substance: the FR dispositions six genuine alternatives, preserves the operator's no-fallback policy, and answers `is_this_a_graph` (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:16-24,270-287`).

The architecture is aligned with existing boundaries. FR-1123 already centralizes schema walking, static provider resolution, compile refusal, runtime refusal, and lint classification; `schema_walk.py` is pure and shared by those surfaces (`yamlgraph/utils/schema_walk.py:1-10,29-46,86-98`). Extending that primitive with a second finding kind is smaller and safer than adding consumer guards or a second provider policy. The proposed runtime gate remains limited to an actual Anthropic model under `json_schema`, while known non-Anthropic providers remain untouched (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:151-159`). The new `E017`/`W029` codes are unclaimed in the reviewed repository, and preserving `E016`/`W028` keeps the two defect classes observable.

The proposal is one responsibility. The walker rule, three refusal surfaces, parity witness, and migration of repository-owned prompts are the coordinated work required to turn on one invariant without knowingly breaking committed Anthropic consumers. Fallback policy, nested `fields:` grammar, inferred properties, and default node error handling are explicitly excluded (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:215-223`). Strategically this is a **framework primitive extension**: the spike counts 32 declarations in 26 prompt files and the invariant applies to every Anthropic-bound structured-output node, while the established FR-1123 abstraction supplies the correct extension point (`docs/spikes/constrained-object-2026-09-27/README.md:88-94`).

Most acceptance witnesses are directly derivable: exact walker paths, provider isolation, compile-before-execution, distinct lint codes, retained FR-1123 behavior, ranker schema content, traceability, and architecture gates are all stated as assertions (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:227-269`). The two committed ranker briefs also freeze exact five-property schemas and keep the YAMLGraph and standalone-digest repository boundaries separate.

Immediate authority is nevertheless unsafe. The FR says provider ownership for the 32 declarations is not established (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:100-103`), defers the census and ledger until implementation, leaves the ledger filename templated, and says the judge will later choose between inventing a shape and moving a node to another provider (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:173-190`). A judge cannot freeze unknown prompt edits or absorb that product/provider decision. The content oracle is also underspecified: it compares transformed values "at that path" without defining canonical paths through `$ref`/`$defs`, even though the proven working form reaches its object through exactly that structure (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:161-171`; `docs/spikes/constrained-object-2026-09-27/README.md:46-49`). Finally, the next scheduled run may legitimately have no input, so mandatory publication is not a deterministic test of this change (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:261-263`).

## Required revisions

### R-1: Freeze the complete migration ledger before authority

Run the deterministic current-tree census during planning and commit its populated result at the exact path `docs/issues-2026-09-27-fr1125-census.md`. Fold into the FR one row per graph/node/prompt/open-object path with these columns: graph, node, prompt file, schema path, static-provider result, every graph consumer of that prompt, disposition, exact target schema or unchanged reason, governing authoring brief, and validation command.

For every static-Anthropic row, replace "the judge decides" and "whatever those nine fields become" with one frozen disposition:

1. declare an exact `output_schema`, including property names, JSON types, required keys, and descriptions grounded in the prompt's existing contract; or
2. retain the open object only by naming the exact non-Anthropic provider to which the node will move.

**Human decision required:** for each row whose committed prompt does not establish its keys, the operator must choose option 1 or 2 in the FR. Recommended default: option 2, because inventing properties would contradict the FR's rejection of auto-declaration. No row may be deferred to enforcement, and changing a provider is authorized only when explicitly chosen in this table.

Name every committed authoring brief needed by the frozen rows. Keep the two existing ranker briefs and their exact five-property schemas. A prompt used by multiple graphs may be edited only after the ledger proves that the narrowed schema is valid for every consumer. Update the effort estimate after the exact number of Anthropic-bound migrations is known.

### R-2: Define one typed finding and exact traversal semantics

Specify one immutable typed result:

```python
class SchemaFinding(NamedTuple):
    path: str
    kind: Literal["untyped", "open_object"]
```

`find_unconstrainable(schema)` must return findings in the existing deterministic traversal order, with each path emitted once. Preserve the current rules that `$defs` entries use canonical `$defs.<name>...` paths and a `$ref` occurrence is a stop rather than a second finding. An `open_object` is exactly a concrete subschema whose `type == "object"` and whose `properties` value is absent or an empty mapping, regardless of `additionalProperties`; objects with at least one declared property are not open. The existing missing-type behavior and paths remain unchanged.

Make all three refusal surfaces consume `find_unconstrainable`; keep `find_untyped_subschemas` and `find_open_objects` only as tested projections if existing callers or focused tests require them. Define message aggregation when both kinds occur: one error may contain multiple findings, but every finding must retain its own kind-specific path and fix. The untyped fix must no longer recommend `dict` or `list[dict]`; the open-object fix must point to declared `output_schema` properties or a provider that accepts open objects.

### R-3: Make transformed-content parity reference-aware and bounded

Replace the current parity prose and AC-05 with this oracle contract in the existing sole private-SDK test module:

- Run the existing missing-keyword oracle first. If `transform_schema` raises that exact error, compare only the `untyped` findings as FR-1123 does.
- For a successful transform, enumerate concrete object nodes in the source schema using canonical paths. Visit `$defs` under `$defs.<name>` and stop at `$ref`; do not pretend that a reference occurrence and its definition share one physical path.
- For each source object with absent or empty `properties`, require the transformed object at the same canonical path to equal `{"type": "object", "properties": {}, "additionalProperties": false}`.
- For each source object with declared properties, require the transformed object at the same canonical path to preserve exactly the source property-name set. Ignore transform-added metadata such as `title`, `required`, and `additionalProperties` except where the open-object equality above requires them.

Cover root objects, nested properties, array items, absent and empty `properties`, all supported composition branches, `$defs` plus `$ref`, `additionalProperties: true`, dict-valued `additionalProperties`, the spike's four forms, FR-1123's fixtures, and every committed prompt schema. Any unrelated SDK exception propagates. Keep the private SDK import in exactly `tests/unit/test_fr1123_sdk_parity.py`; no production code may import it.

### R-4: Replace the input-dependent production gate

Replace "the next scheduled run archives and sends a bulletin" with the first post-merge scheduled run **that actually invokes `rank_stories` with one or more analysed articles**. Record the run ID, analysed count, transformed-schema/content witness, archived bulletin line, sent-bulletin line, and non-zero story count. A scheduled run with no articles is recorded as a legitimate no-input run but does not satisfy this gate; a ranker-invoking run that returns zero or fails remains a failed gate.

Keep this witness in the standalone digest repository's implementation record and copy its durable run ID and cited lines into FR-1125. It is supporting operational proof, not a substitute for the offline transform-content and graph-path tests.

### R-5: Split the linter surface deliberately

`yamlgraph/linter/checks_prompts.py` is already 426 lines before this change, against the repository's 450-line maximum. Do not leave "stay under the ceiling or split" as an enforcement-time choice. Move the existing FR-1123 constrainability check and its new FR-1125 extension into `yamlgraph/linter/checks_schema.py`, export one unified `check_unconstrainable_schemas`, and wire that function from `graph_linter.py`. Keep prompt rendering and complexity checks in `checks_prompts.py`.

The split must preserve `E016`/`W028` behavior byte-for-byte at the issue-contract level and add `E017`/`W029` only for `open_object`. Add import-boundary and linter-registration witnesses so extracting the module cannot silently omit either defect class.

### R-6: Fold the revised scope and criteria into the FR

Replace the current acceptance list with the criteria below, cite the exact ledger and all exact authoring briefs from R-1, update Status to judged with revisions, and state that implementation authority starts only after R-1 through R-6 and every required human disposition are folded. Extend CAP-164 / REQ-YG-712 to say "unconstrainable" and cover both finding kinds; do not create a new capability or requirement.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/schema_walk.py`: `SchemaFinding`, unified deterministic traversal/projections, kind-specific refusal messages, and unchanged static-provider policy |
| D-2 | `yamlgraph/utils/structured_output.py` and the existing compile caller: Anthropic-plus-`json_schema` runtime refusal and static-Anthropic compile refusal using unified findings |
| D-3 | `yamlgraph/linter/checks_schema.py` and `yamlgraph/linter/graph_linter.py`: extracted unified check with `E016`/`W028` preserved and `E017`/`W029` added |
| D-4 | Focused walker, binder, compile, CLI, linter, SDK-content-parity, and import-boundary tests under `tests/unit/`, all on `REQ-YG-712` |
| D-5 | `scripts/fr1125_open_object_census.py` and `docs/issues-2026-09-27-fr1125-census.md`, reproducing the exact folded current-tree ledger |
| D-6 | Only the prompt/provider migrations enumerated exactly by the folded R-1 ledger, authored from its named committed briefs through the sole graph-authoring route |
| D-7 | The two ranker prompt migrations and content witnesses frozen by `feature-requests/authoring-briefs/fr-1125-example-ranker-properties-brief.md` and `feature-requests/authoring-briefs/fr-1125-digest-ranker-properties-brief.md`, with repository boundaries kept separate |
| D-8 | FR-1121 and FR-1123 deviation records, CAP-164 / REQ-YG-712 update, linter/reference documentation, changelog fragment, FR implementation record, and Distill diary entry with `**Seed:**` |
| D-9 | The first qualifying post-merge standalone-digest production witness defined by R-4 |

Not authorized: any `function_calling` fallback or method downgrade; any change to FR-998's typed unsupported-`output_config` retry; any new provider policy not explicitly chosen in the folded ledger; inferred or auto-generated object properties; nested `fields:` grammar; provider-neutral rejection in `schema_loader`; changes to FR-905 validation semantics; changes to `on_error`; edits to a graph or prompt absent from the frozen ledger; changes to CI, hooks, judge/review doctrine, or graph-authoring doctrine; any Anthropic schema rule beyond missing-type and open-object findings.

## Revised acceptance criteria

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

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-6 and every required human disposition are folded into FR-1125. | GATE |
| C-2 | Refusal requires both Anthropic classification and effective `json_schema`; non-Anthropic and explicit `function_calling` behavior remain unchanged. | GATE |
| C-3 | No prompt or provider edit may occur unless the folded ledger names its exact disposition, all consumers, target schema/provider, and committed authoring brief. | GATE |
| C-4 | Every governed graph/prompt edit must use the sole authoring route; the YAMLGraph and standalone-digest checkouts remain separate repository boundaries. | GATE |
| C-5 | SDK content parity uses canonical concrete-object paths and never dereferences `$ref` into a second synthetic path or broadens into unrelated Anthropic schema rules. | GATE |
| C-6 | `E016`/`W028` retain their established meaning; only `E017`/`W029` identify open objects. | GATE |
| C-7 | Do not invent object properties. A missing committed key contract requires the operator's explicit provider-or-schema disposition before enforcement. | GATE |
| C-8 | A no-input scheduled digest run cannot satisfy the production witness; the gate closes only on a ranker-invoking run with non-zero archived and sent output. | GATE |

Authority granted: after R-1 through R-6 and the human dispositions are folded, implement the unified open-object extension, three Anthropic refusal surfaces, extracted linter check, bounded content-parity oracle, exact frozen migrations, ranker repairs, and records listed in D-1 through D-9—nothing else.
