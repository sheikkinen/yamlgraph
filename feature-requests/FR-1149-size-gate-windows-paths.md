# Feature Request: FR-1149 The size gate keys its baseline by POSIX paths on Windows

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
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

- [ ] AC-01: `baseline_key(PureWindowsPath(r"C:\r\.github\hooks\tests\x.py"), PureWindowsPath(r"C:\r"))`
  is `".github/hooks/tests/x.py"` (a test that fails on the old `str(...)` line on every OS).
- [ ] AC-02: a tree with a baselined file under its baseline length and over `LIMIT` passes `main()` on the
  running OS.
- [ ] AC-03: on Windows, `PYTHONUTF8=1 python scripts/size_gate.py` exits 0 at the fixed commit: the eight
  false errors are gone and `llm_providers.py` is held by its temporary entry (AC-08).
- [ ] AC-04: the existing `.github/hooks/tests/test_size_gate.py` tests pass unchanged; every new test carries
  `REQ-YG-631`.
- [ ] AC-05: `changelog/unreleased/fr-1149-size-gate-windows-paths.md` (`type: fix`, `scope: hooks`).
- [ ] AC-06: a diary reflection with a **Seed:**.
- [ ] AC-07: no `--no-verify`, no skipped hook, no `Co-authored-by` trailer.
- [ ] AC-08: `BASELINE` holds `"yamlgraph/utils/llm_providers.py": 473` with a comment naming FR-1149 and FR-1148
  and saying the next PR (the FR-1148 split) removes it; `test_baseline_is_shrink_only_and_honest` passes.

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

## Implementation status

Filled at enforcement.
