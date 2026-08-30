# Judgement: FR-922 Skip and Investigate `test_bare_repo_recap_no_hallucinated_conventions` (283s Single Test)

**Verdict:** APPROVED WITH REVISIONS — the latency problem is real and the skip-plus-investigation sequence is defensible, but authority activates only after the FR resolves the REQ-coverage ambiguity and makes the investigation evidence contract mechanically checkable.

**Prior art:** dispositioned by this judgement.
`FR-798-full-suite-failure-classification-investigation.md` (Enforced) is the
closest neighbour: it established the taxonomy for red full-suite results
(product regression / test isolation defect / provider unavailability /
environment mismatch) and its report `docs/investigations/fr798-full-suite-failures.md`
covers an fr432 fixture isolation bug. It does **not** address per-test LLM
latency, and it never examined the recap graph — FR-922 supplies a new instance
of FR-798's "test isolation defect" class (the `test_race_loser_teardown_live`
thread-count pollution, recorded as an incidental finding) rather than
duplicating its scope. `FR-800-memory-demo-mock-seam-correction.md` and
`FR-801-provider-readiness-preflight.md` matched only on the generic nouns
"repo/skip"; neither touches recap latency or REQ-YG-531. The FR-922 `.md` hit
is the document under judgement, not a competitor.

**Reviewed against:** `feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.md`; cited evidence files `tests/integration/test_recap_demo_integration.py`, `examples/demos/recap/graph.yaml`, `feature-requests/FR-700-timeframe-recap-example.md`, `feature-requests/FR-704-recap-orphans-bypass-model.md`, `feature-requests/FR-923-test-suite-latency-lanes-coverage-core-slow-marks.md`, `capabilities/CAP-195-timeframe-recap-demo.yaml`, `ARCHITECTURE.md`, `scripts/req_coverage.py`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`.

## What is sound

The proposal names a concrete first consumer and event: keyed full-suite runs with `ANTHROPIC_API_KEY` set are paying the cost now (`FR-922` lines 8, 14). The defect is measurable enough to justify immediate mitigation: the target test is reported at 282.98s, 34% of an 826s sequential suite, and 17x the next-slowest integration test (`FR-922` lines 14, 31).

The scope distinguishes the valuable behavior from the cost defect. The test is already a live LLM integration test, marked slow and tagged `REQ-YG-531`, and it compiles and invokes the recap graph once (`tests/integration/test_recap_demo_integration.py` lines 63-76). Its assertions guard against hallucinated FR references and require exact orphan-hash preservation (`tests/integration/test_recap_demo_integration.py` lines 81-91). That maps to the recap requirement that convention-free repositories must not hallucinate findings (`CAP-195-timeframe-recap-demo.yaml` lines 20-30; `ARCHITECTURE.md` line 2496).

The investigation-first classification is aligned with repo doctrine. The Scripture says bugs whose causal-chain test would take more than 15 minutes may split into investigation first and fix second (`.github/copilot-instructions.md` line 112), and operational performance degradation must be traced and recorded in feature requests (`.github/copilot-instructions.md` line 226). FR-922 follows that pattern by making the skip the immediate mitigation and deferring graph/prompt/model changes until a measured causal chain exists (`FR-922` lines 16-18, 62-76).

Prior art is meaningfully dispositioned. FR-700 created the recap graph and live bare-repo test (`FR-700-timeframe-recap-example.md` lines 13-20, 124-130). FR-704 removed model transit for orphan copying and flipped the integration assertion to exact equality (`FR-704-recap-orphans-bypass-model.md` lines 14-16, 40-55, 64-68). Neither prior FR addresses live-call latency; the current graph still has exactly one LLM node plus deterministic tool/python collection/finalization (`examples/demos/recap/graph.yaml` lines 14-54, 101-116).

Strategic classification: this is a contrib/example operational bug and investigation, not a framework primitive. The affected surface is the recap demo test and its measurement record; no new abstraction is warranted.

## Required revisions

### R-1: Replace the REQ-coverage wording with a two-channel coverage record

Amend the FR so it no longer says or implies that `scripts/req_coverage.py` proves live behavioral coverage is suspended. That script statically extracts `@pytest.mark.req(...)` decorators from test AST nodes (`scripts/req_coverage.py` lines 96-145), so adding `@pytest.mark.skip` to a still-tagged test can leave REQ-YG-531 listed even though the live witness no longer runs.

Fold this exact distinction into the FR: "Static REQ marker coverage remains/changes as reported by `python scripts/req_coverage.py --detail`; runtime live-LLM witness execution is suspended as shown by pytest skip output." The skip reason may still state that the live witness is suspended, but not that the static requirement registry necessarily loses coverage.

### R-2: Make the skip verification mechanically checkable without a full keyed suite

Replace the broad acceptance phrase "full keyed suite no longer executes the test" (`FR-922` line 80) with a targeted command witness: `ANTHROPIC_API_KEY=... pytest tests/integration/test_recap_demo_integration.py::TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions -q -rs` must report the test as skipped with an `FR-922` reason. A full-suite timing rerun may be recorded as supporting evidence, but must not be required for the skip itself.

### R-3: Resolve the trace/log evidence ambiguity

The investigation section currently allows "LangSmith trace or `YAMLGRAPH_ROUTE_LOG` + executor logging" while also requiring trace IDs "per Commandment 9" (`FR-922` lines 64-69). Amend this into one mechanical evidence contract: each of the at least three samples must record start/end wall time, LLM call count, model, token counts when available, per-call latency, retry/timeout evidence, and either LangSmith trace IDs or an explicit statement that LangSmith was unavailable plus the exact local log artifact used instead. If trace IDs are unavailable, the FR must not claim Commandment-9 trace compliance; it may record a blocked/degraded observability finding.

### R-4: Fence FR-923 and recap-graph changes out of this FR

Add an explicit out-of-scope sentence: FR-922 does not authorize CI lane splitting, coverage-core changes, pytest default changes, model swaps, prompt edits, recap graph edits, or replacement of the witness test. FR-923 owns suite-lane and coverage-core work (`FR-923-test-suite-latency-lanes-coverage-core-slow-marks.md` lines 14-22, 74-91); FR-922 may only choose a disposition and spawn a follow-up fix/re-tier/replace FR after the investigation.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/integration/test_recap_demo_integration.py::TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions` gains a single `@pytest.mark.skip(...)` reason citing `FR-922` and the suspended live witness. |
| D-2 | `feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.md` records skip verification, REQ coverage detail, investigation samples, causal-chain conclusion, and disposition. |
| D-3 | One investigation log artifact under `tmp/` or `logs/` may be produced for local evidence, but the durable summary and cited identifiers belong in the FR. |
| D-4 | `changelog/unreleased/<FR-922-slug>.md` documents the skipped live recap test and investigation. |

