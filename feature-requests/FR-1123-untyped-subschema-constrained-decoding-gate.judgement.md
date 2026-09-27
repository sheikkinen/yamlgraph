# Judgement: FR-1123 Refuse untyped prompt-schema fields before constrained decoding

**Prior art:** dispositioned in the parent FR header ([FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md) — FR-998, FR-458, FR-456, FR-632, FR-1086, FR-1121, FR-1097); no REJECTED FR in this territory.

**Route:** `scripts/judge.sh` (copilot backend, `gpt-5.6-sol`), 2026-09-27; draft folded verbatim below.

**Verdict:** APPROVED WITH REVISIONS — the provider-bound schema gate is a sound framework primitive, but authority activates only after the FR resolves its provider-policy contradiction, uses the real compile seam and unclaimed diagnostic codes, limits parity to this defect class, and freezes the twelve schema migrations plus their authoring evidence.

**Reviewed against:** `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md`; `feature-requests/FR-1123.research.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `feature-requests/FR-458-openai-strict-schema-additional-properties.md`; `feature-requests/FR-456-structured-output-json-fallback.md`; `feature-requests/FR-632-pydantic-tojson-boundary.md`; `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md`; `feature-requests/FR-1086-lint-compile-check.md`; `feature-requests/FR-1086-lint-compile-check.judgement.md`; `yamlgraph/utils/structured_output.py`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/schema_loader.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/linter/checks_prompts.py`; `yamlgraph/linter/checks_providers.py`; `yamlgraph/linter/graph_linter.py`; `capabilities/CAP-164-structured-output-fallback.yaml`; the nine prompt files enumerated in FR-1123's Problem table; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/graph-authoring/adapters/README.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect is real, bounded, and evidenced. FR-1123:57-89 identifies the exact Pydantic schema shapes, provider rejection, and twelve committed fields; the committed inventory matches the cited prompt files. The research record preserves four genuine solution classes, records the failed persona instead of hiding it, corrects its initial overcount, dispositions the external compiler precedent, and answers `is_this_a_graph` negatively (`FR-1123.research.md:41-59`). That satisfies the research-substance gate rather than merely shape-checking it.

The minimal architecture is correct. `schema_loader.py` deliberately accepts `Any`, while `structured_output.py:40-46` is the single production binding policy that knows whether the actual model is Anthropic. Keeping the walker provider-neutral and applying it at the constrained-output boundary follows FR-998 and the repository's boundary-normalization doctrine. A static node-factory check plus the definitive binder check is justified: the first prevents upstream token spend when the provider is knowable at compile time, while the second protects direct callers and dynamically resolved providers.

The proposal is one responsibility, not a bundle. The walker, Anthropic compile/runtime refusals, lint feedback, and migration of repository-owned schemas are all necessary parts of turning on one invariant without leaving committed consumers broken. The nested-schema grammar, fallback policy, OpenAI strict rules, and default `on_error` policy are explicitly excluded at FR-1123:181-188.

The acceptance surface is largely testable. FR-1123:190-217 names direct assertions for paths, provider isolation, call ordering, compile-before-execution, SDK-oracle placement, module size, import boundaries, and requirement coverage. RED can be written against the current `list[Any]` schema without inventing absent modules or fixtures. Strategically this is a **framework primitive**: nine committed consumers already exhibit the forbidden shape, every Anthropic-bound YAML schema is a future consumer, and no existing abstraction performs this check.

Four defects prevent immediate authority. First, S-3 says only unresolved providers receive a warning, but its witness and AC-5 require the warning for known Mistral graphs (`FR-1123:144-152,166-168,205-208`), contradicting the Ideal Result and Alternatives claim that accepting providers remain untouched (`FR-1123:91-100,224`). Second, `create_llm_node` does not exist: compilation reaches `create_node_function` through `_compile_llm_node` (`node_compiler.py:250-255`; `llm_nodes.py:421-438`), and actual provider fallback is `provider or PROVIDER or "anthropic"` in `llm_factory.py:142`, not the resolution described by S-2. Third, active FR-1086 already owns `E015` (`FR-1086:40-45,100-106`; its judgement R-3), so FR-1123 cannot claim it. Fourth, comparing every SDK rejection with this one-keyword walker would silently expand the primitive to all present and future Anthropic schema rules; parity must classify only the cited missing-keyword rejection.

## Required revisions

### R-1: Freeze one provider-resolution and diagnostic policy

Replace S-3 and AC-5 with this exact policy:

- A statically resolved Anthropic node with an untyped subschema emits error `E016`.
- A statically resolved, known non-Anthropic node emits no issue.
- A provider that cannot be resolved statically emits advisory `W028`, stating that an Anthropic runtime selection would reject the named path.
- Resolution precedence is node provider, graph `defaults.provider`, `PROVIDER`, then the built-in `"anthropic"` default, using one pure helper shared with `create_llm`; a state-derived provider remains unresolved until execution.

