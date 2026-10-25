# Feature Request: FR-1149 The size gate keys its baseline by POSIX paths on Windows

**Priority:** HIGH
**Type:** Bug
**Status:** Approved with revisions (R-1..R-7 folded), in enforcement
**Requested:** 2026-10-25
**First consumer / first event:** the FR-1148 follow-up on the Windows
machine `Huutokauppakone`: its first `.py` commit after the FR-1148 split,
2026-10-25, which the gate refused for eight files it does not own.
**Research:** in-body Alternatives Considered table (FR-889 style); no
`research.sh` run, the defect is one line with a reproduction.
**Prior art:** [FR-889-os-enforced-main-write-lock.md](FR-889-os-enforced-main-write-lock.md)
— widened the gate to `.github/` and `scripts/` and introduced the
shrink-only BASELINE keyed by repository-relative path;
[FR-942-instruction-context-diet.md](FR-942-instruction-context-diet.md)
— added the instruction-byte ceiling to the same script, untouched here.
No rejected FR covers this territory.

## Summary

`scripts/size_gate.py` keys `BASELINE` by POSIX paths
(`.github/hooks/tests/test_main_write_guard.py`) and looks files up by
`str(p.relative_to(root))`, which on Windows is a backslash path. No
baselined file is ever found on Windows, so every held oversize file reports
as an error and the gate exits 1 on any commit that touches a `.py` or `.sh`
file, whatever that commit changes.

## Value Statement

For contributors committing from Windows (the game-engine proof of concept
runs there), who today cannot commit any Python change through the hooks,
versus skipping the gate (forbidden) or committing from a Mac.

## Problem

Reproduction on `Huutokauppakone` (Windows 11, Python 3.13, `origin/main`
at `c1db2321`), `PYTHONUTF8=1 python scripts/size_gate.py`, exit 1:

```text
✗ .github\hooks\tests\test_main_write_guard.py: 549 lines exceeds 450 — split into submodules
✗ .github\hooks\tests\test_pre_command_guard.py: 807 lines exceeds 450 — split into submodules
✗ .github\hooks\tests\test_reasoning_pattern_check.py: 592 lines exceeds 450 — split into submodules
```

