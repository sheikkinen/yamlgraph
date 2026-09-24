# Plan: Test Mutator — does the suite catch planted bugs?

Status: planning (pre-FR). Next step: file an FR from this plan, judge it via
the adapter, then author the graph via `scripts/author.sh`.

## Intent

A green suite proves the code passes the tests; it does not prove the tests can
fail. The mutator plants plausible bugs one at a time, runs the tests that
should see them, and records whether they did. Every surviving mutant is either
an equivalent mutant or a named test gap.

## Ideal Result

One command produces, for a pinned SHA:

- a per-file mutation plan (what was planted, why, which test should catch it);
- a per-mutant verdict (`killed` / `survived` / ...), with the failing test
  and the failure reason;
- a survivor list ranked by severity, each row a candidate FR or an
  equivalent-mutant disposition;
- proof the main checkout was never touched.

Minimal path back: freeze file corpus → map (LLM plans mutants per file) →
deterministic executor in a worktree → reconcile → report.

## Non-goals

- Not a CI gate (first run is a census; gating is a later FR if scores stabilise).
- No automatic test writing. Survivors are reported, not fixed.
- No mutation of tests, prompts, graphs, or hooks in v1 — `yamlgraph/**/*.py` only.

## Architecture

```mermaid
flowchart LR
  Freeze[Freeze corpus: path, sha256, git SHA] --> Select[Test selection per file]
  Select --> Map([map: plan mutants per file])
  Map --> Save[Save plans/&lt;file&gt;.yaml]
  Save --> Exec[Executor in worktree: apply, run, revert]
  Exec --> Reconcile[Reconcile: every planned mutant has a verdict]
  Reconcile --> Report[Report + survivor ledger]
```

Split of responsibility (three-layer rule):

| Stage | Owner | LLM? |
|---|---|---|
| Freeze, test selection | Python tool | no |
| Plan mutants | YAML `map` node + prompt | yes |
| Apply / run / revert | Python tool | no |
| Survivor triage (equivalent vs gap) | optional second `map` | yes |
| Reconcile, report | Python tool | no |

The LLM only *proposes*. Everything it emits is a claim reconciled against the
source at the boundary (`two_strike_split`).

## Stage 1 — Freeze

- Corpus: `git ls-files 'yamlgraph/**/*.py'` at a pinned SHA (139 files today).
- Record `{path, sha256, bytes}` + `git rev-parse HEAD` in
  `tmp/mutator/<run_id>/corpus.yaml`. Every artifact carries the SHA
  (`artifact_carries_code_identity`).
- Exclude `__init__.py` with no logic, generated files, and files with zero
  selected tests (reported as `no_tests`, not silently dropped).

## Stage 2 — Test selection

Deterministic, not LLM-guessed:

1. Run the unit suite once with `pytest --cov=yamlgraph --cov-context=test`
   (coverage dynamic contexts; not configured today — probe required).
2. Per source file, per line: the set of tests that executed it.
3. A mutant on line L runs only the tests that covered L. Fallback: tests that
   import the module (reported as `selection=import`, lower confidence).

Baseline: selected tests must pass twice on the unmutated worktree. A red or
flaky baseline aborts that file (`baseline_red` / `baseline_flaky`) — never
counted as a kill.

## Stage 3 — Plan mutants (the map)

Reuse `examples/demos/corpus_census` (FR-892 discover/extract tool slots,
`max_map_items: 200`) if its finding schema can carry a mutant list; otherwise
a dedicated graph. Decide in the FR after reading the census graph's schema.

Per-file input: file source (with line numbers), covered-line map, names of
covering tests.

Per-file output (inline schema), saved as
`tmp/mutator/<run_id>/plans/<path_with_underscores>.yaml`:

```yaml
file: yamlgraph/utils/llm_factory.py
sha256: "..."
git_sha: "..."
mutants:
  - id: llm_factory-003
    operator: boundary          # see catalogue
    line: 88
    original: "if retries >= max_retries:"
    replacement: "if retries > max_retries:"
    rationale: "off-by-one lets one extra retry through"
    expected_detector: tests/unit/test_llm_factory.py::test_retry_limit
    equivalent_risk: low        # low|medium|high
```

Bounds (from past runaway incidents): 3–8 mutants per file, stated as a range,
not only a cap. Only lines in the covered-line map are eligible; uncovered
lines are already known gaps and are reported by coverage, not mutated.

### Operator catalogue (prompt vocabulary)

Mechanical classes plus repo-specific ones drawn from the Scripture traps:

| Operator | Example |
|---|---|
| `boundary` | `>=` → `>`, `[:200]` → `[:199]` |
| `negate` | drop/insert `not` |
| `constant` | default/timeout/limit changed |
| `return_value` | return `None` / `[]` / `{}` instead of result |
| `swallow` | `raise` → `pass` / log-and-continue |
| `silent_fallback` | empty filter result → return everything (Commandment 6) |
| `wrong_key` | state/dict key swapped for a sibling key |
| `drop_call` | remove a side-effect call (validation, normalisation) |
| `order` | swap two statements with a data dependency |
| `type_lie` | skip a Pydantic/`isinstance` normalisation at a boundary |

