# Judgement: FR-1156 Raise the Anthropic SDK Floor to 2.8.0 and Re-Align the Untyped-Schema Walker

**Prior art:** FR-1123 (untyped walker + SDK parity oracle), FR-1125 (open-object rule + content parity), FR-1154 (SDK-2 factory; its judgement excluded dependency upgrades), FR-761 (constraints artifact). No cited prior FR is Rejected.

## Round 1 (2026-11-13, copilot backend via scripts/judge.sh) — REJECTED, R-1..R-4 folded into the FR

**Verdict:** REJECTED — return to plan: the research record substitutes message-matching variants for a substantive alternative, and literal traversal, dependency closure, and regression gates are not sufficiently specified; no implementation authority is granted.

**Reviewed against:** Committed inputs at `95f2e5770bbdfe5f36ee2acb4c62b7c1a47a05c7`: `feature-requests/FR-1156-anthropic-sdk-2-8-floor.md`; `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md`; `feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md` (lines 1-230); `feature-requests/FR-1154-anthropic-api-version-sampling-removed.md`; `feature-requests/FR-1154-anthropic-api-version-sampling-removed.judgement.md`; `feature-requests/FR-761-reproducible-dependency-governance.md`; `yamlgraph/utils/schema_walk.py`; `tests/unit/test_fr1123_sdk_parity.py`; `pyproject.toml` (lines 1-200); `constraints/dev-py312.txt`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md` (lines 1-105 and supplied repository doctrine). These paths had no differences from HEAD. SDK behavior, wheel metadata, and CI results are assessed as the FR's committed probe claims, not independently reproduced observations. No author's transcript, temporary resolver report, or installed private SDK source was consumed.

## What is sound

The reported incident is concrete, and its causal explanation agrees with the cited test: both rejection oracles compare `ValueError` text exactly (`FR-1156:8-14,36-49,64-70`; `test_fr1123_sdk_parity.py:23-33,142-150`). Updating only that string would leave the mixed-type `Literal` false refusal described in Probe 2. Realigning the shared pure walker, rather than importing private SDK code into production, addresses the provider boundary once (`FR-1156:73-91,157-172`).

The strongest case against accepting the plan is not that the incident is unreal. It is that a successful root-literal test and a Windows/Python-3.13 resolver dry run can conceal an incorrect traversal rule and an unverified Python-3.12 constraints artifact. Neither proves the promised agreement across lint, compile, and SDK transformation.

| Criterion | Finding and evidence |
|---|---|
| Scope | The two dependency floors and shared predicate are a coherent small correction; the path normalization is directly coupled to the edited parity witness. However, "whatever minimal cascade" does not freeze a dependency surface (`FR-1156:150-169`). |
| Consistency | Probe 2 says literals suppress type-driven descent while compositions remain traversed, but the solution introduces eligibility only in the untyped branch, and its criteria never distinguish unconditional early return from correct traversal (`FR-1156:88-91,157-162,178-180`). |
| Measurability | Most criteria name exact values or commands. AC-02 accepts resolution alone despite the claimed unpinned Windows dependency; AC-07 accepts baseline-relative failures instead of a passing required suite (`FR-1156:100-109,177,182`). |
| Feasibility | The recorded resolver succeeds on Python 3.13, but the edited artifact targets Python 3.12. The lowest wrapper floor, 1.7.7, is inferred from metadata rather than exercised with 2.8.0 (`FR-1156:15-17,96-118,192-193`; `constraints/dev-py312.txt:8-17`). |
| Architecture alignment | Reuse of `schema_walk.py`, its typed findings, and the single private-SDK test module is appropriate. The content oracle also needs literal-aware traversal if those cases enter its shared fixtures (`schema_walk.py:77-107`; `test_fr1123_sdk_parity.py:111-131`; `FR-1156:163-172`). |
| Single responsibility | One provider-schema migration, including its dependency universe and witnesses; no SPLIT is necessary. Factory-branch retirement and full constraints regeneration remain separate (`FR-1156:186-193`). |
| Strategic classification | **Framework primitive correction**, not a new primitive: existing lint, compile, and bind consumers share this schema rule, so example or pattern documentation cannot fix it (`FR-1125:123-178`; `FR-1156:52-57,157-172`). The proposal needs no new abstraction or capability. |
| Testability | Root acceptance/rejection cases are directly derivable. Tests for the new descent rule and actual lint/compile behavior are missing from the frozen witness matrix (`FR-1156:160-167,178-181`). |

FR-1123 and FR-1125 are appropriately distinguished as the original rejection and content-preservation rules (`FR-1156:18-28`). FR-761 is the reproducibility precedent, not merely ownership of a filename (`constraints/dev-py312.txt:3-17`; `FR-761`, AC-01/AC-02 and implementation record). FR-1154's judgement explicitly excluded dependency upgrades from its authority (`FR-1154.judgement.md`, Not authorized and C-6); a separately judged FR can authorize this migration, but its exclusion must not be rewritten as a claim that the older judgement already permits it. No cited prior FR is itself Rejected; the rejected alternative dispositions still need accurate treatment (`FR-1156:202-205`).

## Required revisions

### R-1: Replace the strawman alternative with evidence-backed solution classes

Make `**Research:**` point explicitly to a committed research record or the committed in-body dispositioned alternatives table. The in-body route is allowed; running a research adapter is not required by this judgement.

Supply four to six genuine solution classes, with cited probe or precedent evidence for each and preserved counterarguments. Keep the cap and single-version migration classes. Replace the claim that different SDK rules make correctness for both impossible with the actual alternative: version-dependent predicates and traversal plus version-aware oracle expectations. Reject it on its additional maintained branches if that is the chosen tradeoff, not on impossibility. Treat prefix matching and accepting two error strings as oracle-repair variants, not as two independently complete solutions to semantic drift (`FR-1156:202-205`). A fourth distinct class can be normalization of mixed literals to typed composition schemas; disposition its schema-changing cost against the existing boundary rule rather than implementing it.

Preserve `is_this_a_graph: no`, distinguish FR-1154's prior dependency-upgrade prohibition as scope belonging to that FR, and cite FR-761's reproducibility obligations. The current table's dual-major alternative is a strawman, so the substantive research gate withholds authority, rather than merely granting conditional implementation permission (`judge-fr/doctrine.md`, Local conventions, research-evidence rule).

### R-2: Freeze literal eligibility and traversal with branch-specific witnesses

Specify the effective type-driven traversal rule independently of whether the node would otherwise be untyped. Use committed SDK-2.8 probe results to freeze what happens when literal keywords coexist with `type`, compositions, `$defs`, or each other. Preserve `$defs` traversal and `$ref` stopping; do not infer that the presence of a literal key alone makes its value eligible.

Add direct walker and real-SDK parity fixtures proving:

1. Eligible literals with `type: object` or `type: array` do not generate findings from ignored `properties` or `items`, including false `open_object` findings.
2. An eligible literal with `anyOf`, `oneOf`, or `allOf` still visits the selected composition and reports an untyped child at its exact path.
3. `$defs` under an eligible literal still follows the SDK's recorded traversal behavior; reference occurrences do not create duplicate paths.
4. Primitive `const` and enum members cover null, string, number, and boolean; empty enums and object/array values retain the recorded rejection behavior. Probe and state the precedence when both `const` and `enum` are present.

Update the test-local content enumeration only as necessary to reflect the same SDK traversal; otherwise its current object enumeration can claim a literal-masked object was hollowed even though the transform never processed it (`test_fr1123_sdk_parity.py:111-131`). Preserve unrelated SDK exceptions and existing open-object assertions. Update both the module rule and the public `find_untyped_subschemas` docstring.

### R-3: Bound and honestly validate the dependency amendment

Replace "whatever minimal cascade" and the contradictory "larger than the langchain-core family" stop condition with the exact recorded amendment:

| Existing pin | Revised pin |
|---|---|
| anthropic | 2.8.0 |
| langchain-anthropic | 1.7.10 |
| langchain-core | 1.8.0 |
| langsmith | 0.14.17 |
| langchain-protocol | 0.0.21 |
| certifi | 2026.10.23 |

New pins are `httpx2==2.12.0`, `httpcore2==2.12.0`, `truststore==0.10.4`, and `opentelemetry-api==1.45.2` (`FR-1156:103-107`). Any additional changed or new pin stops enforcement and requires an FR amendment; do not regenerate the whole artifact. Explicitly include certifi, which the solution's cascade list omits.

Record an executable command using the actual constraints path, interpreter version, platform, exact extras, exit status, and a resolved-package-to-pin comparison. Do not describe a Windows run with unconstrained `sspilib` as complete closure. State that Windows resolution is supplementary evidence, not a Python-3.12 reproduction. Require a clean Linux/Python-3.12 install consuming the amended artifact before claiming that artifact is reproducible; obtain that witness on a suitable host without installing an interpreter on the shared authoring host or changing CI infrastructure.

Also require an isolated install/import/schema-transform witness for `anthropic==2.8.0` with the declared minimum `langchain-anthropic==1.7.7`, or raise that floor to the lowest combination actually verified and re-submit that decision. The successful 1.7.10 resolution does not verify the 1.7.7 minimum.

### R-4: Replace proxy acceptance with direct boundary and passing-suite gates

AC-04 must require actual lint and compile witnesses, not conclude their behavior from the walker result. Use temporary fixtures in the authorized Python test file: static Anthropic emits no E016, an unresolved provider emits no W028, and a static-Anthropic compile succeeds for the mixed-literal model. No committed graph or prompt artifact change is needed. Keep a neighboring `Any` fixture refused, proving the checks were not disabled.

Replace AC-07's baseline-relative allowance with a passing targeted suite, the exact fast-unit command, strict requirement coverage, existing lint/format and import-boundary checks, and green Linux CI. Explicitly include the new test file in the targeted command; explicitly require the slow private-SDK parity tests to execute and pass, not skip or be deselected. Keep RED-before-GREEN history and existing assertions.

Record remaining failures as blockers, not acceptable baseline results. Record implementation status, the bounded dependency diff, validation environments, and any deviations in the FR; include the repository-required Distill entry with a **Seed:**.

## Scope is frozen

This table bounds a possible re-submission only. Rejection authorizes no production or test implementation.

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1156-anthropic-sdk-2-8-floor.md` and, if used, its committed research record: accurate alternatives, exact traversal contract, dependency amendment, and evidence |
| D-2 | `pyproject.toml`: the two verified Anthropic dependency floors only |
| D-3 | `constraints/dev-py312.txt`: the ten named pin changes/additions and truthful amendment provenance |
| D-4 | `yamlgraph/utils/schema_walk.py`: eligible primitive literals, SDK-aligned descent, and directly affected docstrings |
| D-5 | `tests/unit/test_fr1123_sdk_parity.py`: SDK-2.8 rejection text, literal parity fixtures, directly affected content traversal, and portable private-import path assertion |
| D-6 | `tests/unit/test_fr1156_literal_subschema.py`: independent predicate/traversal and temporary-fixture lint/compile witnesses |
| D-7 | `changelog/unreleased/fr-1156-anthropic-sdk-2-8-floor.md`, FR implementation record, and a scoped `docs/diary/` Distill entry |

