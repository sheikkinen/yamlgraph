# Reflection: FR-1149 — the platform the gate never saw

**Date:** 2026-10-25
**FR:** FR-1149 (the hooks key their files by POSIX paths on Windows)

## What happened

The FR-1148 follow-up was the first `.py` commit made from a Windows machine in a while. The size gate refused it
for eight files the change did not touch. Each was in `BASELINE`, under a forward-slash key, at or above its
length; the gate looked them up with `str(p.relative_to(root))`, a backslash path on Windows, so none was ever
found. The fix was one `.as_posix()`.

The fixed gate then could not commit itself: `llm_providers.py` was genuinely over the limit, and the split that
cures it would run the unfixed gate. The operator chose one temporary, exact-size baseline entry, owned by FR-1148.

Running every hook by id (the config has `fail_fast`, so a single run shows only the first failure) found the same
defect twice more: `noqa_coverage.py` read all 259 documented noqa as undocumented, and `hedging_check.py` raised
37 findings its ALLOWLIST already holds. A fourth consequence hid behind them: on macOS `noqa-confession-fix`
realigns drifted confessions before the strict check, so `main` had six drifted references nobody saw, and on
Windows the fixer had the same bug.

## Root cause

Every one of the three compared a path it had just built from the OS with a key written by hand in POSIX form.
The `platform` boundary of the Knowledge Graph: the path enters at `relative_to` and is compared without being
normalised. CI runs on Linux, where the OS form and the key form coincide, so no check could ever see it.

## Heuristic

**A key written by hand is data, not an OS path: normalise the computed side at the line that computes it, and
test with a `PureWindowsPath` so the test condemns the bug on the OS CI runs.** A test that only exercises the
running OS (`main()` on a tmp tree) passes on POSIX against the broken code; the `PureWindowsPath` argument is what
makes the witness cross-OS.

Second: **`fail_fast` hides the inventory.** When one hook fails for a platform reason, run every hook by id before
deciding; the second and third failure change the decision (here, from "one script" to "one FR for every key").

## Corrective actions

- The three keys normalised (`baseline_key`, `rel_key`, `_finding_key`), each with a test that takes a
  `PureWindowsPath`.
- `test_allowlist_suppresses` built its own key from the OS path; fixed to `as_posix()`.
- The six drifted confessions realigned.
- The pytest hook's 286 Windows-only failures are not fixed here; the skip is recorded in the FR addendum and the
  PR body, and CI runs the full suite.

**Seed:** Should CI run one job on Windows — even only the pre-commit hooks without the unit suite — so a defect
that only the second platform shows is caught by the platform, not by the first contributor who commits from it?
