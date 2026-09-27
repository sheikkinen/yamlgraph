# Judgement: FR-1128 The #729 spike probe breaks every commit's inline-LLM check

**Prior art:** dispositioned in the parent FR header ([FR-1128](FR-1128-spike-probe-inline-llm-exemption-name.md) — FR-047, FR-599, FR-1125, FR-1110, FR-916); no REJECTED FR in this territory.

**Verdict:** APPROVED WITH REVISIONS — the existing `probe_` exemption makes the rename the smallest valid repair and a repository-scan unit test closes the merge-boundary gap, but authority activates only after the test boundary, immutable surfaces, and completion evidence are made mechanically exact.

**Reviewed against:** `feature-requests/FR-1128-spike-probe-inline-llm-exemption-name.md`; `feature-requests/047-lint-inline-llm.md`; `feature-requests/FR-599-l7-affect-recall-miss-decomposition-probe.md`; `feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md`; `scripts/lint_inline_llm.py`; `tests/unit/test_lint_inline_llm.py`; `.pre-commit-config.yaml`; `docs/spikes/constrained-object-2026-09-27/probe.py`; `docs/spikes/constrained-object-2026-09-27/README.md`; `docs/confessions.md`; `ARCHITECTURE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

1. **Scope:** The FR chooses the smallest behavioral repair: rename one retained diagnostic probe so its path satisfies the existing `probe_` exemption, rather than widening `EXCLUDE_PATHS` or rewriting the probe (`FR-1128`, lines 40-44, 60-64, 84-86). The repository evidence confirms the exemption is a substring check (`scripts/lint_inline_llm.py`, lines 58-62, 169-175) and the old name has exactly the three in-spike references the FR identifies (`probe.py`, line 20; spike `README.md`, lines 24 and 124).
2. **Consistency:** The problem, ideal result, and two-step RED/GREEN solution all address the same causal chain: a whole-tree local hook finds a tracked violation that CI does not currently test (`FR-1128`, lines 24-31, 45-52, 55-64). One inconsistency remains: the solution freezes the whole linter, while AC-03 freezes only three constants; R-2 resolves it (`FR-1128`, lines 63-64, 72-73).
3. **Measurability:** The proposed lint invocation, zero-result assertion, old-name grep, requirement marker, requirement-coverage command, and changelog artifact are observable (`FR-1128`, lines 68-78). R-1 and R-3 replace the remaining implementation-shaped or presence-only wording with exact witnesses.
4. **Feasibility:** `scan_directory` already enumerates tracked Python files with `git ls-files` and applies exclusions to repository-relative paths (`scripts/lint_inline_llm.py`, lines 136-154, 156-175). The existing unit tests already import this function and exercise clean and violating temporary trees (`tests/unit/test_lint_inline_llm.py`, lines 214-257), so a repository-root assertion requires no new dependency or production branch.
5. **Architecture alignment:** REQ-YG-073 defines the lint as detection of `main()` scripts importing LLM execution without graph loading (`ARCHITECTURE.md`, lines 357 and 862). The rename preserves that rule and the already-authorized read-only probe exception, while the repository test turns local-only detection into a merge-boundary witness, aligning with the doctrine that detection without enforcement is advisory (`.github/copilot-instructions.md`, lines 153-155).
6. **Single responsibility:** The rename removes the present false violation and the repository-level test prevents recurrence of the same invariant. They are RED and GREEN halves of one defect, not orthogonal features (`FR-1128`, lines 55-64, 68-71); a SPLIT verdict would sever the regression witness from its repair.
7. **Strategic classification:** **Pattern documentation / maintenance.** The existing abstraction already suffices: `probe_` is the accepted naming contract for read-only diagnostic probes (`scripts/lint_inline_llm.py`, line 61; `FR-599`, lines 238-240). This FR adds no framework primitive and correctly rejects changing the graph or exclusion model (`FR-1128`, lines 82-88).
8. **Testability:** A direct failing test can scan the resolved repository root and compare the returned violations with `[]`; on the cited baseline it must expose the old probe path, and after the rename the same assertion must pass (`FR-1128`, lines 40-41, 57-64, 68-71). Existing test and requirement-marker patterns are already present (`tests/unit/test_lint_inline_llm.py`, lines 214-257).

## Required revisions

### R-1: Specify the repository test exactly

Replace Proposed Solution step 1 with an exact contract: in `tests/unit/test_lint_inline_llm.py`, resolve the repository root as `Path(__file__).resolve().parents[2]`, call `scan_directory(repo_root)`, and assert that the returned list equals `[]`. State that the RED commit is made before the rename and its failure output must include `docs/spikes/constrained-object-2026-09-27/probe.py`. This removes ambiguity about `<repo root>` and proves that the test failed for the named defect rather than an import or fixture error.

### R-2: Freeze the complete enforcement surfaces

Replace AC-03 with a requirement that both `scripts/lint_inline_llm.py` and `.pre-commit-config.yaml` have no diff from baseline `d7539f93`. Freezing only `EXCLUDE_PATHS`, `LLM_IMPORTS`, and `GRAPH_IMPORTS` does not enforce the Proposed Solution's stronger statement that the linter stays unchanged, and it leaves other behavior-bearing surfaces such as `LLM_MODULES`, path enumeration, and hook invocation unguarded.

### R-3: Make completion artifacts substantive

Replace AC-06 with the repository's complete completion contract: the `fix` changelog fragment names FR-1128 and REQ-YG-073 and passes the repository changelog checks; the FR records implemented status, RED and GREEN commit SHAs, exact validation results, decisions, and deviations; and a Distill entry under `docs/diary/` contains a literal `Seed:`. This folds the repository doctrine's source-of-truth and Distill requirements into mechanically reviewable evidence (`.github/copilot-instructions.md`, lines 26-28, 214).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/unit/test_lint_inline_llm.py`: one repository-root invariant test carrying `@pytest.mark.req("REQ-YG-073")` |
| D-2 | Rename `docs/spikes/constrained-object-2026-09-27/probe.py` to `docs/spikes/constrained-object-2026-09-27/probe_constrained_object.py` |
| D-3 | Update only the renamed probe's `Run:` path and the two filename references in `docs/spikes/constrained-object-2026-09-27/README.md` |
| D-4 | One conforming `fix` fragment in `changelog/unreleased/` |
| D-5 | FR-1128 implementation-status, decision, deviation, commit, and validation record |
| D-6 | One FR-1128 Distill entry in `docs/diary/` with `Seed:` |

