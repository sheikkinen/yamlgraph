# Judgement: FR-842 Lint/Compile Validation Parity

**Verdict:** APPROVED WITH REVISIONS — the parity fix is real, minimal, and aligned, but authority activates only after the FR tightens its ambiguous baseline-evidence, error-code, and continuation semantics. R-1 through R-4 were folded into the FR on 2026-08-20 (frozen issue code: `E000`); human publication gate pending.

**Prior art:** FR-025/FR-047 built the lint suite and already noted the missing `validate_condition_expression` call; FR-110 lints state-variable expressions; FR-406 owns the JSON/exit-code contract preserved here. GitClaw FR-840 run `32361594593` is the live witness; canonical `846ddfe` records the flat-edge workaround. The runtime evaluator in `yamlgraph/utils/conditions.py` stays unchanged — grammar extension is fenced to a separate FR.

**Reviewed against:** `feature-requests/FR-842-lint-compile-validation-parity.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `yamlgraph/utils/validators.py`; `yamlgraph/linter/graph_linter.py`; `yamlgraph/utils/conditions.py`; `yamlgraph/linter/checks.py`; `yamlgraph/cli/graph_validate.py`; `reference/cli.md`; `feature-requests/025-linter-cross-ref-checks.md`; `feature-requests/047-lint-inline-llm.md`; `feature-requests/FR-110-lint-state-variable-expressions.md`; `feature-requests/FR-406-lint-json-output.md`.

## What is sound

The problem is substantiated and statically diagnosable. The FR identifies a concrete lint/compile gap where lint reports success while compile-time validation rejects a parenthesized condition (`feature-requests/FR-842-lint-compile-validation-parity.md:14-23`). The cited code supports that claim: `lint_graph` runs many bespoke checks but does not call `validate_config` (`yamlgraph/linter/graph_linter.py:97-155`), while `validate_config` calls `validate_edges` (`yamlgraph/utils/validators.py:230-238`) and `validate_edges` validates every `condition` (`yamlgraph/utils/validators.py:94-102`).

The proposed fix is architecturally correct because it reuses the loader validator instead of duplicating grammar rules (`feature-requests/FR-842-lint-compile-validation-parity.md:67-74`). That matches the repo pattern of avoiding parallel rule definitions, and it directly addresses the prior FR-025 gap: FR-025 already noted that the linter did not call `validate_condition_expression` (`feature-requests/025-linter-cross-ref-checks.md:78-92`).

The scope fence is appropriately narrow. Keeping parenthesized conditions rejected is consistent with the runtime evaluator, which only quote-splits on flat `and`/`or` and then requires a single comparison regex match (`yamlgraph/utils/conditions.py:191-204`). The FR also preserves FR-406's JSON/exit-code contract rather than altering output transport (`feature-requests/FR-842-lint-compile-validation-parity.md:75-79`; `feature-requests/FR-406-lint-json-output.md:62-71`).

Strategic classification: **Framework primitive**. `yamlgraph graph lint` is the authoring and CI pre-flight surface for all graphs, not a GitClaw-only example; parity with load-time validation has broad reuse across external schedulers, demos, and CI.

## Required revisions

### R-1: Replace the baseline-evidence acceptance criterion with an enforceable RED/GREEN criterion

Rewrite AC-01 so the committed regression test asserts the desired final behavior, not that the old baseline "passes lint." The historical baseline observation belongs in implementation notes or the FR evidence record; the final test suite must not preserve a test that expects the defective behavior.

### R-2: Freeze the compile-validation lint issue code

Replace "E001-compile-validation or the existing error taxonomy's next free id" with one exact code, and require that code in tests. `LintIssue.code` is a string (`yamlgraph/linter/checks.py:50-57`), but existing lint codes already reuse numeric ranges across modules, so the FR must name the intended stable code rather than leaving the enforcer to choose one.

### R-3: Specify whether lint continues after compile-validation failure

Add an explicit rule: `lint_graph` must append the compile-validation error and still run the existing lint checks when they can operate on the parsed YAML object; only YAML parse/read failures may abort through the existing CLI exception path. This preserves the linter's diagnostic aggregation behavior (`yamlgraph/linter/graph_linter.py:95-164`) while preventing a single compile validator failure from hiding unrelated lint errors.

### R-4: Narrow "exact message" to the `LintIssue.message` field

State that the caught `ValueError` text from `validate_config` must appear unchanged in the new `LintIssue.message`. Human CLI formatting and JSON object wrapping need not be byte-identical to loader exceptions, because `cmd_graph_lint` derives exit status from `issue.severity == "error"` and prints either human formatting or `LintResult.model_dump_json()` (`yamlgraph/cli/graph_validate.py:190-204`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/linter/graph_linter.py` or a small helper it calls from `yamlgraph/linter/` |
| D-2 | Regression tests in the existing linter/CLI test surface, especially `tests/unit/test_graph_linter.py`, `tests/unit/test_linter_fr025.py`, or a dedicated FR-842 test file |
| D-3 | Invalid graph fixtures needed for compile/lint parity tests |
| D-4 | `reference/cli.md` lint documentation |
| D-5 | Changelog fragment under `changelog/unreleased/` |

