# Feature Request: Retire `yamlgraph graph bench` (bench_commands, CAP-90)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Draft — awaiting judgement
**Effort:** 0.5 day
**Requested:** 2026-08-29
**First consumer / first event:** every maintainer and CI run from the merge
onward — the first event is this FR's own PR pipeline, which stops running a
dead command's test file and stops asserting a capability claim whose only
operational consumer is one demo shell script this FR migrates.
**Research:** consumer-record sweep 2026-08-29 (method of
[docs/research-agentic-sdlc-providers-2026-08-29.md](../docs/research-agentic-sdlc-providers-2026-08-29.md) §4.4)
+ second-strike conviction in
[docs/diary/diary-2026-05-31-letter-to-the-philosopher.md](../docs/diary/diary-2026-05-31-letter-to-the-philosopher.md)
("dead code wearing a 'utility' costume"; listed under removals at 336 lines).
**Prior art:** FR-231 (the surface being retired — spec survives there and in git history); the 2026-05-31 diary removal list (first strike; this sweep is the confirmed recurrence per the graduation rule); FR-465/FR-466 + FR-470/CAP-163 (retirement mechanism and format — followed); CAP-89/FR-231 (execution-timing callback — shared with `graph run --timing`, explicitly KEPT); siblings FR-909/FR-910/FR-912 (same evidence class, separate surfaces).

## Summary

Delete the `yamlgraph graph bench` subcommand —
`yamlgraph/cli/bench_commands.py` (336 lines), its subparser wiring, its
dispatch branch, and `tests/unit/test_bench_command.py` — retire CAP-90 per
the FR-465/466 precedent, and migrate its single real consumer
(`examples/demos/hellograph-speed/compare_speed.sh`) to plain timed
`yamlgraph graph run` invocations.

## Value Statement

Maintainers shed 336 code lines, a dead test file, and one capability claim.
The timing question the command answered is already served by
`graph run --timing` (CAP-89, kept) and the hellograph-speed demo graphs.

## Problem

`yamlgraph graph bench` (FR-231) runs a graph across multiple
provider/model combos and prints a comparison table. Its consumer record
after ~5 months: one demo script (`compare_speed.sh` — which invokes it
once per provider, i.e. uses none of the multi-model comparison the command
exists for), its own unit test, and two historical doc mentions. No script,
CI job, hook, or chaplain pipeline runs it. The 2026-05-31 diary already
convicted it — "How often is it used? If the answer is 'never since it was
written,' it's dead code wearing a 'utility' costume" — and listed it for
removal; fifteen weeks later the answer to its question is still never.
Second strike: retirement is due (`graduation`, `growth_as_default`).

**Honest record:** the initial sweep grep (`yamlgraph bench`) missed
`compare_speed.sh` because the real invocation is `yamlgraph graph bench` —
the defective-grep class the FR-909/910 judge flagged. The consumer was
found by widening to `graph bench|bench_commands|cmd_graph_bench` and is
dispositioned by migration, not ignored.

## Ideal Result

`git grep bench -- yamlgraph` returns nothing; the `graph bench` subparser
and dispatch branch are gone; `compare_speed.sh` still demonstrates the
three-provider speed comparison using `graph run`; CAP-90 reads
`status: retired` citing this FR; CAP-89 (`--timing`,
`utils/timing_tracker.py`) is untouched and still tested; the full suite
and `req_coverage.py --strict` are green; the bench spec survives in FR-231
so resurrection — e.g. inside a future eval harness with quality metrics,
as the 2026-05-31 diary sketched — is a disposition of this FR, not
archaeology.

## Proposed Solution

Mechanical deletion, one consumer migration, registry retirement:

1. **Code**: delete `yamlgraph/cli/bench_commands.py`; remove the
   `graph bench` subparser block (`yamlgraph/cli/__init__.py:192–~230`) and
   the dispatch branch in `yamlgraph/cli/graph_commands.py:344–346`.
