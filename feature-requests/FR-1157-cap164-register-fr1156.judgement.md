# Judgement: FR-1157 Register FR-1156 in CAP-164 and State the Literal Rule in REQ-YG-712

**Round:** [FR-1157](FR-1157-cap164-register-fr1156.md) round 1 (2026-11-13, copilot backend via scripts/judge.sh); R-1 and R-2 folded into the FR.

**Prior art:** [FR-1156](FR-1156-anthropic-sdk-2-8-floor.md) is the parent whose round-3 amendment this FR re-files as a separate small authority; FR-1157 itself is the judged FR.

**Verdict:** APPROVED WITH REVISIONS - the registry repair is justified and minimal, but the requirement must also exclude literal-masked open objects and the container check needs a reproducible command; authority activates only after promotion and both revisions are folded into the committed FR.

**Reviewed against:** Committed inputs at `c9ed8396a00de6536d919bc1d4feb05ad68b9ff7`: `feature-requests/FR-1157-cap164-register-fr1156.md` (entire file); `capabilities/CAP-164-structured-output-fallback.yaml` (entire file, also its `fr:` at cited GREEN `f69b58c6`); `tests/unit/test_changelog_req_cross_wiring.py` (entire file); `changelog/unreleased/fr-1156-anthropic-sdk-2-8-floor.md` (entire file); `feature-requests/FR-1156-anthropic-sdk-2-8-floor.md` (entire file); `feature-requests/FR-1156-anthropic-sdk-2-8-floor.judgement.md` (round-1 findings and round 2, lines 120-204); `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md` (entire file); `feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md` (lines 1-105 and capability/implementation matches); `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md` (lines 1-85 and supplied repository doctrine). Consumed working-tree evidence files had no differences from HEAD. Container results and SDK behavior are assessed as committed evidence claims, not independently reproduced observations. No author's chat, temporary witness script, uncommitted adapter changes, or installed SDK source was consumed.

## What is sound

The failure has a concrete cause: the fragment claims REQ-YG-712, CAP-164 owns that requirement but omits FR-1156, and the existing test rejects exactly that missing mapping (`fr-1156-anthropic-sdk-2-8-floor.md:1-6`; `CAP-164:3,55`; `test_changelog_req_cross_wiring.py:24-38,102-145`). Adding the owner association repairs data rather than weakening enforcement. Keeping the same requirement and fragment avoids invented capability machinery.

The strongest case against the proposed two edits is that a green cross-wiring test does not prove the registry describes the literal rule correctly. FR-1156 explicitly accepts `{"type": "object", "enum": ["a"]}` without hollowing, yet the unchanged open-object clause would still describe that form as refused (`FR-1156:135,144-150`; `CAP-164:60-62`). R-1 closes this directly coupled omission in the same text field.

| Criterion | Finding and evidence |
|---|---|
| Scope | One capability association and its existing requirement text are the smallest sufficient repair. Correcting the literal exception for both finding kinds stays within that surface (`FR-1157:68-78`; `CAP-164:55-74`). |
| Consistency | The untyped replacement is sound, but retaining the unconditional open-object definition contradicts the parent traversal contract and the stated ideal of describing the implemented rule (`FR-1157:43-46,73-76`; `FR-1156:144-150`). |
| Measurability | Exact field changes and targeted checks are mechanical. The container command contains an unresolved script placeholder; the cited parent appendix supplies only different 3.12 witnesses (`FR-1157:61-63,82-86`; `FR-1156:358-411`). R-2 makes AC-04 executable. |
| Feasibility | The mapping parser already accepts comma-separated FRs, and no new dependency or runtime logic is needed. The parent records a non-root Linux/3.11 CI mirror, but its reproduction recipe is incomplete (`test_changelog_req_cross_wiring.py:35-38`; `FR-1156:288-321`). |
| Architecture alignment | CAP-164 is the declared source of ownership and requirement truth; the repair follows its existing multi-FR pattern instead of changing the gate (`CAP-164:3,55-74`; `FR-1125:262,292,382`). |
| Single responsibility | Ownership and specification accuracy are tightly coupled maintenance of one existing capability, not independent features. No SPLIT is warranted (`FR-1157:26-31,68-78`). |
| Strategic classification | **Pattern documentation / registry maintenance**, not a new framework primitive: existing abstractions suffice and no new capability or REQ is needed (`FR-1157:77,90-97`). |
| Testability | The committed collision witness fails for missing registry data, not missing fixtures/imports. Exact text and diff assertions can verify the documentation repair without adding production or test code (`test_changelog_req_cross_wiring.py:102-145`; `FR-1157:82-86`). |