Not authorized: changes to `scripts/lint_inline_llm.py`, `.pre-commit-config.yaml`, exclusion semantics, graph-loading policy, provider behavior, the probe's executable logic, `probe-output.txt`, `results.json`, FR-1125's implementation, or any graph/prompt artifact.

## Revised acceptance criteria

- [ ] AC-01: In a committed RED change based on `d7539f93` and preceding the rename, `test_repository_has_no_inline_llm_violations` resolves `Path(__file__).resolve().parents[2]`, calls `scan_directory(repo_root)`, asserts the result equals `[]`, carries `@pytest.mark.req("REQ-YG-073")`, and fails with output naming `docs/spikes/constrained-object-2026-09-27/probe.py`; the failure is not an import, collection, or fixture error.
- [ ] AC-02: In a separate later GREEN commit, the tracked file is renamed to `docs/spikes/constrained-object-2026-09-27/probe_constrained_object.py`; the focused repository-invariant test passes, `scan_directory(repo_root) == []`, and `python scripts/lint_inline_llm.py` exits 0.
- [ ] AC-03: `git diff --exit-code d7539f93 -- scripts/lint_inline_llm.py .pre-commit-config.yaml` exits 0.
- [ ] AC-04: `git grep -n "probe\.py" -- docs/spikes/constrained-object-2026-09-27/` returns no matches; the renamed probe's `Run:` line and both spike README references name `probe_constrained_object.py`; `git ls-files --error-unmatch docs/spikes/constrained-object-2026-09-27/probe_constrained_object.py` exits 0 and the old path is not tracked.
- [ ] AC-05: The focused inline-LLM test module, the non-slow unit suite, and `python scripts/req_coverage.py --strict` all exit 0.
- [ ] AC-06: A `changelog/unreleased/*.md` fragment has `type: fix`, names FR-1128 and REQ-YG-073, describes restoration of the repository-wide inline-LLM invariant, and passes the repository changelog checks.
- [ ] AC-07: FR-1128 records Implemented status, RED and GREEN commit SHAs, exact validation commands and results, decisions, and deviations; a corresponding `docs/diary/` Distill entry contains a literal `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | A human must review the repository-wide test as an enforcement-boundary change before merge. | GATE |
| C-2 | Preserve the two-commit RED-then-GREEN history: the committed RED witness must precede the rename and fail for the named probe path only. | GATE |
| C-3 | Do not modify `scripts/lint_inline_llm.py` or `.pre-commit-config.yaml`; any required change to either surface stops enforcement and returns to planning. | GATE |
| C-4 | Do not alter the probe's executable logic or generated evidence; only the file rename and its three filename references are authorized. | GATE |
| C-5 | Do not weaken, broaden, or add an exclusion and do not convert the probe into a graph. | GATE |
| C-6 | Fold R-1 through R-3 into FR-1128 before implementation authority becomes active. | GATE |

Authority granted: after R-1 through R-3 are folded, implement only the repository invariant test, the exemption-conforming probe rename and three reference updates, and the required changelog, FR record, and Distill artifacts listed above.