Not authorized: changes to `create_llm` or FR-1154/FR-1146/FR-071 behavior; old-header test removal; full constraints regeneration; unrelated pin changes; provider fallbacks; production private-SDK imports; schema normalization; multi-version branching; new capabilities or REQ IDs; committed graphs or prompts; consumer-repository changes; CI, hook, or doctrine changes.

## Revised acceptance criteria

These are re-submission criteria, not authority activated by satisfying them alone.

- [ ] AC-01: The committed Research reference resolves to a substantive four-to-six-class alternatives record satisfying R-1, with accurate precedent dispositions and `is_this_a_graph: no`.
- [ ] AC-02: The FR fixes both dependency floors and includes an isolated minimum-pair install/import/transform witness; the proposed pair is `anthropic==2.8.0` and `langchain-anthropic==1.7.7`.
- [ ] AC-03: The constraints amendment contains exactly the six revised and four new pins in R-3, an FR-1156 provenance line, and no unrelated pin changes. Exact extras resolution and pin comparisons are recorded; a clean Linux/Python-3.12 install verifies the amended artifact.
- [ ] AC-04: The six root schemas in original AC-03 yield their exact accepted/rejected paths; primitive categories and nonprimitive values have independent REQ-YG-712 witnesses.
- [ ] AC-05: Typed literal nodes suppress type-driven findings, literal compositions retain the correct child findings, and `$defs`/`$ref` behavior and const/enum precedence match the committed SDK probes and exact-path assertions.
- [ ] AC-06: A Pydantic mixed-literal model produces no untyped finding, temporary fixture lint emits neither the applicable E016 nor W028, and static-Anthropic compile succeeds. A neighboring `Any` field still triggers the existing refusal.
- [ ] AC-07: Real SDK-2.8 rejection and content parity execute without skips across the original census, existing open-object fixtures, every Probe-2 row, and R-2's traversal fixtures. Unrelated SDK exceptions propagate. The only private-SDK import remains in `test_fr1123_sdk_parity.py` and its path assertion is platform-neutral.
- [ ] AC-08: Every added or changed test carries REQ-YG-712; behavioral RED witnesses precede GREEN in separate commits. Targeted tests explicitly include the new file and slow parity module; the fast unit suite, strict requirement coverage, existing lint/format/import checks, and Linux CI pass without weakened assertions.
- [ ] AC-09: The fix changelog fragment has `scope: deps` and `req: REQ-YG-712`; the FR records the eventual judgement fold, implementation status, exact dependency diff, environments, and deviations; the scoped Distill entry contains a **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Return to plan, record the rejected disposition on promotion, fold R-1 through R-4, and obtain a new independent judgement before implementation. This draft grants no authority. | GATE |
| C-2 | Research evidence must be committed and substantive; message-matching variants cannot stand in for a complete competing semantic solution. | GATE |
| C-3 | Freeze and witness literal traversal and minimum dependency compatibility before GREEN implementation; keep private SDK use confined to the existing oracle module. | GATE |
| C-4 | Additional dependency changes or failed Python-3.12 closure stop enforcement for an explicit amendment; neither an unconstrained platform dependency nor a Python-3.13-only run establishes artifact reproducibility. | GATE |
| C-5 | Required checks must pass; no baseline-relative failure allowance, skipped parity substitute, or weakened assertion is acceptable. | GATE |
| C-6 | Any proposed CI, hook, or doctrine change is outside this scope and requires separate judgement and human review as enforcement infrastructure. | GATE |

Authority granted: none. Only planning revisions and committed evidence for re-submission are permitted by this verdict.
