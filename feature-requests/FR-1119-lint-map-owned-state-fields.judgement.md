# Judgement: FR-1119 Lint knows the state fields a map node creates

**Verdict:** APPROVED WITH REVISIONS — the E007 defect is real and the fix is small, but authority activates only after the FR repairs its research record and makes its proposed map-field set agree with the state builder and parity criterion.

**Reviewed against:** `feature-requests/FR-1119-lint-map-owned-state-fields.md`; cited evidence `yamlgraph/linter/checks_semantic.py`, `yamlgraph/models/state_builder.py`, `yamlgraph/compile/map_compiler.py`, `feature-requests/FR-1073-map-result-contract.md`, `feature-requests/FR-1116-map-memo-file-corpus.md`, `feature-requests/FR-1120-census-map-memo.md`, `examples/demos/meta_map/graph.yaml`, `tests/unit/test_fr1073_map_result_contract.py`, `tests/unit/test_fr1113_meta_map.py`, `tests/unit/test_linter_fr025.py`, `reference/graph-yaml.md`, and `ARCHITECTURE.md`; repo doctrine `.github/copilot-instructions.md`, `CLAUDE.md`, `.github/skills/judge-fr/doctrine.md`, and `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect has direct committed witnesses: FR-1116 records the false E007 and workaround (`feature-requests/FR-1116-map-memo-file-corpus.md:284-288`), that workaround is present (`examples/demos/meta_map/graph.yaml:31`), and FR-1120 depends on both the default failures field and `_map_verdict` (`feature-requests/FR-1120-census-map-memo.md:130-135,180`). The linter currently adds only `collect` (`yamlgraph/linter/checks_semantic.py:115-130`), while the builder adds the derived failures field and shared map channels (`yamlgraph/models/state_builder.py:262-271`). The negative no-map criterion is a good guard against globally blessing underscore-prefixed names.

The work is a framework primitive: E007 is a shared semantic guarantee, and the concrete uses cover a verdict consumer plus default and explicit failures contracts. The change is feasible in the existing semantic check, directly testable under REQ-YG-069 (`ARCHITECTURE.md:796`), and remains one responsibility; removing the demonstrated `meta_map` workaround is a migration witness, not an independent feature.

## Required revisions

### R-1: Supply a substantive equivalent research record

Replace the three-row Alternatives table and unsupported boundary claim with 4-6 genuine solution classes, precedent lines, preserved disagreement, and an explicit `is_this_a_graph` answer, as required by `.github/skills/judge-fr/doctrine.md:118-129`. At minimum disposition: manual `state:` declarations; local map-only derivation in the linter; reuse of `extract_node_fields`; a shared map-field helper; and global underscore suppression. Correct the claim at `feature-requests/FR-1119-lint-map-owned-state-fields.md:90`: `checks_semantic.py` already imports `COMMON_INPUT_FIELDS` from `state_builder` (`yamlgraph/linter/checks_semantic.py:9`), and `extract_node_fields` accepts a node dictionary without building a full graph configuration (`yamlgraph/models/state_builder.py:219-220,237-278`). Select the local map-only derivation if preserving the present narrow scope; explain that wholesale helper reuse would also alter E007 knowledge for unrelated node types.

### R-2: Make the map-owned field contract internally consistent

Correct the statement that the builder creates three map fields (`feature-requests/FR-1119-lint-map-owned-state-fields.md:24-26`). For a valid map it creates five: `collect`, the configured/default failures field, `_map_accounting`, `_map_open`, and `_map_verdict` (`yamlgraph/models/state_builder.py:262-271`; existing witness `tests/unit/test_fr1073_map_result_contract.py:468-490`). Amend the Proposed Solution so a `type: map` contributes all five to known fields: add the three shared channels whenever a map node exists, and derive the failures field only when a non-empty `collect` is available, so linting malformed input does not raise an unbound-name exception. Keep the change local to map nodes.

### R-3: Define parity against the actual builder

Retain AC-04's full parity promise, but specify that the test calls both `_build_known_state_fields` and `extract_node_fields` on the same two-map fixture and asserts that every builder-derived key is known to E007. Include one default and one explicit failures key. Add no-map negative controls for `_map_accounting`, `_map_open`, and `_map_verdict`; otherwise adding the shared names unconditionally would satisfy the positive tests while weakening E007. This resolves the contradiction between the two-field Proposed Solution (`feature-requests/FR-1119-lint-map-owned-state-fields.md:65-70`) and the every-field criterion (`feature-requests/FR-1119-lint-map-owned-state-fields.md:81`).

### R-4: Freeze requirement traceability

Replace the AC-06 choice between an existing requirement and a new capability (`feature-requests/FR-1119-lint-map-owned-state-fields.md:83`) with REQ-YG-069. Update that requirement's known-field list in `ARCHITECTURE.md`, and mark every new test with `@pytest.mark.req("REQ-YG-069")`. This extends the existing E007 contract; it does not create a new capability.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Fold R-1 through R-4 into `feature-requests/FR-1119-lint-map-owned-state-fields.md` |
| D-2 | Add map-only known-field derivation in `yamlgraph/linter/checks_semantic.py` |
| D-3 | Add focused E007 positive, negative, and builder-parity tests under `tests/unit/` |
| D-4 | Update REQ-YG-069 in `ARCHITECTURE.md` |
| D-5 | Remove only the `_map_verdict` workaround from `examples/demos/meta_map/graph.yaml` through a committed authoring brief and `scripts/author.sh` |
| D-6 | Add the changelog fragment, FR implementation record, and Distill diary entry |

Not authorized: changing state-builder or map-compiler behavior; changing map reducers, dispatch, accounting, completeness, or schema validation; changing E007's expression scan surface; adding node-field behavior for non-map node types; editing any graph other than `examples/demos/meta_map/graph.yaml`; introducing a new capability/REQ; or broad linter/compiler refactoring.

## Revised acceptance criteria

- [ ] AC-01: A graph with a map node that reads `{state._map_verdict.<map>.dispatch}` without declaring `_map_verdict` produces no E007.
- [ ] AC-02: Separate fixtures reading the default `<collect>_failures` field and an explicit `failures:` field without declaring them produce no E007.
- [ ] AC-03: A map graph may reference `_map_accounting` and `_map_open` without E007 because both are fields created by the state builder.
- [ ] AC-04: A graph with no map node that references `_map_accounting`, `_map_open`, or `_map_verdict` receives E007 for each referenced field.
- [ ] AC-05: For a fixture with two map nodes, one using default failures and one explicit failures, every key returned by `extract_node_fields` for those nodes is present in `_build_known_state_fields`.
- [ ] AC-06: The map-only derivation handles a malformed map lacking `collect` without raising from `_build_known_state_fields`; existing schema diagnostics remain responsible for reporting the malformed node.
- [ ] AC-07: `examples/demos/meta_map/graph.yaml` no longer declares `_map_verdict`; the change is produced through `scripts/author.sh`, `yamlgraph graph lint examples/demos/meta_map/graph.yaml` reports no E007, and `tests/unit/test_fr1113_meta_map.py` passes.
- [ ] AC-08: All new tests carry `@pytest.mark.req("REQ-YG-069")`; REQ-YG-069 names map `collect`, failures, accounting, open, and verdict fields; and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-09: The changelog fragment, folded FR implementation record, and Distill diary entry with a `Seed:` are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not begin implementation until R-1 through R-4 are folded into the FR and this revised scope is the plan of record. | GATE |
| C-2 | Add shared map channels only when at least one `type: map` node exists; no global underscore-name allowlist is permitted. | GATE |
| C-3 | Keep production changes within `yamlgraph/linter/checks_semantic.py`; builder and compiler files are evidence and test oracles, not implementation surfaces. | GATE |
| C-4 | Route the sole graph edit through `scripts/author.sh` and retain its authoring report as the validation witness. | GATE |
| C-5 | A human reviewer must verify the E007 negative controls before merge because this changes an enforcement surface. | GATE |

Authority granted: after the required revisions are folded, implement the map-only E007 field parity, its focused witnesses, the single `meta_map` workaround removal, and the listed traceability artifacts—nothing adjacent.
