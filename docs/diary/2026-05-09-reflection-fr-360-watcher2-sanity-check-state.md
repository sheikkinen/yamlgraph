# Diary: FR-360 Watcher2 Sanity-Check Reflection

**Date:** 2026-05-09
**FR:** FR-360 Voice-driven GitHub issue intake via incaller
**Author:** watcher2 (post-validate sanity reviewer)

---

## What Happened

FR-360 added a `github_issue_intake` mode to `projects/incaller`, routing confirmed-recap calls through a new `create_issue` Python tool node that shells out to `gh issue create`.
The implementation spans 11 changed files (+789 / -3 lines), all within scope: graph YAML, one new tool node, two readback prompt templates, tests, architecture registration, changelog fragment, and README.

All 7 acceptance criteria (AC-01..AC-07, REQ-YG-333..339) were ticked and verified by 11 passing unit tests in `tests/unit/test_fr360_voice_issue_intake_red.py` in 0.28 s.

---

## Trap

**`working_system_inertia`** — The existing probe-recap confirmation path was a single catch-all edge (`recap_analysis.is_confirmed == True → generate_goodbye`). The temptation is to leave that edge intact and bolt the new path on beside it. Judge AMEND-01 caught that this would route both modes identically on the timeout branch (`recap_count >= 3`), sending intake-mode callers to goodbye silently without any issue-creation attempt — and without a failing test to prove it.

The resolution was correct: **both** the confirmed edge and the timeout edge were made mode-guarded, and a negative assertion (`assert not _has_edge(...)`) was added to the test for the timeout path so the absence of an incorrect edge is also verified.

---

## Root Cause

Underspecified edge conditions in the original FR draft. When a new routing branch is added to an existing conditional graph, every existing edge that uses the same source node must be re-evaluated — not just the new one.
Judge AMEND-01 and AMEND-02 caught both the edge-guard gap and the unnamed readback node issue before implementation began, which is why the final diff is clean.

---

## What Worked

1. **Boundary normalization**: `_normalize_chaplain_opt_in()` centralizes the truthy/falsey mapping with explicit `_TRUTHY`/`_FALSEY` frozensets, raising on ambiguous input rather than silently defaulting. This matches the Scripture's "normalize at the boundary" law.
2. **Explicit failure shape**: `_failure()` always returns `{issue_url: None, issue_number: None, issue_create_error: <msg>}`, ensuring the success and failure state keys are mutually exclusive and both always present in the returned dict. Test AC-05 verified both `FileNotFoundError` and `CalledProcessError` paths independently.
3. **Negative edge assertion**: `assert not _has_edge(graph, "analyze_recap_response", "create_issue", "recap_count >= 3 and mode == ...")` proves the timeout path is correctly blocked, not merely that the success path is present.
4. **All 11 tests pass, zero pre-existing failures**: clean TDD green.

---

## Proportionality Assessment

| Signal | Verdict |
|--------|---------|
| Diff scope vs FR scope | ✅ Proportional — 7 ACs, 7 test functions, one new Python module |
| Test assertions check behavior | ✅ Behavioral (subprocess call shape, state key presence, edge existence) |
| No speculative flags or extensibility | ✅ Single mode guard; no adapters |
| AMEND resolutions present in code | ✅ Both AMEND-01 and AMEND-02 resolved; AMEND-03 registered in ARCHITECTURE.md |

---

## Seed

> When a conditional graph has N existing edges from a shared source node and a new mode branch is introduced, is there a static analysis or linting check that can enumerate *all* source-node edges and flag any that are not yet mode-guarded — before the test is written?

A `graph lint` rule that detects "sibling edges from the same source share a subset condition but differ only on destination" and warns when a new mode guard is added without updating all siblings would catch AMEND-01 class gaps automatically.
