# Feature Request: Retire the stale FR knowledge graph and the FR-275 meta-tests

**Priority:** MEDIUM
**Type:** Enhancement (removal)
**Status:** Approved (judge SPLIT, operator override 2026-09-28 — see judgement)
**Effort:** 0.5 day
**Requested:** 2026-09-27
**First consumer / first event:** the `test (3.11)` / `test (3.14)` CI jobs
on this PR (≈100 s less sequential test time per job), and the prior-art
hook on the next FR file created after merge (it stops parsing a 270 KB
YAML file that holds no node for any FR filed since 2026-08-18).
**Research:** in-body measurement record (§ Problem) and dispositioned
alternatives table (§ Alternatives Considered). No `scripts/research.sh` run.
`is_this_a_graph`: No — deterministic subtraction and registry/test
reconciliation; no per-item model call.
**Prior art:**
- [FR-814](FR-814-fr-knowledge-graph-extraction.md) /
  [FR-816](FR-816-knowledge-graph-cluster-display-names.md) /
  [FR-817](FR-817-knowledge-graph-cross-cluster-mentions.md) (CAP-240):
  built the graph, cluster names, cross-cluster mentions, and the
  prior-art hook's cluster boost. This FR retires all of it.
  [FR-815](FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md)
  and [FR-818](FR-818-judge-prior-art-context-narrowing.md) proposed graph
  consumers; neither added a live reader of the artifact (verified by
  `git grep fr-knowledge-graph` — the only runtime reader is
  `prior_art.py`).
- [FR-275](FR-275-test-speed-optimization.md) (CAP-126, REQ-YG-275):
  created the `slow` marker; its acceptance tests are the second
  retirement here.
- FR-1131 test-suite cost concentration (Proposed, draft in worktree
  `docs/fr1131-test-suite-cost`, not on main): the test-cost analysis that found both items. Its Phase C step 5
  (FR-275 meta-tests) is taken out and done here; FR-1131 keeps the rest.
- [FR-1012](FR-1012-chaplain-subtree-archive-and-removal.md) / CAP-264: precedent for a
  retirement witnessed by an absence test and a retired-state capability.
- [FR-938](FR-938-prior-art-retrieval-in-research-route.md): the
  `rare_floor` prior-art retrieval stays unchanged; only the graph boost
  inside it goes.

## Summary

Two things cost test time and witness nothing true:

1. The FR knowledge graph (`scripts/extract_fr_graph.py` →
   `reference/fr-knowledge-graph.yaml`) was last regenerated on 2026-08-18.
   It has 689 nodes, the highest FR-819. About 300 FRs filed since have no
   node, so the prior-art hook's cluster boost silently does nothing for
   every new FR. No hook, CI job or script regenerates it. Its 29 tests
   pass on this stale file.
2. `test_fr275_test_speed_optimization.py` spends ~100 s testing that
   pytest's own `-m` marker selection works, plus one test with body
   `pass` and five source-text greps.

Delete the graph feature end to end. Delete 12 of 13 FR-275 tests; keep the
one that witnesses marker registration.

## Value Statement

For the operator and every agent session: CI test jobs lose ~100 s of
sequential time each, and the prior-art hook stops claiming a graph boost
that has not fired for a month.

## Problem

Measured on main @ 4f55aea3 / eae85eea, 2026-09-27, reference machine
(iMac, 12 xdist workers, Python 3.13.5). Command:
`pytest tests/unit/ -q --no-cov -n auto --junitxml=tmp/unit-junit.xml`,
per-test time summed from the junit `testcase@time` attributes. The
per-test numbers needed here are copied into the tables below; this FR
is the committed record.

**FR knowledge graph.**

| Fact | Evidence |
|---|---|
| Artifact last committed 2026-08-18 | `git log -1 -- reference/fr-knowledge-graph.yaml` → `2f9c00fc` |
| 689 nodes, max FR-819, 1683 edges | `yaml.load` of the committed file |
| Corpus now reaches FR-1128 | `ls feature-requests` |
| No regenerator | `git grep extract_fr_graph` in hooks, workflows, pre-commit: none |
| Only runtime reader | `.github/hooks/scripts/checks/prior_art.py:123-217` (`_load_graph`, `_graph_prior_art`, 1.5× boost, `[graph:cluster]` tag) |
| Boost is a no-op for every FR > FR-819 | `_graph_prior_art` returns `[]` when the new FR id is not a node |
| Docstring claims a staleness diagnostic that does not exist | `prior_art.py:129` "missing/stale graph → diagnostic"; the code checks missing and malformed only |
| Hook parses the file on every FR creation | 0.92 s `yaml.safe_load` of 270 KB |
| `# noqa: BLE001` at `prior_art.py:151` has no entry in `docs/confessions.md` | `grep prior_art.py docs/confessions.md` → only `prior_art_gate.py` rows |
| `test_fr_graph.py` cost | 36.8 s summed over 29 tests; 13 tests re-load the artifact through three function-scoped fixtures (2.3–3.9 s setup each under xdist); `TestDeterminism` extracts the real corpus twice (12.4 s) |

