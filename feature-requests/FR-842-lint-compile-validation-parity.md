# Feature Request: FR-842 Lint/Compile Validation Parity

**Priority:** HIGH
**Type:** Bug / Linter completeness
**Status:** Enforced 2026-08-20 - implemented at `34e0fce0`; red 8 targeted
failures then 9/9 green; full unit suite 5963 passed at 89.97% coverage; all
pre-commit gates green; lint issue code frozen as `E000`
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Depends on:** FR-025 (linter cross-ref checks), FR-047 (lint CLI)
**Blocks:** Trustworthy pre-flight validation for any externally scheduled
graph (GitClaw intake, cron, CI)
**Prior art:** FR-025/FR-047 built the lint check suite; FR-110 lints state
variable expressions; FR-406 added lint JSON output. None of them execute the
compile-time config validators, so lint and compile enforce different
grammars. The GitClaw FR-840 rollout is the live witness: `yamlgraph graph
lint gitclaw.yaml` reported "No issues found" while the first intake run in
`sheikkinen/gitclaw-yle-haiku` failed at compile with `Edge 21 has invalid
condition syntax: '(review_verdict == 'REJECTED' or review_verdict ==
'APPROVED WITH REVISIONS') and _loop_counts.enforce == null'` (run
`32361594593`), consuming a full CI pipeline attempt to discover a statically
detectable defect. The condition grammar itself is honest: the runtime
evaluator in `yamlgraph/utils/conditions.py` is regex/split-based and cannot
evaluate parenthesized grouping, so the compile validator correctly rejects
it — the defect is that lint never runs that validator.
**First consumer / first event:** The next `yamlgraph graph lint` invocation
in a GitClaw repository's authoring or CI flow, when a graph that cannot
compile must be reported at lint time instead of failing a scheduled run.

## Summary

Make `yamlgraph graph lint` a strict superset of compile-time validation: any
graph that lint passes must load through `validate_config` without error.
Execute the compile-time validators inside `lint_graph` and surface their
`ValueError`s as lint errors with the same message text, before the
style/semantic checks run.

Do not extend the condition grammar. Parenthesized grouping stays rejected by
both compile and lint because `evaluate_condition` cannot evaluate it; the
documented workaround is flat per-branch edges (as applied in GitClaw commit
`846ddfe`). Any grammar extension is a separate FR that must change parser,
validator, evaluator, and `negate_condition` together.

## Root Cause

- Compile path: `graph_loader` -> `validate_config`
  (`yamlgraph/utils/validators.py:238`) -> `validate_edges` ->
  `validate_condition_expression`, which splits on `and`/`or` and requires
  every part to match `field <op> value`. A leading `(` fails the match.
- Lint path: `lint_graph` (`yamlgraph/linter/graph_linter.py`) aggregates
  style, cross-reference, contract, prompt, provider, and pattern checks —
  none of which invoke `validate_config` or `validate_condition_expression`.
- Runtime path: `yamlgraph/utils/conditions.py` (`_split_compound`,
  `evaluate_comparison`) has no parenthesis support, so the compile rejection
  protects real runtime behavior.

Lint therefore validates a *different, looser* language than the one the
loader accepts, and the gap surfaces only when a scheduled run pays for it.

## Ideal Result

`yamlgraph graph lint <graph>` fails, with the loader's exact error message,
for every graph that `yamlgraph graph run <graph>` would refuse to load — and
a regression test enforces that parity so future validator additions are
automatically covered by lint.

## Design

1. In `lint_graph`, before existing checks, run the complete compile-time
   config validation (`validate_config`) on the parsed graph dict inside a
   `try/except ValueError`, converting each failure into a lint error entry
   with severity `error` and the frozen issue code `E000` (R-2; `E000` is
   unused in the current `E001`-`E802` taxonomy and sorts before all checks).
2. The caught `ValueError` text from `validate_config` must appear unchanged
   in the new `LintIssue.message`; human CLI formatting and JSON wrapping need
   not be byte-identical to loader exceptions (R-4).
3. Diagnostic continuation (R-3): `lint_graph` appends the compile-validation
   error and still runs the existing lint checks whenever they can operate on
   the parsed YAML object; only YAML parse/read failures may abort through the
   existing CLI exception path. A compile-validation failure must never hide
   unrelated lint errors, and must never surface as an uncaught exception.