The committed in-body research reference is substantive for this bounded data repair: four distinct choices retain or remove attribution, weaken enforcement, or repair ownership with or without accurate documentation; each is dispositioned and `is_this_a_graph` is answered (`FR-1157:14,88-97`). The cited FR-1123/FR-1125 precedents are used rather than recreated. FR-1156's rejected first round and its round cap do not disappear: this new FR requests only the omitted registry surface, not renewed authority over the parent's migration (`FR-1157:16-22`; `FR-1156:282-310`; parent judgement, round 2 D-1..D-7 and C-4). This is not measurement tooling.

## Required revisions

### R-1: State the literal exception for open objects too

Retain the proposed untyped replacement. In the same REQ-YG-712 `text`, additionally replace `object (type object with no declared properties, which the transform` with `object (type object with no declared properties and carrying no primitive const or non-empty all-primitive enum, which the transform`.

Fold this exact additional replacement into Proposed Solution item 2 and AC-02. Replace the blanket "no other text change" with "only these two clause replacements in REQ-YG-712 text; all other text remains unchanged." No new finding kind or behavior is authorized.

### R-2: Replace the missing CI-mirror script with an inline reproducible recipe

Replace `<FR-1156 CI-mirror script>` in Planned Operations with an inline container recipe committed in this FR. It must identify the candidate commit, copy that committed tree into a writable container workspace, install `git` and `curl`, install the exact CI-3.11 extras unpinned, and execute as a non-root user:

`python -m pytest tests/unit -q --no-cov -m "not slow" -n auto`

State the exact extras, setup commands and invocation; do not point at an unspecified temporary script. Record Python/platform, resolved dependency versions, candidate SHA, command, exit status and pytest totals in the implementation status. Preserve AC-04's separate green Linux CI requirement. This is a documentation recipe, not authority to change CI or create new test infrastructure.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `capabilities/CAP-164-structured-output-fallback.yaml`: append only FR-1156 to `fr:` and make only the two R-1 clause replacements in REQ-YG-712 `text` |
| D-2 | `feature-requests/FR-1157-cap164-register-fr1156.md`: revision folds, inline validation recipe and implementation/validation record |
| D-3 | Promoted judgement alongside FR-1157; scoped Distill record with a **Seed:**, which may be folded into the parent PR's existing diary entry |

Not authorized: other capability fields, FR-1157 registration, new REQ IDs, new tests, a separate changelog fragment, runtime/schema-walker edits, dependency changes, graph/prompt edits, CI/hook/doctrine changes, or reopening FR-1156's frozen implementation scope. FR-1156's existing fragment remains unchanged.

## Revised acceptance criteria

- [ ] AC-01: CAP-164 `fr:` is exactly `FR-464, FR-998, FR-1121, FR-1123, FR-1125, FR-1156`; its prior entries and order are unchanged.
- [ ] AC-02: REQ-YG-712 `text` contains exactly the proposed untyped replacement and R-1 open-object replacement; a baseline-relative diff proves no other capability field or requirement text changed.
- [ ] AC-03: `python -m pytest tests/unit/test_changelog_req_cross_wiring.py -q --no-cov` and `python scripts/req_coverage.py --strict` exit zero without test or gate modifications.
- [ ] AC-04: The committed R-2 recipe executes the unchanged fast-unit command on the committed candidate in the non-root Linux/3.11 CI mirror and exits zero; the implementation record contains its identity, environment, command and totals. The corresponding Linux CI test checks for that candidate also pass.
- [ ] AC-05: FR-1157 records implementation status, revision folds and validation outcomes. The repair lands in the FR-1156 PR using its existing REQ-YG-712 fragment, without a separate fragment; the scoped Distill record contains a **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Promote this draft and fold R-1/R-2 into the committed FR before implementation. | GATE |
| C-2 | Treat this as separate authority for the omitted registry surface only; all FR-1156 acceptance and release conditions remain in force. | GATE |
| C-3 | Preserve the existing condemning witness and fragment attribution. Do not modify assertions, add skips/deselections, or substitute a baseline comparison for passing checks. | GATE |
| C-4 | Any further red result blocks completion: record it and obtain separately judged authority for repairs outside D-1..D-3. | GATE |
| C-5 | Keep CI, hooks and doctrine untouched. Any infrastructure proposal requires a separate FR and explicit human review; this verdict grants no merge or release decision. | GATE |

Authority granted: none by this draft alone; after promotion and both revision folds, only the scoped registry/documentation repair and its records may be implemented in the FR-1156 PR.