Not authorized: condition grammar extensions; parenthesis support; evaluator changes in `yamlgraph/utils/conditions.py`; loader behavior changes in `yamlgraph/utils/validators.py` except where a test proves an existing validator bug directly blocks this FR; new CLI flags; JSON schema changes; GitClaw repository changes; broad linter rewrites; changes to judge/review doctrine or hooks.

## Revised acceptance criteria

- [ ] AC-01: A committed regression test constructs or loads a graph containing the FR-840 grouped condition and asserts `lint_graph(...).valid is False`.
- [ ] AC-02: That regression test asserts the lint result contains one `severity == "error"` issue whose `message` includes the unchanged validator text `invalid condition syntax`.
- [ ] AC-03: A CLI-level test or existing CLI assertion proves `yamlgraph graph lint <invalid-compile-graph>` exits nonzero through the normal lint error path, not by an uncaught exception.
- [ ] AC-04: `lint_graph` calls the same `validate_config` path used by graph loading; no duplicate condition grammar, edge-field grammar, `on_error` grammar, or node-schema grammar is introduced in linter code.
- [ ] AC-05: Parity tests cover at least these `validate_config` rejection classes: grouped condition syntax, missing edge `from`, missing edge `to`, invalid `on_error`, and graph-schema validation error.
- [ ] AC-06: Existing linter checks still run when a compile-validation error is appended and the parsed YAML shape allows them to run.
- [ ] AC-07: JSON mode still emits `LintResult` JSON with compile-validation failures represented as normal lint issues, and exit-code semantics remain unchanged: errors exit 1; warnings-only or clean runs exit 0.
- [ ] AC-08: Parenthesized grouping remains rejected by compile validation, lint, and runtime; the flat-edge workaround is documented in the lint reference.
- [ ] AC-09: A changelog fragment is added, targeted linter/CLI tests pass, and the full unit suite plus lint gates pass.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into the FR before implementation authority activates. | GATE |
| C-2 | Do not implement or relax boolean-condition parenthesis support under this FR. | GATE |
| C-3 | Do not duplicate compile-time validation rules in linter checks; call the loader validation boundary. | GATE |
| C-4 | Do not change `graph lint --json` payload schema beyond naturally including the new lint issue. | GATE |
| C-5 | Do not make lint fail by surfacing compile validator exceptions through the CLI's generic exception handler; failures must be ordinary `LintIssue` errors. | GATE |

Authority granted: after the required revisions are folded into the FR, implement lint/load validation parity by adding compile-time validation errors to the existing linter result stream while preserving existing lint checks, JSON output shape, and condition grammar.