Add FR-1086 and its judgement to Prior art, state that its active authority owns `E015`, and rename every proposed `E015` occurrence to `E016`. Record `W028` explicitly rather than saying “W-series.” Do not warn on an explicitly known Mistral, OpenAI, or other non-Anthropic provider.

### R-2: Name the real compile seam and bound what compile time can know

Replace every `create_llm_node` reference with the actual path: `_compile_llm_node` calls `create_node_function`, whose `resolve_llm_node_config` builds the output model. Run the shared walker there only when the pure provider resolver returns static Anthropic. The compile error must name node, prompt, model, and every offending JSON path.

State explicitly that a state-derived provider cannot be refused during compilation. It is protected later by `bind_structured_output`, which must inspect the actual Anthropic model before calling `with_structured_output`. In the binder, validate only when the actual model is Anthropic and the effective method is `json_schema`; an explicit `function_calling` override and every non-Anthropic model remain unchanged. Remove the broader wording “when the resolved method is `CONSTRAINED_METHOD`” because it would also gate a non-Anthropic caller that explicitly selects `json_schema`.

### R-3: Limit SDK parity to the defect class under authority

Define the oracle result as “Anthropic `transform_schema` raises the cited missing `type`/`anyOf`/`oneOf`/`allOf` schema error.” Compare that boolean with `bool(find_untyped_subschemas(schema))` for the five fixtures and the committed prompt census. A different SDK rejection is outside this parity assertion and must propagate from the oracle harness rather than force the walker to implement an unrelated provider rule.

Keep the private SDK import in exactly one slow test module and never production. Add nested fixtures for `properties`, `items`, `prefixItems`, each composition keyword, `$defs`, dict-valued `additionalProperties`, and accepted `$ref`, with exact JSON paths. This makes the proposed traversal contract measurable instead of testing only `stories.items`.

### R-4: Freeze all twelve prompt migrations

Replace “retyped or dispositioned” and “the judge decides” with this table and update descriptions that currently permit a wider shape:

| Prompt field | Required type |
|---|---|
| `daily_digest/rank_stories.stories` | `list[dict]` |
| `book_translator/extract_terms.terms` | `list[dict]` |
| `book_translator/identify_chapters.markers` | `list[dict]` |
| `book_translator/translate_chunk.difficult_passages` | `list[dict]` |
| `yamlgraph_gen/generate_tools.tools` | `list[dict]` |
| `yamlgraph_gen/assemble_graph.node_list` | `list[dict]` |
| `yamlgraph_gen/generate_prompts.prompts` | `list[dict]` |
| `codegen/plan_discovery.tasks` | `list[dict]` |
| `codegen/synthesize.target_files` | `list[dict]` |
| `codegen/synthesize.dependencies` | `list[str]` |
| `codegen/synthesize.test_coverage` | `dict` |
| `codegen/synthesize.patterns_to_follow` | `list[str]` |

If FR-1121 lands first, FR-1123 verifies the already-typed digest field and does not rewrite it. No documented exception may leave an empty subschema in the committed census.

### R-5: Make graph-authoring evidence match the adapter contract

For each affected example directory actually modified by FR-1123, add and cite one committed brief under `feature-requests/authoring-briefs/`, then run `scripts/author.sh` once for that directory. The generated `tmp/draft-authoring-report.md` must be verified before the next run and summarized in the FR implementation record; it is reviewed and then discarded or overwritten, not committed. Require the report's `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation` sections, plus lint and the narrowest honest smoke for the affected graph.

Replace AC-6's ambiguous “committed brief and adapter report each” with that contract. A directory not modified because another enforced FR already supplied the exact migration needs no new authoring run, but its final schema remains part of the census.

### R-6: Fold the revised scope and criteria into the FR