## Stage 4 — Execute (sandbox)

Runs in a detached worktree, never in the main checkout:

- `scripts/worktree.sh spike` (or `new`) at the pinned SHA, under
  `tmp/worktrees/`. Assert `git rev-parse HEAD == corpus git_sha` before start.
- For each mutant, sequentially within a worktree:
  1. Verify `original` occurs **exactly once** on/near `line` in the file.
     Zero or many → `not_applied` (the LLM's claim failed reconciliation).
  2. Apply the replacement (string edit of that single occurrence).
  3. `python -m py_compile` → failure = `stillborn` (not a kill).
  4. Run selected tests: `pytest <ids> -x -q --no-cov -p no:cacheprovider`
     with a timeout of `max(3 × baseline, 30s)`; output to a per-mutant log.
  5. `git checkout -- <file>`; assert `git status --porcelain` is empty.
- Parallelism: N worktrees, one mutant in flight per worktree (no shared index
  or tree between workers — `one_session_one_repo`).
- No LLM calls, no network, API keys unset in the executor env so a mutant
  cannot reach a provider.

## Stage 5 — Verify the verdicts

A red run is not automatically a kill. Classify from the log, not the exit code:

| Verdict | Condition |
|---|---|
| `killed` | ≥1 selected test fails with an assertion/expected-exception failure |
| `killed_by_error` | fails only by collection/import error or unrelated exception — recorded separately; weak evidence |
| `survived` | all selected tests pass |
| `timeout` | exceeded timeout (counted as detected, flagged) |
| `stillborn` | did not compile |
| `not_applied` | `original` not found exactly once |

Also record `detector_matched`: did the predicted `expected_detector` actually
fail? A kill by a different test is fine; a prediction miss rate is a signal of
planning quality.

Canaries (per run, must hold or the run is invalid):

- **Positive canary:** one mutant per sampled file replacing a covered
  function body with `raise AssertionError("canary")` — must be `killed`. A
  surviving canary means test selection is broken, not the suite.
- **Negative canary:** one known-equivalent edit (e.g. rename a local
  variable consistently) — must `survive`. A kill means the harness is noisy.

Reconciliation: `planned == applied + not_applied + stillborn`; every applied
mutant has exactly one verdict; every corpus file has a plan or an explicit
skip reason.

## Stage 6 — Report

`tmp/mutator/<run_id>/report.md` + `results.yaml`:

- mutation score per file and overall: `killed / (applied − stillborn)`;
  `killed_by_error` shown separately, not merged.
- survivors listed by operator and file, with original/replacement diff and
  rationale. Read the survivors by name before trusting any score.
- optional triage map: LLM labels each survivor `equivalent` / `gap` with a
  one-line reason; `gap` rows become FR candidates. Triage is a claim; a human
  samples it.

## Cost estimate (to be confirmed by a 5-file pilot)

- Plan: 139 files × 1 cheap-model call (haiku) ≈ 139 calls.
- Execute: ~139 × 5 ≈ 700 mutants × selected-test runtime (seconds each with
  line-level selection) + 2 baseline runs per file.
- Coverage-context run: one full unit-suite run.

## Alternatives (unprobed except where marked)

| Option | Status |
|---|---|
| `mutmut` / `cosmic-ray` | probed: neither installed in `.venv`. Mechanical operators, no repo-specific bug classes; worth a pilot on the same 5 files as a comparison baseline. |
| LLM plans + LLM applies edits | rejected: application must be deterministic and revertible. |
| Mutate in main checkout | rejected: FR-889 main lock; shared-tree risk. |
| Run full suite per mutant | rejected on cost; kept as the verification for a sample of survivors (selection may have missed a detector). |

## Pre-mortem

- *All mutants killed* → check the killed_by_error share and the positive/negative canaries before celebrating.
- *Many survivors on one file* → first check its test selection (import fallback?), then equivalence, then gap.
- *Worktree left dirty* → the per-mutant `git status` assertion must abort the run, not warn.
- *LLM plans mutants on lines that moved* → reconciliation by exact string, never by line number alone.
- *Test pollution* → one worker's mutant leaking into another via shared `tmp/` or env; each worker uses its own worktree and temp dir.

## Open questions for the FR

1. Reuse `corpus_census` or a dedicated graph?
2. Coverage contexts: enable in `pyproject.toml` or pass via CLI only for the mutator?
3. Pilot file set (suggest 5 files with known incident density: `utils/llm_factory.py`, `executor_base.py`, `graph_loader` modules, a map-node module, a tool module).
4. Threshold for turning this into a CI signal (not in v1).

## Acceptance criteria (draft)

- AC-1: Running the mutator never modifies the main checkout (witness: `git status` of main before/after identical; executor refuses to start outside `tmp/worktrees/`).
- AC-2: One plan file per corpus file or an explicit skip reason; counts reconcile.
- AC-3: Every applied mutant has exactly one verdict from the table above, derived from the pytest log.
- AC-4: Positive and negative canaries hold on the pilot.
- AC-5: Pilot report lists survivors with diff + rationale; at least the survivors are read and dispositioned by a human before the full run.