Not authorized: deleting the test; removing or changing `REQ-YG-531`; editing `examples/demos/recap/graph.yaml` or recap prompts; changing provider/model/max-token config; changing CI workflow lanes, branch-protection contexts, pytest defaults, or coverage settings; replacing the live witness with record/replay; broad-skipping the whole recap integration class; altering `scripts/req_coverage.py` to make the skip look covered or uncovered.

## Revised acceptance criteria

- [ ] AC-01: The target test method has exactly one new `@pytest.mark.skip(...)` decorator whose reason includes `FR-922` and states that the live REQ-YG-531 witness is suspended pending latency investigation.
- [ ] AC-02: A targeted pytest run of `tests/integration/test_recap_demo_integration.py::TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions -q -rs` with `ANTHROPIC_API_KEY` present reports the test as skipped and shows the `FR-922` reason.
- [ ] AC-03: `python scripts/req_coverage.py --detail` is run after the skip, and the FR records the exact `REQ-YG-531` status separately from runtime skip status.
- [ ] AC-04: The investigation records at least three timed invocations against the same three-commit bare-repo fixture shape and includes wall time, LLM call count, model, token counts when available, per-call latency, retry/timeout evidence, and graph-runtime overhead for each sample.
- [ ] AC-05: The investigation cites LangSmith trace IDs for each sample, or explicitly records LangSmith unavailability and the exact local log artifact used instead without claiming trace compliance.
- [ ] AC-06: The FR records a reproducibility verdict: stable latency, degraded one-off, or inconclusive, with the three sample values shown.
- [ ] AC-07: The FR records exactly one disposition: spawn fix FR, spawn re-tier FR, spawn replacement-witness FR, or close with documented rationale that the skipped test remains intentionally suspended.
- [ ] AC-08: No recap graph, prompt, provider/model, CI workflow, pytest default, coverage, or `scripts/req_coverage.py` changes are included in this FR.
- [ ] AC-09: A changelog fragment exists under `changelog/unreleased/` and names the skipped live recap test plus the investigation outcome.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into the FR before implementation authority activates. | GATE |
| C-2 | Do not run or invoke any judge skill, judge adapter, judge graph, or `yamlgraph` judgement route while enforcing this judgement. | GATE |
| C-3 | The skip must be test-method scoped only; class-level or module-level recap integration skips are out of scope. | GATE |
| C-4 | If the investigation identifies an apparent fix, do not implement it in FR-922; record the disposition and create/follow a separate FR. | GATE |
| C-5 | If LangSmith tracing is unavailable, record that observability gap honestly instead of substituting success-shaped trace language. | GATE |

Authority granted: after the required revisions are folded in, the enforcer may skip the single live recap bare-repo test, record the static-vs-runtime coverage status, run the bounded latency investigation, and write the disposition; no recap implementation or CI-lane change is authorized by FR-922.