**FR-275 meta-tests** (`tests/unit/test_fr275_test_speed_optimization.py`,
13 tests, 100.6 s summed):

| Tests | What they check | Cost |
|---|---|---|
| `test_fast_test_run_excludes_slow_tests`, `test_slow_test_run_includes_only_slow_tests` | `pytest --collect-only -m …` over all of `tests/unit` succeeds and prints "deselected"/"selected" | 45.8 s + 29.7 s |
| `test_slow_marker_recognized_by_pytest`, `test_marker_selection_syntax_works`, `test_all_tests_still_run_by_default` | `pytest --markers`, `pytest --help` contains `-m MARKEXPR`, collect-only of one file | ~10 s |
| `test_slow_marker_properly_applied` | body is `pass` | 0 |
| `test_map_timeout_tests_have_slow_marker`, `test_race_node_tests_have_slow_marker`, `test_chaos_tools_respects_test_delay_scale`, `test_timeout_tests_use_configurable_delays`, `test_claude_md_has_fast_test_commands`, `test_claude_md_has_slow_only_test_commands` | a string is present in a source or doc file | ~0 |
| `test_slow_marker_defined_in_pyproject` | the `slow` marker is registered in `pyproject.toml` | ~0 — **kept** |

The subprocess tests are all `slow`-marked, so the pre-commit fast loop
does not pay them. CI runs `tests/unit/` sequentially with coverage and
pays all of them (CI `test` job: 366–592 s over the last 10 PR runs;
recent successful PR runs of `workflow.yml`: 36375330726, 36344481514,
36343842154, 36343050621).

**REQ-YG-275 clauses after pruning** (R-4). The requirement text is
narrowed to what the surviving witness proves:

| Clause | Disposition |
|---|---|
| `slow` marker defined in `pyproject.toml` | Kept. Witness: `test_fr275_test_speed_optimization.py::test_slow_marker_defined_in_pyproject` |
| tests sleeping >1 s carry `@pytest.mark.slow` | Dropped from the requirement. The witness was a source grep for the string; the markers themselves stay in `test_map_node_timeout.py` (4) and `test_race_node.py` (1). |
| `-m "not slow"` / `-m "slow"` select correctly; behaviour unchanged without filters | Dropped. This is pytest's behaviour, not yamlgraph's; the pre-commit fast loop runs `-m "not slow"` on every commit. |
| `TEST_DELAY_SCALE` configures chaos/timeout delays | Dropped from the requirement. The code in `tests/chaos_tools.py:33` and `test_map_node_timeout.py:106,154` stays; its witness was a source grep. |
| commands documented in CLAUDE.md | Dropped. Documentation wording, not behaviour. |
| "comprehensive acceptance tests validate marker functionality" | Dropped. |

## Ideal Result

Every test in `tests/unit` witnesses a yamlgraph behaviour that can
regress. No committed artifact is read at runtime unless something keeps
it current. The prior-art hook does exactly what its output claims.

## Proposed Solution

One PR, RED then GREEN.

**RED commit** — add `tests/unit/test_fr1134_retirements.py`
(`@pytest.mark.req("REQ-YG-716")`), failing on the current tree:

- `scripts/extract_fr_graph.py`, `reference/fr-knowledge-graph.yaml`,
  `reference/fr-knowledge-graph.md`, `tests/fixtures/fr_graph_validation.yaml`,
  `tests/unit/test_fr_graph.py`, `capabilities/CAP-240-fr-knowledge-graph.yaml`
  do not exist.
- `.github/hooks/scripts/checks/prior_art.py` source contains none of
  `fr-knowledge-graph`, `_graph_prior_art`, `graph:cluster`, `import yaml`.

The same commit adds `.github/hooks/tests/test_fr1134_prior_art_output.py`,
a characterization witness (R-3): a synthetic corpus of FR ids above
FR-819 in a temp dir, run from the repo root so the current graph still
loads, and the full `build_prior_art` output compared to a string
literal. It passes on the parent tree and must pass unchanged after
GREEN. The FR-275 pruning gets no new witness (C-2): it only deletes
tests and narrows REQ-YG-275.

**GREEN commit** —