and six more lines of the same shape (nine `✗` in all). Eight of the nine
are in `BASELINE` under their forward-slash key, at or above their current
length (`".github/hooks/tests/test_main_write_guard.py": 550`): five under
`scripts/`, three under `.github/hooks/tests/`. The ninth,
`yamlgraph/utils/llm_providers.py` at 473 lines, is a genuine failure on
every OS (FR-1148's owed split), not this defect. The lookup
`BASELINE.get(rel, LIMIT)` misses because `rel` uses `\`, so each falls back
to `LIMIT` (450). On macOS and Linux `rel` already uses `/`, so CI never saw
it.

The `platform` boundary of the Knowledge Graph: the path enters as an OS
path at `relative_to` and is compared as a key without being normalised.

## Ideal Result

The gate gives the same verdict for the same tree on Windows, macOS and
Linux: a baselined file is held at its baseline on every OS, and the
printed path is the same key the baseline uses.

## Planned Operations

```yaml
probes:
  - "PYTHONUTF8=1 python scripts/size_gate.py on Windows at c1db2321 — the reproduction above (done)"
  - "the new test run against the unfixed line — must fail (the witness, see Implementation)"
branches:
  - "another path comparison in the script also uses an OS separator → normalise it in the same change"
delegations:
  - "judge.sh: 1 run (JUDGE_BACKEND=claude)"
waits:
  - "judge"
  - "CI"
  - "operator merge decision"
commands:
  - JUDGE_BACKEND=claude scripts/judge.sh feature-requests/FR-1149-size-gate-windows-paths.md
  - pytest .github/hooks/tests/test_size_gate.py -q --no-cov
  - PYTHONUTF8=1 python scripts/size_gate.py
  - PYTHONUTF8=1 pre-commit run --files <changed files>
```

## Proposed Solution

Normalise at the boundary where the OS path enters: one function that turns a
scanned file into its baseline key, used for both the lookup and the printed
path.

```python
def baseline_key(path: PurePath, root: PurePath) -> str:
    """A file's BASELINE key: its path from the root with forward slashes, on every OS."""
    return path.relative_to(root).as_posix()

# main()
rel = baseline_key(p, root)
```

Constraints: no change to `LIMIT`, `WARN` or the byte ceiling; no change to
output on macOS or Linux; one `BASELINE` entry added, below.

**One temporary BASELINE entry (operator decision [O], 2026-10-25):**
`"yamlgraph/utils/llm_providers.py": 473`. On Windows the fixed gate and the
split of `llm_providers.py` (FR-1148's owed work) block each other: this PR's
commit runs the fixed gate, which still fails on the genuinely oversize
`llm_providers.py`; the split's commit would run the unfixed gate, which fails
on the eight path errors. The operator chose, over a combined commit or a
commit from macOS: "add llm_providers.py at 473 to the size gate's baseline in
the gate-fix PR (shrink-only, recorded in FR-1149); the refactor PR right
after removes the entry." The entry is the file's exact size at `c1db2321`, so
the shrink-only ratchet holds it there; the refactor PR removes it.

## Acceptance Criteria

Revised by judgement ([FR-1149-size-gate-windows-paths.judgement.md](FR-1149-size-gate-windows-paths.judgement.md)):

- [x] AC-01: `baseline_key(PureWindowsPath(r"C:\r\.github\hooks\tests\x.py"), PureWindowsPath(r"C:\r"))` is `".github/hooks/tests/x.py"` and the result contains no `\`. The test runs and passes on every OS; the FR records accurately that against the pre-fix code it fails for a missing function, not for the old `str(...)` line (R-3).
- [x] AC-02: a tree with a baselined file over `LIMIT` but within its baseline length passes `main()` on the running OS. Non-regression only — the FR states that on POSIX this passes against the pre-fix code too, so AC-01 is the cross-OS regression witness (R-4).
- [x] AC-03: `PYTHONUTF8=1 python scripts/size_gate.py` exits 0 on Windows at the fixed commit; the command, exit code, and output (no `✗` lines; `llm_providers.py` held by AC-08's entry) are pasted into the FR's Implementation status (R-7).
- [x] AC-04: `pytest .github/hooks/tests/test_size_gate.py -q --no-cov` passes with every pre-existing test unchanged; the module-level `pytestmark = pytest.mark.req("REQ-YG-631")` covers the new tests (infrastructure scope, excluded from `req_coverage`).
- [x] AC-05: `changelog/unreleased/fr-1149-size-gate-windows-paths.md` exists with front matter `type: fix`, `scope: hooks`, `req: REQ-YG-631`, and `python scripts/check_changelog_req.py` passes (R-7).
- [x] AC-06: a `docs/diary/` reflection with a **Seed:**.
- [ ] AC-07: no `--no-verify`, no skipped hook, no `Co-authored-by` trailer; `PYTHONUTF8=1 pre-commit run --files <changed files>` passes.
- [x] AC-08: `BASELINE` holds exactly one temporary entry, `"yamlgraph/utils/llm_providers.py": 473`, with a comment naming FR-1149 and FR-1148 and stating that FR-1148's split removes it; the number equals the file's current line count, and `test_baseline_is_shrink_only_and_honest` passes on its live clauses — `p.is_file()` and `actual <= allowed` (R-5).
- [x] AC-09: `feature-requests/FR-1148-anthropic-thinking-off.md` names the removal of the FR-1149 temporary `BASELINE` entry in its Follow-up-owed paragraph, and FR-1149 cites FR-1148 AC-08 as that entry's owner (R-6).
- [x] AC-10: the FR's Implementation status records the pre-judgement landing of the code with its commit SHA (R-1) and the verbatim RED-witness output against the pre-fix line (R-2).

## Alternatives Considered

**is_this_a_graph:** no — a one-line key normalisation.

| # | Alternative | Disposition |
|---|---|---|
| A | **`.as_posix()` at the key** (chosen) | The smallest change at the entry boundary; one function for lookup and print |
| B | Store BASELINE keys with `os.sep` | Rejected — the file would differ by OS; a key is data, not an OS path |
| C | Compare with `Path(rel) == Path(key)` | Rejected — normalises at every comparison, downstream of the boundary |
| D | Skip the gate on Windows | Rejected — `infrastructure_self_exempt`; the gate would not hold there at all |

## Related

- `scripts/size_gate.py` — `main()`, the `rel` line
- `.github/hooks/tests/test_size_gate.py` — REQ-YG-631
- FR-1148 follow-up (the first commit this unblocks)

## Judgement fold (2026-10-25)

Round 1, `JUDGE_BACKEND=claude scripts/judge.sh`: APPROVED WITH REVISIONS. Folded:

| # | Revision | Where folded |
|---|---|---|
| R-1 | Record that the code exists before the judgement | Implementation status: written in the working tree before the judgement, uncommitted; the judge read it as committed. Committed after this fold, its SHA recorded below |
| R-2 | A real RED witness, verbatim | Implementation status, `RED witness` |
| R-3 | AC-01 stated accurately; `"\\" not in key` | AC-01; `test_baseline_key_is_posix_for_a_windows_path` |
| R-4 | AC-02 is non-regression on POSIX | AC-02 |
| R-5 | AC-08 cites the live clauses of the honesty test | AC-08; line 123's tautology parked below |
| R-6 | The temporary entry's owner named | AC-09; FR-1148's Follow-up owed paragraph carries the removal sentence |
| R-7 | AC-03 and AC-05 recorded as facts | AC-03, AC-05; Implementation status |

**Parked (not this FR):** `test_baseline_is_shrink_only_and_honest` line 123 asserts
`actual > LIMIT or allowed >= actual`, a tautology after line 122; its repair is separate work.

**The judge's question for the human:** the temporary entry has no mechanical expiry if FR-1148's split slips.
The operator's decision of 2026-10-25 makes that split the PR after this one.

## Implementation status

**R-1, the record:** the fix and its tests were written in the working tree before the judgement and were not
committed; the judge read them as committed. They are committed after this fold (`fix(hooks)` commit, its SHA
in the PR). The `docs(fr)` commit `246f909e` holds the FR only.

**RED witness (R-2),** Windows 11, Python 3.13, the two new tests against `origin/main`'s `scripts/size_gate.py`
(`c1db2321`):

```text
E       AttributeError: module 'size_gate' has no attribute 'baseline_key'
.github\hooks\tests\test_size_gate.py:134: AttributeError
>       assert size_gate.main() == 0
E       AssertionError: assert 1 == 0
.github\hooks\tests\test_size_gate.py:149: AssertionError
FAILED .github/hooks/tests/test_size_gate.py::test_baseline_key_is_posix_for_a_windows_path
FAILED .github/hooks/tests/test_size_gate.py::test_a_baselined_file_is_held_on_this_os
2 failed, 9 deselected in 0.38s
```

AC-01's test fails for the missing function, the weak witness the judgement foresaw; AC-02's test fails on the
defect itself on Windows (the held file is not held, the gate exits 1).

**AC-03,** Windows 11, at the fixed working tree (with the temporary entry):

```text
$ PYTHONUTF8=1 python scripts/size_gate.py
(18 lines of ⚠ warnings for files between 400 and 450 lines; no ✗ line)
exit 0
```

## Addendum 2026-10-25: the scope widened to every hook with the Windows path bug

**Trigger [O]:** the operator, relayed by the producer: "fix paths, skip hooks as seen fit". The judgement above
covered the size gate only; this addendum widens the scope, so it is not covered by that judgement's frozen scope
and is recorded here for the reviewer.

**Why:** running every hook by id on Windows (the config has `fail_fast`) found the same defect in two more hooks:

| Script | The defect | The fix |
|---|---|---|
| `scripts/noqa_coverage.py` | `str(filepath.relative_to(root))` at two sites: every noqa's file is a backslash path on Windows, never the forward-slash path of `docs/confessions.md`, so all 259 noqa read as undocumented, and its `--fix` hook could not realign drift | `rel_key(filepath, root)` with `.as_posix()`, used at both sites |
| `scripts/hedging_check.py` | `_finding_key` builds `f"{filepath}:{lineno}"` from the OS path, so no finding matches its forward-slash ALLOWLIST key on Windows (37 false findings) | `_finding_key` uses `PurePath(filepath).as_posix()` |

**RED witness** for the two (Windows 11, against `origin/main`'s scripts):

```text
E       AttributeError: module 'scripts.noqa_coverage' has no attribute 'rel_key'
tests\unit\test_noqa_coverage.py:246: AttributeError
E       AssertionError: assert 'yamlgraph\\t...\\agent.py:68' == 'yamlgraph/tools/agent.py:68'
E
E         - yamlgraph/tools/agent.py:68
E         ?          ^     ^
E         + yamlgraph\tools\agent.py:68
E         ?          ^     ^
tests\unit\test_hedging_check.py:171: AssertionError
FAILED tests/unit/test_noqa_coverage.py::test_rel_key_is_posix_for_a_windows_path
```

`noqa_coverage`'s is the weak form (the helper did not exist); `hedging_check`'s fails on the defect itself, and
would on POSIX too (a `PureWindowsPath` argument).

**Two consequences, fixed in the same change:**

- `tests/unit/test_hedging_check.py::TestScanFile::test_allowlist_suppresses` built its ALLOWLIST key as
  `f"{py_file}:2"`, the OS path; it passed on Windows only because both sides used backslashes. Its key is now
  `py_file.as_posix()`.
- `docs/confessions.md` had drifted on `main` (six line references in `copilot_runtime_claude.py` and
  `copilot_runtime_opencode.py`). On macOS the `noqa-confession-fix` hook realigns drift before the strict check; on
  Windows it could not (the same path bug). `python scripts/noqa_coverage.py --fix` realigned the six; the strict
  check then passes.

**The tests this change touches,** run on Windows:

```text
$ pytest -q --no-cov tests/unit/test_noqa_coverage.py tests/unit/test_hedging_check.py .github/hooks/tests/test_size_gate.py
...................................                                      [100%]
35 passed in 2.26s
```

**Skipped hooks (the operator's approval, the producer's rules):** the `pytest` hook (the whole unit suite) is
skipped with `SKIP=pytest` on this branch's code commits only: on Windows it fails on 286 tests outside this
change (ramp installer, pre-commit hooks, post-merge, copilot and worktree tests that need bash, WSL or POSIX
paths). Every other hook runs and passes, the fixed size gate, noqa and hedging checks included. CI runs the
full suite on the PR. Each skip is listed with its commit in the PR body.

**Acceptance criteria added:**

- [x] AC-11: `noqa_coverage.rel_key` and `hedging_check._finding_key` give forward-slash keys for a Windows path
  (tests in `test_noqa_coverage.py` and `test_hedging_check.py`, `REQ-YG-063`).
- [x] AC-12: on Windows, `python scripts/noqa_coverage.py --strict` and
  `python scripts/hedging_check.py yamlgraph scripts --strict` exit 0.
- [x] AC-13: every skipped hook is recorded here and in the PR body; CI's full checks pass before merge.

## Addendum 2026-10-25: the acceptance criteria at merge

**R-1's SHA:** the `fix(hooks)` commit is `5fcb1ded`; the diary entry is `98492c8f`.

**CI's first run failed one test,** `test_changelog_req_cross_wiring.py::TestChangelogReqIntegrity::
test_no_req_collision_across_unrelated_frs` (3.14: 1 failed, 7630 passed; 3.11 cancelled):

```text
REQ-YG-083 claimed by FR-1148 (fragment) but FR-1148 capability has no capability
REQ-YG-631 claimed by FR-1149 (fragment) but FR-1149 capability has no capability
```

Each fragment names a requirement whose capability did not list the FR in its `fr` field. `a2a3e459`
(`chore(registry)`) adds FR-1148 to CAP-28 and FR-1149 to CAP-255; the capability-sync hook regenerated the two
lines of `ARCHITECTURE.md`. No requirement text changed. That commit was also made with `SKIP=pytest`, for the
same reason as `5fcb1ded`; the test above passes locally after the change (2 passed).

**Met:** AC-01 to AC-06 and AC-08 to AC-13. On Windows, `noqa_coverage.py --strict` and
`hedging_check.py yamlgraph scripts --strict` exit 0 (AC-12). Every CI check on PR #758 passed at `a2a3e459`
(AC-13).

**Not met as written: AC-07.** Its "no skipped hook" was overtaken by the operator's decision in the first
addendum: the `pytest` hook was skipped on `5fcb1ded`, and AC-13 records that skip. The rest of AC-07 holds: no
`--no-verify`, no `Co-authored-by` trailer, and every other hook passed.
