# Reflection: FR-1134 — the red test CI never runs

**Date:** 2026-09-28
**FR:** FR-1134 (retire FR knowledge graph and FR-275 meta-tests)

## What happened

This FR removes code, so the risk was the hook's output changing without
anyone seeing it. Before the removal I wrote a characterization test. I
also dumped `build_prior_art` for all 243 FR files above FR-819 and
compared the results before and after: byte-identical. That proof cost
one script and one `cmp`. It is stronger than any claim that "the boost
never fired".

Two surprises came up during the rebase and the final run.

1. **The numbers collided.** FR-1129 merged CAP-293 and REQ-YG-716 while
   this branch held them. Renumbering with max+3 headroom went cleanly.
   The fixup that carried the renumber did not: the first fixup failed
   capability validation because the renamed file was staged before its
   `id:` was edited. The second fixup then swept up every staged file.
   The PR is squash-merged, so the history cost nothing.
2. **One hook test failed.** It fails the same way without my change.
   FR-942 (#548) removed `reasoning-pattern-check.sh` from the Hooks
   subsection of the Scripture, and the REQ-YG-063 test still asks for
   it. Neither CI (`workflow.yml` collects `tests/unit/`) nor pre-commit
   runs `.github/hooks/tests`, so the failure has been on
   main since #548 with nobody reporting it.

Earlier in the session I claimed "main is red" from 7 failures in the
main checkout. In a clean worktree, 6 of them passed, and the 7th passed
once `.venv/bin` was first on PATH, as the hook runs it. So the
false-red came from the checkout's environment, not from the code. The
true-red sat in a suite that no gate runs.

## Trap

`unrun_suite_is_unwatched`: a test suite that no gate runs is not a
witness. It is a claim that decays silently. The REQ-YG-063 test was
green when it merged and has been red for the ~190 PRs since #548. Coverage tools
count it as coverage, but nothing runs it, so it enforces nothing.

## Heuristic

Before trusting a suite's colour, ask which gate runs it. For every test
directory, name the CI job or hook that executes it. A directory with no
gate either gets one or loses its `req` claims.

**Seed:** How many REQ IDs are witnessed only by tests in directories CI
never collects? A one-pass census could compare `req_coverage.py` output
against the CI `pytest` paths. Each REQ with no CI-run witness is a
phantom claim.