1. Delete the six paths above.
2. `prior_art.py`: remove the optional `yaml` import, `GRAPH_PATH`,
   `_load_graph`, `_graph_prior_art`, the boost in `score()` and the
   `[graph:cluster]` tag. The unconfessed `# noqa: BLE001` goes with
   `_load_graph`. The ranking for FRs > FR-819 is unchanged by
   construction (their boost set was already empty).
3. `.github/hooks/tests/test_fr938_rare_floor.py::test_module_runs_without_pyyaml_installed`:
   keep the test (the hook still runs under bare `python3`); drop the
   sentence in its docstring that names the FR-814 graph.
4. `scripts/size_gate.py`: remove the `scripts/extract_fr_graph.py` entry.
5. `test_fr275_test_speed_optimization.py`: delete the 12 tests listed in
   § Problem; keep `test_slow_marker_defined_in_pyproject`.
6. Add `capabilities/CAP-293-fr-knowledge-graph-retired.yaml`
   (REQ-YG-716, module `tests/unit/test_fr1134_retirements.py`), following
   CAP-264. Regenerate `ARCHITECTURE.md` with
   `scripts/aggregate_capabilities.py` (removes the CAP-240 section and
   REQ-YG-601..603).
7. `capabilities/CAP-126-test-speed-optimization.yaml`: narrow the
   description and REQ-YG-275 text per the clause table; drop `CLAUDE.md`
   from its modules.
8. Historical records (FR-814..818 and their judgements, diaries, recaps,
   changelog, `docs/mercury-census/findings.md`) are not edited.

## Acceptance Criteria

- [ ] AC-01: RED commit contains only the new witness test and fails on the
  parent tree; GREEN commit makes it pass.
- [ ] AC-02: the six paths are absent; `git grep -e extract_fr_graph -e fr-knowledge-graph`
  outside `feature-requests/`, `docs/`, `changelog/` returns nothing.
- [ ] AC-03: `test_fr1134_prior_art_output.py` passes on the RED parent
  and after GREEN, unchanged; `.github/hooks/tests/` passes; a
  before/after run of `build_prior_art` over every real FR file above
  FR-819 gives identical output (count recorded here).
- [ ] AC-04: `test_fr275_test_speed_optimization.py` has one test and no
  `subprocess` import; REQ-YG-275 text matches the clause table;
  `python scripts/req_coverage.py --strict` passes (REQ-YG-601..603 gone
  from registry and ARCHITECTURE.md).
- [ ] AC-05: `python scripts/validate_capabilities.py` passes with CAP-293
  present and CAP-240 absent.
- [ ] AC-06: full `tests/unit` run is green in the PR worktree (no failure
  allowance); summed time of the removed tests recorded here.
- [ ] AC-07: CI run ID, head SHA, Python version, conclusion and duration
  of `test (3.11)` and `test (3.14)` on this PR recorded here next to the
  366–592 s baseline.
- [ ] AC-08: a human reviews the `prior_art.py` and hook-test diff before
  merge (GATE, R-6).
- [ ] Changelog fragment (`type: removal`) in `changelog/unreleased/`.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A-1 | Regenerate the graph and add a staleness gate (`extract_fr_graph.py --check` in pre-commit / CI) | Rejected. A regeneration gate on every FR commit adds cost to the busiest path for a 1.5× boost that has not fired in a month with no one noticing — `would_you_use_this` answered by the record. The graph has no reader other than this boost. |
| A-2 | Keep the graph, fix only the test cost (module-scope fixtures, tmp_path determinism) | Rejected. It makes tests of a stale artifact faster. Tests that pass on dead data are the defect (`gate_checks_shape_not_substance`). |
| A-3 | Keep the FR-275 greps (they cost ~0 s) | Rejected. They check that FR-275's acceptance text still sits in files; they pin CLAUDE.md wording and break on edits unrelated to behaviour. Time is not the only cost. |
| A-4 | Replace the kept marker test with `--strict-markers` in `addopts` | Not in this FR. It changes marker handling for the whole suite and every nested pytest run; it needs its own measurement. The kept test is the minimal witness. |
| A-5 | Delete all 13 FR-275 tests | Rejected. REQ-YG-275 would lose its only witness and `req_coverage --strict` would fail. |
| A-6 | Retire the graph in a separate FR from FR-275 | Judge verdict SPLIT; overruled by the operator (2026-09-27, 2026-09-28): one FR, one PR. The two keep separate requirements and witnesses. |

## Related

- `.github/hooks/scripts/checks/prior_art.py`, `.github/hooks/tests/test_fr938_rare_floor.py`
- `capabilities/CAP-240-fr-knowledge-graph.yaml`, `capabilities/CAP-126-test-speed-optimization.yaml`, `capabilities/CAP-264-chaplain-runtime-retired.yaml`
- FR-1131 (test-suite cost), FR-814..818, FR-275, FR-1012
