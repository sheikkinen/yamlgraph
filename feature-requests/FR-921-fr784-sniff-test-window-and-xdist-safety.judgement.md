# Judgement: FR-921 FR-784 Network-Sniff Tests - Full-Window Exhaustion and xdist Unsafety
**Verdict:** APPROVED WITH REVISIONS - the defect is real and testable, but authority activates only after the FR corrects its identity, restores the missing Ideal Result, and reconciles its fast-loop claim with the already-slow FR-784 browser witnesses.

**Reviewed against:** `feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md`; cited prior art `feature-requests/FR-784-playwright-network-sniff-utility.md`; `feature-requests/FR-275-test-speed-optimization.md`; `capabilities/CAP-126-test-speed-optimization.yaml`; cited dependent FR `feature-requests/FR-923-test-suite-latency-lanes-coverage-core-slow-marks.md`; cited implementation/test evidence `examples/api-discovery/tools/network-sniff.js`; `tests/unit/test_fr784_network_sniff.py`; `tests/fixtures/fr784_spa/spa_server.py`; repo doctrine `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `pyproject.toml`.

**Prior art:** dispositioned by this judgement — `FR-921-...md` is the FR under
judgement, not a competitor. `FR-923` (suite latency umbrella) is the dependent
consumer and is scope-separated by C-5: no CI lane changes under FR-921.
`FR-293-pytest-xdist-parallel-tests.md` introduced `-n auto` as an opt-in mode
and owns the xdist convention FR-921 must satisfy; it does not address per-test
settle latency, so FR-921 extends rather than duplicates it. `FR-073-fast-unit-tests.md`
(Implemented) and `FR-275-unit-test-runtime-quick-wins.md` established the
`-m "not slow"` fast loop — both are precedent for R-2's correction (the FR-784
witnesses are already excluded from that loop) and neither claims the sniffer
latency territory.

## What is sound

The problem is concrete enough to judge. FR-921 names six exact tests, their sequential durations, and their `-n auto` failure mode (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:22-31`), and it separates the suspected timing defect from the xdist symptom while explicitly warning not to assume one cures the other (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:33-45`). The cited code makes the timing hypothesis plausible: `_sniff` passes `--timeout 15000` by default (`tests/unit/test_fr784_network_sniff.py:141-147`), and `network-sniff.js` creates one shared deadline, waits for `page.goto(..., waitUntil: "networkidle")`, then races pending response reads against the remaining deadline (`examples/api-discovery/tools/network-sniff.js:133-167`).

The FR preserves the original FR-784 semantics instead of deleting coverage. FR-784 froze a JSON output contract, classification/redaction rules, dependency contract, and deterministic local fixture witness (`feature-requests/FR-784-playwright-network-sniff-utility.md:42-127`), with acceptance coverage for the same browser-observed behaviors (`feature-requests/FR-784-playwright-network-sniff-utility.md:132-142`). FR-921's alternatives correctly reject deleting the tests, shrinking the timeout as a substitute for settle detection, and using `xdist_group` as the only fix (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:70-77`).