2. **Consumer migration**: rewrite
   `examples/demos/hellograph-speed/compare_speed.sh` to call
   `yamlgraph graph run <graph> --var-file ./vars.yaml --timing` per
   provider (loop `--runs` in shell if the demo keeps repetition); re-run
   the demo and commit `demo-output.log` (demo-gate, FR-206).
3. **Tests**: delete `tests/unit/test_bench_command.py`; add a narrow
   FR-913 witness test asserting the `graph` subparser rejects `bench` as
   an unknown subcommand. Timing-tracker tests (CAP-89) are untouched.
4. **Docs**: remove `bench` from the `graph` usage line in
   `reference/cli.md:26` and its command section; remove the bench mention
   in `reference/getting-started.md`; remove the active CAP-90 row from
   `ARCHITECTURE.md`; regenerate `reference/module-map.md`.
5. **Registry**: CAP-90 → `status: retired`, description prefixed
   `RETIRED by FR-913` (file stays, per CAP-163). CAP-89 remains active —
   verify its REQ coverage does not route through the deleted test.
6. **Changelog**: fragment `type: removal`.

Kept: `yamlgraph/utils/timing_tracker.py`, the `--timing` flag on
`graph run`, CAP-89 and its tests; `examples/demos/hellograph-speed/`
(migrated, not deleted); FR-231/FR-299 and all diary/doc history.

**Boundary:** this FR does NOT touch the timing callback (CAP-89), the
hellograph-speed graphs, the eval-harness idea (future FR if ever), or the
sibling retirement surfaces (FR-909/910/912).

## Acceptance Criteria

- [ ] AC-01: `git ls-files 'yamlgraph/cli/bench_commands.py'` prints nothing, and `git grep -nE 'bench_commands|cmd_graph_bench|BenchResult' -- yamlgraph` prints no live references
- [ ] AC-02: a new FR-913 witness test asserts the `graph` subparser rejects `bench`; no `bench` subparser or dispatch branch remains in `yamlgraph/cli/`
- [ ] AC-03: `tests/unit/test_bench_command.py` is deleted; timing-tracker/CAP-89 tests still pass; `python scripts/req_coverage.py --strict` passes with CAP-90 retired
- [ ] AC-04: `examples/demos/hellograph-speed/compare_speed.sh` contains no `graph bench` invocation, runs green via `graph run`, and the diff includes a fresh `demo-output.log` (FR-206 demo-gate)
- [ ] AC-05: `reference/cli.md`, `reference/getting-started.md`, and `ARCHITECTURE.md` contain no live bench advertising; `reference/module-map.md` regenerated
- [ ] AC-06: CAP-90 carries `status: retired` + `RETIRED by FR-913`; CAP-89 unchanged; `scripts/validate_capabilities.py` passes
- [ ] AC-07: full unit suite passes with the witness test present
- [ ] AC-08: changelog fragment under `changelog/unreleased/` with `type: removal` naming FR-913

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Keep as-is | REFUTED — second-strike conviction; sole consumer uses one model per call, defeating the command's purpose |
| Keep for compare_speed.sh | REFUTED — the script needs timed runs, not a comparison table; `graph run --timing` serves it with zero bespoke code |
| Fold into a native eval harness now | REFUTED — that harness is an unfiled future FR; holding 336 dead lines hostage to it is `growth_as_default` |
| Delete hellograph-speed demo too | REFUTED — the demo has a real question (provider speed) and stays; only its transport changes |

## Related

- Origin: FR-231 (bench command + timing callback), FR-299 (promptfoo router eval — bench mention only)
- First strike: docs/diary/diary-2026-05-31-letter-to-the-philosopher.md (removal list)
- Precedent: FR-465/FR-466, FR-470, CAP-163; siblings FR-909, FR-910, FR-912
- Kept twin: CAP-89 execution-timing callback (`graph run --timing`)
