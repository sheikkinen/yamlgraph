# Judgement: FR-1059 Attribute-tailed fields never render in simple-format prompts

**Prior art:** [FR-1059-attribute-fields-in-simple-format.md](FR-1059-attribute-fields-in-simple-format.md)
— the FR this judgement governs, not a competing proposal. Its own
`**Prior art:**` line dispositions the substantive precedent (FR-1057, FR-631,
FR-252, FR-110, FR-319, FR-645, FR-430, FR-214).

**Verdict:** APPROVED WITH REVISIONS — the mapping-aware renderer is a small, testable correction at the prompt boundary, but authority activates only after the absent FR-1057 parent is committed and the collision, list-rendering, ID-allocation, and corpus-witness ambiguities below are folded into the FR.

**Reviewed against:** `feature-requests/FR-1059-attribute-fields-in-simple-format.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; cited prior art `feature-requests/FR-631-variable-string-interpolation.md`, `feature-requests/FR-252-python-node-variables.md`, `feature-requests/FR-110-lint-state-variable-expressions.md`, `feature-requests/FR-319-lint-unanchored-prompt-variables.md`, `feature-requests/FR-645-lint-map-subnode-prompt-variables.md`, `feature-requests/FR-430-linter-mixed-template-syntax.md`, and `feature-requests/FR-214-fix-extract-variables-nested-set.md`; cited implementation evidence `yamlgraph/utils/template.py`, `yamlgraph/executor_base.py`, `yamlgraph/utils/expressions.py`, `yamlgraph/node_factory/llm_nodes.py`, `examples/codegen/impl-agent.yaml`, `examples/codegen/prompts/plan_discovery.yaml`, `reference/prompt-yaml.md`, and `ARCHITECTURE.md`. The cited `feature-requests/FR-1057-prompt-template-dialect-split.md` was not present in committed tree `d6faf6b5815c393f1da0fc0959708f477ca08825` and therefore could not be consumed as evidence.

## What is sound

- **Scope and single responsibility:** the FR confines production behavior to simple-format field traversal and explicitly excludes new lint behavior (`FR-1059`, lines 189-241). The selected change addresses one boundary defect rather than changing the deliberate Pydantic-to-dict state shape at `yamlgraph/node_factory/llm_nodes.py:289-293`.
- **Consistency and architecture alignment:** the intended mapping-first, object-second traversal matches the established graph-layer path rule in `yamlgraph/utils/expressions.py:28-50` and `yamlgraph/utils/expressions.py:89-96`. The live graph passes `parsed_request` from one LLM node to another (`examples/codegen/impl-agent.yaml:175-190`), while the prompt dereferences three tails (`examples/codegen/prompts/plan_discovery.yaml:70-72`).
- **Feasibility:** `format_prompt` has a narrow simple-dialect branch ending in `template.format(**safe_vars)` (`yamlgraph/executor_base.py:90-132`), so a `string.Formatter` specialization is a workable local change. The FR's probes cover mapping, object, and missing-key behavior (`FR-1059`, lines 189-237).
- **Measurability and testability:** AC-1 through AC-8 define direct assertions for mapping, object, nested, mixed, failure, extraction, and live-message behavior (`FR-1059`, lines 249-256). These can condemn the defect rather than merely checking a final command exit.
- **Strategic classification:** **Contrib/example-scale correction to an existing framework abstraction.** After the declared FR-1057 retirement, one surviving workflow contains three live sites (`FR-1059`, lines 172-174). That does not establish a new framework primitive, but fixing the existing renderer is still proportionate because the same public formatting boundary serves every prompt and the alternative three-site rewrite leaves the demonstrated cross-layer semantic trap intact (`FR-1059`, lines 272-278).
- **Research substance:** the in-body research presents seven genuine alternatives, executable observations, dispositions, precedent, and an explicit `is_this_a_graph` answer (`FR-1059`, lines 265-286), satisfying the prospective research-content gate.

## Required revisions

### R-1: Establish the committed parent before authority

Commit or merge FR-1057, then rebase FR-1059 onto that commit. Replace every `Enforced-unpushed`, “after FR-1057 merges,” provisional line reference, and unavailable relative link with the committed parent SHA and current paths. Re-run and update the failure probe, census, formatter/extractor evidence, and lint baseline on that rebased tree. This is mandatory because the current FR expressly depends on `scan_simple_fields`, `bare_roots`, E013/E014, and a documentation section that do not exist in the reviewed committed tree (`FR-1059`, lines 16-22, 151-177, 230-241, 255, and 261).

### R-2: Specify mapping-key precedence and correct the preservation claim

State that, while traversing a `Mapping`, a dotted component is always a key lookup even when its name collides with a mapping attribute such as `items`, `keys`, or `values`; `getattr` is used only when the current value is not a `Mapping`. Delete the claim that every currently rendering template remains identical (`FR-1059`, line 235): `{a.items}` with a dict currently resolves the object attribute, while the proposed algorithm resolves key `"items"` or raises `KeyError`. Add an acceptance test for both a present colliding key and an absent colliding key.

### R-3: Preserve simple-format list presentation through paths

Define a terminal list reached through a dotted or indexed path to use the renderer's existing comma-joined list presentation, not Python list representation. The current boundary deliberately normalizes top-level lists before formatting (`yamlgraph/executor_base.py:128-132`), while two of the three live fields are lists (`examples/codegen/prompts/plan_discovery.yaml:71-72`) and the proposal's probe currently emits `"['a']"` (`FR-1059`, lines 219-224). Add exact assertions for scalar, non-empty-list, and empty-list text in the live witness so “contains `feat`” cannot pass while the other two fields render incorrectly.

### R-4: Allocate final traceability IDs before enforcement

After rebasing onto the committed parent, scan `capabilities/`, allocate the then-free capability and requirement IDs, and replace every provisional `CAP-275` / `REQ-YG-686` occurrence in the FR before RED implementation begins. AC-12 cannot simultaneously prescribe those IDs while the acceptance preamble says they are provisional (`FR-1059`, lines 245-247 and 260-262).

### R-5: Make the corpus checks executable

Paste the exact deterministic commands used for the graph-shaped-YAML lint baseline and the attribute-tail census into the FR, including how graph-shaped files are selected, where baseline/post-change logs are written, and the asserted exit/count comparison. AC-9 and AC-10 currently name outcomes but not reproducible commands, and “each renders” is not established by the field-name census alone (`FR-1059`, lines 257-258). Keep rendering correctness in the exact `prepare_messages` witness from R-3; use the census only to assert the residual site set.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Mapping-aware simple-format field traversal in `yamlgraph/utils/template.py` and/or the simple branch of `yamlgraph/executor_base.py::format_prompt` |
| D-2 | RED/GREEN unit coverage for mapping, object, nested, mixed index/attribute, collision, missing-key, extraction-root, and list-presentation behavior |
| D-3 | Live `prepare_messages("examples/codegen/plan_discovery", ...)` regression witness using the committed example prompt |
| D-4 | One newly allocated capability file and generated `ARCHITECTURE.md` requirement content |
| D-5 | One paragraph in `reference/prompt-yaml.md` documenting mapping-key precedence, object fallback, missing-key behavior, and terminal list presentation |
| D-6 | Exact corpus lint/census commands and their baseline/post-change logs cited from the FR Implementation Record |
| D-7 | FR implementation record, fix changelog fragment, and Distill diary entry |

Not authorized: changes to graph-layer expression resolution; Pydantic/state normalization; checkpointers; Jinja rendering semantics; prompt or graph linter codes; rewrites of the three `plan_discovery` placeholders; retirement of the simple dialect; unrelated prompt migrations; CI, hook, judge, or review infrastructure.

## Revised acceptance criteria

- [ ] **AC-01:** On the committed rebased parent, a separately committed RED test proves `format_prompt("{a.b}", {"a": {"b": "v"}})` raises `AttributeError`; the GREEN implementation returns `"v"`.
- [ ] **AC-02:** Dotted traversal uses mapping keys for every `Mapping` and `getattr` only for non-mapping objects.
- [ ] **AC-03:** A mapping key whose name is `items` resolves that key; an absent `items` key raises `KeyError` rather than exposing `dict.items`.
- [ ] **AC-04:** Plain-object attribute traversal remains functional.
- [ ] **AC-05:** `{a.b.c}` traverses two mappings, and `{a.b[0].c}` traverses mixed mapping/index components.
- [ ] **AC-06:** A missing mapping tail raises `KeyError`; no silent value and no `on_error` change is introduced.
- [ ] **AC-07:** Terminal lists reached through paths retain comma-joined simple-format presentation; tests assert non-empty and empty lists exactly.
- [ ] **AC-08:** On the rebased FR-1057 parent, `extract_variables("{a.b}") == {"a"}`.
- [ ] **AC-09:** The exact live `prepare_messages("examples/codegen/plan_discovery", ...)` probe asserts all three rendered lines: scalar `change_type`, comma-joined `key_terms`, and comma-joined `file_patterns`; its transcript is recorded in the FR.
- [ ] **AC-10:** The FR contains and executes an exact tracked-graph lint command; the post-change run has zero crashes and no findings absent from the recorded rebased-parent baseline, with both log paths cited.
- [ ] **AC-11:** The FR contains and executes an exact census command using the FR-1057 parser; it reports the same three surviving sites in `plan_discovery.yaml`. Rendering is proven by AC-09, not inferred from this count.
- [ ] **AC-12:** The full unit suite, `ruff check yamlgraph/`, and `python scripts/req_coverage.py --strict` exit zero.
- [ ] **AC-13:** A final free capability/requirement pair is allocated after rebase; the capability file is added and `ARCHITECTURE.md` is regenerated with `python scripts/aggregate_capabilities.py`.
- [ ] **AC-14:** `reference/prompt-yaml.md` documents mapping-key precedence, object fallback, missing-key failure, and path-terminal list presentation for the simple dialect, while preserving the per-message dialect contract from FR-1057.
- [ ] **AC-15:** `changelog/unreleased/fr-1059-attribute-fields-in-simple-format.md` records a `fix` in `prompts` using the final requirement ID.
- [ ] **AC-16:** The FR Implementation Record identifies the parent SHA, RED SHA, GREEN SHA, final IDs, commands, logs, results, and any deviation.
- [ ] **AC-17:** A Distill entry in `docs/diary/` names the trap, extracts a heuristic, and includes a **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-1057 and its cited parser, lint, extraction, and documentation contracts exist in the committed parent; no implementation starts from the reviewed `d6faf6b5` tree. | GATE |
| C-2 | R-1 through R-5 are folded into the committed FR, including final capability/requirement IDs and exact corpus commands. | GATE |
| C-3 | RED is committed separately and fails for the missing mapping traversal rather than an import, fixture, or absent-parent error. | GATE |
| C-4 | Mapping lookup remains fail-loud and takes precedence over mapping object attributes; object fallback is retained only for non-mappings. | GATE |
| C-5 | Existing simple-format list presentation is preserved for values reached through paths and proven by exact live-output assertions. | GATE |
| C-6 | No linter, graph-expression, state-normalization, checkpointer, Jinja, example-placeholder, or enforcement-infrastructure change enters this FR. | GATE |

Authority granted: after C-1 and C-2 are satisfied, implement only the frozen mapping-aware simple-format traversal and its directly required tests, documentation, traceability, changelog, implementation record, corpus witnesses, and Distill artifact.