The proposed enforcement shape follows project correction doctrine: write a failing witness first, then fix the boundary, then re-run under xdist (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:51-60`). That aligns with the repo's TDD rule that bug fixes require a condemning test before the fix (`.github/copilot-instructions.md:222`).

Strategic classification: test-infrastructure bug fix for an existing contrib/example tool, not a new framework primitive. It touches the FR-784 Playwright utility and its tests; no new graph, prompt, CI lane, or framework abstraction is justified.

## Required revisions

### R-1: Correct the FR identity and restore the Ideal Result

Change the H1 from `FR-784` to `FR-921` and make FR-784 appear only as prior art/dependency. The filename and user target are FR-921, but the document title currently says `# Feature Request: FR-784...` (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:1`). Add an `## Ideal Result` section between `## Problem` and `## Proposed Solution`; the repo template requires it and says the proposed solution must read as the minimal path back from that ideal (`feature-requests/TEMPLATE.md:49-55`; `.github/copilot-instructions.md:233`).

### R-2: Remove the false fast-loop claim from this FR

Rewrite the first-consumer, value statement, and acceptance criteria so this FR targets the FR-784 test file and full-suite `-n auto` safety, not the documented `-m "not slow"` fast loop. FR-921 currently says the documented fast loop pays the 77s cost and must be reduced by >=60s (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:8`, `feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:18`, `feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:67`), but the cited long browser witnesses are already marked `@pytest.mark.slow` (`tests/unit/test_fr784_network_sniff.py:259-337`). The marker registry defines `slow` as tests taking more than one second (`pyproject.toml:217-221`), and FR-275/CAP-126 established `pytest -m "not slow"` as the fast iteration convention (`feature-requests/FR-275-test-speed-optimization.md:73-82`; `capabilities/CAP-126-test-speed-optimization.yaml:17-18`). FR-923 also treats FR-921 as prerequisite for full-suite `-n auto`, not as proof that slow FR-784 browser tests are presently in the not-slow lane (`feature-requests/FR-923-test-suite-latency-lanes-coverage-core-slow-marks.md:21`, `feature-requests/FR-923-test-suite-latency-lanes-coverage-core-slow-marks.md:37-38`, `feature-requests/FR-923-test-suite-latency-lanes-coverage-core-slow-marks.md:88`).

### R-3: Pin the implementation surface to the actual utility path

Replace `scripts/**/network-sniff.js` with `examples/api-discovery/tools/network-sniff.js`, and keep `_sniff` changes limited to test instrumentation unless the failing test proves the Python helper is the defect. The actual test constant points at `examples/api-discovery/tools/network-sniff.js` (`tests/unit/test_fr784_network_sniff.py:20-22`), while the FR currently authorizes a glob that does not name the real surface (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:55-57`).

### R-4: Strengthen the in-body research record with reproducible measurement details

Keep the in-body table, but add the exact commands used, browser setup state, Python/Node/Playwright versions or enough environment detail to reproduce the numbers, and one representative xdist assertion excerpt. Local judge doctrine allows an equivalent committed in-body alternatives table, but it requires substance rather than shape: genuine solution classes, precedent lines, disagreement preserved, and an `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:118-128`). Add the explicit answer: "No: this is a deterministic test/tool bug fix, not a graph-shaped LLM workflow." The existing table and alternatives are useful, but the six xdist failures are currently summarized without an assertion witness (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:22-31`, `feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:41-45`, `feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:70-77`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised FR text in `feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md` folding R-1 through R-4 before enforcement authority activates. |
| D-2 | A failing latency regression witness in `tests/unit/test_fr784_network_sniff.py` proving a trivial settling fixture page does not consume the full timeout. |
| D-3 | The minimal settle/early-exit repair in `examples/api-discovery/tools/network-sniff.js`. |
| D-4 | Minimal test-only timing/helper adjustments in `tests/unit/test_fr784_network_sniff.py` if needed to measure the regression honestly. |
| D-5 | Implementation status, measurements, and any xdist isolation decision recorded back into FR-921. |
| D-6 | Changelog fragment in `changelog/unreleased/`. |

Not authorized: changing FR-784's output JSON shape, weakening redaction/auth/CAPTCHA/classification assertions, deleting the browser witnesses, replacing the fix with a shorter fixed timeout, broad CI lane changes owned by FR-923, changing branch protection or required checks, changing judge/review doctrine or hooks, adding or modifying graphs/prompts, changing the SPA fixture semantics except for a narrowly documented test-fixture bug, or removing `@pytest.mark.slow` from the FR-784 browser tests under this FR unless the revised FR explicitly proves those tests now satisfy the existing slow-marker contract.

## Revised acceptance criteria

- [ ] AC-01: FR-921 title, Ideal Result, and research/evidence record are revised per R-1 through R-4 before code enforcement begins.
- [ ] AC-02: A new `@pytest.mark.req("REQ-YG-590")` regression test in `tests/unit/test_fr784_network_sniff.py` fails before the fix by asserting a settled local fixture sniff using the normal 15000ms ceiling completes in under 5s while still returning valid FR-784 JSON.
- [ ] AC-03: `pytest tests/unit/test_fr784_network_sniff.py -q --no-cov` completes in under 15s total with the committed Playwright/Chromium setup installed.
- [ ] AC-04: `pytest tests/unit/test_fr784_network_sniff.py -q --no-cov -n auto` passes with zero FR-784 failures across three consecutive runs.
- [ ] AC-05: The timeout witness remains bounded: the hanging fixture path still exits 0, emits valid JSON, and includes a timeout warning when invoked with `timeout_ms=4000`.
- [ ] AC-06: No FR-784 semantic regression: data capture, telemetry demotion, token redaction, auth-wall detection, CAPTCHA detection, missing-Playwright diagnostics, and manifest expansion tests still pass or skip only for the existing named browser-setup reason.
- [ ] AC-07: FR-921's implementation record includes before/after wall times for `pytest tests/unit/test_fr784_network_sniff.py -q --no-cov` and the three `-n auto` runs; if `xdist_group("fr784")` is added, the record cites the post-early-exit failure evidence that made isolation necessary.
- [ ] AC-08: A changelog fragment exists in `changelog/unreleased/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 through R-4 are folded into FR-921; the doctrine grants APPROVED WITH REVISIONS authority only after revisions are folded (`.github/skills/judge-fr/doctrine.md:70-72`). | GATE |
| C-2 | The timeout must remain a ceiling, not become a smaller floor: do not satisfy the latency criterion by shrinking the default window without fixing early exit (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:35-40`, `feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:75`). | GATE |
| C-3 | xdist serialization is permitted only after the early-exit fix is applied and a repeated `-n auto` failure is recorded; isolation alone is not an acceptable implementation (`feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:58-60`, `feature-requests/FR-921-fr784-sniff-test-window-and-xdist-safety.md:76`). | GATE |
| C-4 | Do not claim a `pytest -m "not slow"` fast-loop improvement unless the revised FR also explicitly authorizes and proves a slow-marker contract change; current evidence shows the affected browser witnesses are slow-marked (`tests/unit/test_fr784_network_sniff.py:259-337`; `pyproject.toml:217-221`). | GATE |
| C-5 | Any CI, branch-protection, hook, judge, or review-doctrine change is out of scope and requires separate human-reviewed authority; enforcement-infrastructure changes are adversarial input under judge doctrine (`.github/skills/judge-fr/doctrine.md:98-103`). | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, the enforcer may implement only the FR-784 network-sniff early-exit and xdist-safety repair, its direct tests, the FR implementation record, and the changelog fragment described above.
