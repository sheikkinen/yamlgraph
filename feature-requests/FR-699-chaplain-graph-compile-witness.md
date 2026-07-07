# FR-699: Chaplain Graph Compilation Witness Tests

**Status:** ENFORCED
**Created:** 2026-07-07
**Origin:** Inquisitor Audit 258 — ✗ VIOLATION: commit `1ed5b8b6` (chaplain graph tool-path
fix) merged without a condemning test (Commandment 7). This FR retrofits the witness and
condemns the entire defect class.

## Problem

The path-doubling defect (FR-445 graph-root confinement × FR-658 `graph_root` plumbing ×
repo-root-relative `path:` declarations in chaplain graph YAML) killed every enforce session
at launch — and no test could have caught it, because **no test compiles the chaplain graphs**.
The `.chaplain/graphs/*.yaml` configs are production infrastructure executed only at pipeline
runtime; loader-semantics changes arm landmines in them silently (this one sat armed for 4 days).

The fix `1ed5b8b6` was verified by ad-hoc compilation, not by a test: a hypothesis, not a proof.

## Objective

Any framework change that breaks the compilability of a chaplain graph — or the resolvability
of its declared tools — must fail `pytest tests/unit/` at pre-commit, not an enforce session
at 11:29 on a Tuesday.

## Approach

One new test module `tests/unit/test_chaplain_graph_compile.py`:

1. **Compile witness (the condemning test for the class):** parametrized over every
   `.chaplain/graphs/**/*.yaml` graph config — `load_graph_config()` + `compile_graph()`
   must succeed. This test FAILS on the pre-fix tree (verified: see Evidence) because
   `build_python_tool` raises `FileNotFoundError` on the doubled path at compile time.
2. **Proxy wiring witness:** the `write_diary` proxy in `.chaplain/graphs/philosopher/tools.py`
   resolves `.chaplain/lib/diary.py` (file exists at `parents[2]/lib/diary.py`) and the target
   module exposes a callable `write_diary`. No execution of diary side effects — wiring only,
   because wiring is what broke.

No production code changes. No new fixtures beyond repo-relative paths (tests run from repo
root like the existing suite).

## Non-goals

- Executing chaplain graphs or copilot nodes in tests (runtime behavior is out of scope)
- Testing `_resolve_python_tool_path` semantics (already covered by CAP-75 / REQ-YG-196 tests)
- Linting chaplain prompts

## Acceptance Criteria

- AC-01: A parametrized test compiles every graph YAML under `.chaplain/graphs/` (currently 8:
  enforce/validate/sanity, plan/judge, diary, forensic, philosopher); all pass on current main.
- AC-02: The compile witness fails on the pre-fix tree (`b17a8b5e`) — demonstrated in a
  disposable worktree, evidence recorded below.
- AC-03: Proxy wiring test asserts lib path existence + callable `write_diary` on the loaded
  target module.
- AC-04: All tests tagged `@pytest.mark.req("REQ-YG-529")`; REQ-YG-529 added to CAP-75;
  `req_coverage --strict` passes.

## Traceability

- CAP-75 (Portable Chaplain) gains REQ-YG-529: "All chaplain graph configs compile and their
  declared python tools resolve at load time; verified by unit witness tests."

## Judgement (2026-07-07)

**APPROVE with two amendments, applied:**
1. *Scope trim:* original draft included an execution test for `write_diary` with monkeypatched
   state — rejected as over-engineering; the defect was wiring, not behavior; wiring-only
   assertion suffices (`assert_path_not_destination` does not apply — there is no path here,
   only a link).
2. *RED verifiability:* since the fix is already merged, the condemning property must be
   demonstrated against the pre-fix tree, not merely claimed. AC-02 added: run the new test in
   a worktree at `b17a8b5e` and record the failure. Without this, the witness is decorative.
3. *Premise check (Red Hat):* is the pain real? Yes — 4-day armed landmine, one full pipeline
   run lost, diagnosed manually. Detector-originated (Audit 258) but premise independently
   validated by today's incident. Frozen.

## Evidence (Enforce)

- RED (pre-fix tree): recorded in `tmp/fr699-red.log` — compile witness fails at `b17a8b5e`
  with `FileNotFoundError: Python tool path not found: .../watcher-enforce/.chaplain/graphs/...`
- GREEN (main): all witness tests pass; `req_coverage --strict` passes.