Replace the current acceptance list with the criteria below, add the exact deliverables and exclusions, update Status to judged with revisions, and state that implementation authority begins only after R-1 through R-6 are folded. Reuse `REQ-YG-664` only if its capability text is extended to cover refusal of unconstrainable Anthropic schemas; otherwise reserve a new REQ through the repository route before writing tests.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/structured_output.py` or, if needed for the size limit, `yamlgraph/utils/schema_walk.py`: typed error and one JSON-schema walker |
| D-2 | `yamlgraph/utils/llm_factory.py`, `yamlgraph/node_factory/llm_nodes.py`, and the existing structured-output binder: shared static-provider resolution, compile refusal, and actual-model runtime refusal |
| D-3 | `yamlgraph/linter/checks_prompts.py` and `yamlgraph/linter/graph_linter.py`: `E016` for static Anthropic and `W028` for unresolved provider |
| D-4 | `tests/unit/test_fr1123_untyped_subschema.py` plus narrow linter/CLI fixtures and one slow private-SDK parity module |
| D-5 | The twelve fields in the nine prompt files listed in R-4, modified only through the graph-authoring route when FR-1123 owns the edit |
| D-6 | Committed authoring briefs for directories modified by FR-1123 and verified temporary authoring reports summarized in the implementation record |
| D-7 | The canonical linter/graph reference, capability/REQ record, generated architecture record when required, and changelog fragment |
| D-8 | FR implementation record and Distill diary entry with `**Seed:**` |

Not authorized: rejecting `Any` in the provider-neutral schema loader; warning on a known non-Anthropic provider; changing non-Anthropic binding; changing explicit `function_calling`; adding a fallback, downgrade, retry, or second attempt; changing FR-998's unsupported-model policy; implementing nested `fields:` grammar; changing OpenAI strict-mode behavior; changing node error defaults; repairing unrelated prompts or graphs; editing CI, hooks, judge/review doctrine, or graph-authoring doctrine; or implementing any Anthropic schema rule other than the missing-keyword class frozen here.

## Revised acceptance criteria

- [ ] AC-01 (RED): before production implementation, the five frozen type fixtures prove exact walker results: `Any` and `list[Any]` expose their precise paths; `dict`, `list[dict]`, and `list[str]` expose none. The RED commit precedes GREEN.
- [ ] AC-02: nested fixtures cover `properties`, `items`, `prefixItems`, `anyOf`, `oneOf`, `allOf`, `$defs`, dict-valued `additionalProperties`, and accepted `$ref`; assertions compare exact, deterministically ordered JSON paths.
- [ ] AC-03: `bind_structured_output` raises `UnconstrainableSchemaError` before `with_structured_output` for an actual Anthropic model using effective `json_schema`; the error names model and every path. Spies prove no walker call for a non-Anthropic model or explicit `function_calling`.
- [ ] AC-04: provider-resolution tests cover node override, graph default, `PROVIDER`, built-in Anthropic default, explicit known non-Anthropic, and state-derived unresolved provider; `create_llm` and compile/lint classification use the same pure resolver.
- [ ] AC-05: compiling a static-Anthropic fixture fails before any node executes and names node, prompt, model, and path. A state-derived-provider fixture compiles, then the binder refuses before `with_structured_output` when the runtime model is Anthropic.
- [ ] AC-06: lint emits `E016` per offending path for static Anthropic, `W028` per offending path for unresolved provider, and no issue for explicit Mistral or another known non-Anthropic provider; both checks are wired through `lint_graph`, serialized through the existing issue shape, and documented.
- [ ] AC-07: the private-SDK test imports `transform_schema` in exactly one test module and proves parity only for the cited missing-keyword rejection over the frozen fixtures and every committed prompt schema under `examples/`, `graphs/`, and `.github/`; production contains no private SDK import.
- [ ] AC-08: the committed prompt census contains none of the forbidden untyped paths, and all twelve fields have exactly the R-4 types and matching descriptions. If FR-1121 supplied the digest migration first, the census records that ownership without rewriting it.
- [ ] AC-09: every example directory modified by FR-1123 has a cited committed authoring brief and a separately verified `tmp/draft-authoring-report.md`; the implementation record lists each adapter command, authored paths, lint result, smoke result or exact blocked reason, and repairs. Temporary reports are not committed.
- [ ] AC-10: `graph run` on the static-Anthropic fixture exits nonzero with the compile error on stderr and a witness proves no graph node executed.
- [ ] AC-11: `structured_output.py` remains below 400 lines or the walker is split into `schema_walk.py`; `lint-imports` passes and no production `.with_structured_output(` call is added outside the FR-998 policy module.
- [ ] AC-12: tests carry the approved REQ marker; the capability/architecture record, canonical documentation, changelog fragment, FR implementation record, and Distill entry exist; targeted tests, `python scripts/req_coverage.py --strict`, and the full unit suite pass without weakened assertions.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into FR-1123 before any production implementation; this draft alone grants no authority. | GATE |
| C-2 | FR-1086 retains exclusive authority over `E015`; FR-1123 uses `E016` and `W028` and records that prior-art disposition. | GATE |
| C-3 | Runtime refusal must require both an actual Anthropic model and effective `json_schema`; all non-Anthropic and explicit `function_calling` paths remain byte-for-byte policy-equivalent. | GATE |
| C-4 | Static compile refusal may classify only providers resolved by the shared pure resolver; state-derived provider selection is deferred to the actual-model binder, never guessed. | GATE |
| C-5 | SDK parity is limited to the cited missing-keyword error class; no unrelated Anthropic schema rule may enter production under FR-1123. | GATE |
| C-6 | Every graph or prompt edit follows the graph-authoring adapter route with a committed cited brief and verified temporary report; direct edits and committed reports are forbidden. | GATE |
| C-7 | No migration may preserve an empty subschema or silently widen/narrow a field differently from the exact R-4 table. | GATE |

Authority granted: after R-1 through R-6 are folded, implement the single untyped-subschema walker, Anthropic-only compile/runtime refusals, `E016`/`W028` lint feedback, exact twelve-field migration, witnesses, documentation, and records listed in D-1 through D-8.