4. Parity by construction, not duplication: call the same functions the
   loader calls; do not copy their rules into a parallel lint check that can
   drift.
5. Keep JSON output (FR-406) and exit-code semantics unchanged: compile
   validation failures are errors, not warnings.
6. Document in the lint reference that lint is a superset of load-time
   validation, and record the flat-condition workaround for grouped
   boolean logic.

## Validation

Baseline evidence (R-1): the historical observation that the FR-840 grouped
condition passed lint on the pre-fix baseline is recorded here as evidence
(GitClaw run `32361594593`, lint "No issues found"); the committed final test
suite asserts only the desired behavior and never expects the defective one.

- Regression test: a fixture graph containing the exact FR-840 grouped
  condition; assert `lint_graph(...).valid is False` and that the result
  contains one `severity == "error"` issue with code `E000` whose `message`
  includes the unchanged validator text `invalid condition syntax`.
- CLI test: `yamlgraph graph lint <invalid-compile-graph>` exits nonzero
  through the normal lint error path, not an uncaught exception.
- Parity regression across `validate_config` rejection classes: grouped
  condition syntax, missing edge `from`, missing edge `to`, invalid
  `on_error`, and graph-schema validation error — loader rejection implies a
  lint error for each.
- Continuation: with a compile-validation error present, existing lint checks
  still run and their unrelated findings still appear.
- Valid graphs (existing lint test corpus plus `gitclaw.yaml` post-`846ddfe`
  shape) remain clean; JSON schema and exit codes unchanged.
- Full unit suite and lint self-checks pass.

## Acceptance Criteria

- [x] AC-01: A committed regression test constructs or loads a graph containing
      the FR-840 grouped condition and asserts `lint_graph(...).valid is False`
- [x] AC-02: That regression test asserts the lint result contains one
      `severity == "error"` issue with code `E000` whose `message` includes the
      unchanged validator text `invalid condition syntax`
- [x] AC-03: A CLI-level test proves `yamlgraph graph lint
      <invalid-compile-graph>` exits nonzero through the normal lint error
      path, not by an uncaught exception
- [x] AC-04: `lint_graph` calls the same `validate_config` path used by graph
      loading; no duplicate condition, edge-field, `on_error`, or node-schema
      grammar is introduced in linter code
- [x] AC-05: Parity tests cover grouped condition syntax, missing edge `from`,
      missing edge `to`, invalid `on_error`, and graph-schema validation error
- [x] AC-06: Existing linter checks still run when a compile-validation error
      is appended and the parsed YAML shape allows them to run
- [x] AC-07: JSON mode still emits `LintResult` JSON with compile-validation
      failures as normal lint issues; errors exit 1, warnings-only or clean
      runs exit 0
- [x] AC-08: Parenthesized grouping remains rejected by compile validation,
      lint, and runtime; the flat-edge workaround is documented in the lint
      reference
- [x] AC-09: A changelog fragment is added, targeted linter/CLI tests pass,
      and the full unit suite plus lint gates pass

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-025 / FR-047 | Extend the existing lint entry point; keep all current checks and ids |
| FR-110 | State-variable expression lint stays; this FR adds the loader-grammar layer it assumed existed |
| FR-406 | Preserve JSON output contract; compile failures use the error severity |
| GitClaw `846ddfe` | Flat-condition workaround remains the supported form; cite as documentation example |
| `utils/conditions.py` evaluator | Unchanged; grammar extension is out of scope for a separate FR |

## Alternatives Rejected

- **Teach the parser/evaluator parentheses:** larger blast radius (validator,
  evaluator, negation, docs) and no current in-repo consumer needs grouping;
  flat edges express the same routing.
- **Loosen the validator to accept parens:** would ship graphs the runtime
  evaluator silently mis-evaluates — worse than the current failure.
- **Duplicate the condition regex inside a new lint check:** creates a second
  grammar definition that will drift exactly like this incident.

## Scope Fence

FR-842 authorizes the lint-parity change in `yamlgraph/linter/`, its tests,
docs, and changelog fragment. It authorizes no condition-grammar, evaluator,
loader-behavior, CLI-flag, or GitClaw-repository change.
