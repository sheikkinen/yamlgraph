# 2026-07-24 — The reviewer's first act was to reject its own adoption PR

**Context:** FR-758 enforcement — post-fact CAP-211/REQ-YG-569/test
reconstruction for the csap-ported judge/review wrappers. The judged
scope was executed almost mechanically: CAP yaml, `ARCHITECTURE.md`
regen, 18 stubbed contract tests, changelog fragment, two real smokes.

**The generated-file discovery that halved R-1.** The judgement's R-1
demanded `ARCHITECTURE.md` rows the FR hadn't authorized. Before
hand-writing them I greped for the section markers and found
`<!-- BEGIN GENERATED CAPABILITIES -->` — the whole capability section
is regenerated from `capabilities/*.yaml` by
`scripts/aggregate_capabilities.py`. What the judge priced as a
deliverable was one registry file plus one script run. Heuristic
(recurring, second sighting after fr-board): *before authoring any
row in a large doc, check whether the doc is generated* — the marker
comment is a one-grep test. Hand-editing a generated section is the
inverse failure: it survives until the next regen silently deletes it.

**Stub-boundary test design.** The wrapper contract is pure shell:
exit taxonomy, lock protocol, sentinel, artifact grammar. All 18 tests
run against a stub `YAMLGRAPH_BIN` in an isolated `JUDGE_WORKDIR` — no
API keys, no graph execution, 3.4s total. One trap dodged during
authoring: the hermetic exit-69 test with a *fully empty* `PATH`
would not have tested executor resolution at all — with no `mkdir` or
`find` on PATH the wrapper fails earlier, in the lock branch, exiting
73. A hermetic test still needs the subject's own dependencies
(`PATH=/usr/bin:/bin`). Sub-case of `assert_path_not_destination`:
the wrong exit code arrived via the wrong path, and only tracing the
script line-by-line under the test's environment revealed it.

**The smoke that rejected itself.** No open PRs existed, so the
review smoke ran against merged PR #461 — the adoption of the
review-pr bundle itself. The sole route returned exit 0, artifact
contract satisfied, and verdict **Not approved**: PR #461's diff is
bundle adoption, while the governing FR-758 authorizes traceability
reconstruction and explicitly excludes those changes. The reviewer's
first real act in this repository was to correctly reject the PR that
installed it, on frozen-scope grounds. This is better smoke evidence
than an approval: a rubber stamp exercises the happy path; a reasoned
rejection proves diff retrieval, judgement loading, scope comparison,
and the line-one verdict contract all composed. Heuristic: *when
choosing a smoke input, prefer one where the correct answer is
refusal* — a system that can say no for the right reason has
demonstrated more of its contract than one that said yes.

**Boring enforcement, as doctrine predicts.** Two commits-worth of
work, zero surprises beyond the ruff-format re-stage cycle. The
surprises were all spent earlier — in the judge run that found the
PermissionRequest bug. `boring_enforcement`: the Judgement was good.

**Seed:** the review smoke needed a *mismatched* FR↔PR pair to be
maximally informative, and found one by accident. Should the wrapper
test suite gain one marked-slow, opt-in real-execution test that runs
`review.sh` against a known-mismatched historical pair and asserts the
verdict is a rejection — a permanent negative-control for the sole
route, the way assays carry a blank?
