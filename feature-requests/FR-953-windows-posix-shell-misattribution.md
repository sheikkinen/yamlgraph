# Feature Request: The suite mistakes an absent POSIX shell for a failing script

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-09-02
**First consumer / first event:** a Windows contributor runs `pytest tests/unit/` and reads the result — every gate, hook and wrapper test either passes, or skips saying "no POSIX shell", instead of reporting 149 fabricated script failures that name the wrong culprit.
**Research:** in-body dispositioned alternatives table below (FR-889 style). The FR-890 route `scripts/research.sh` could not be run: it is a bash script, and the defect this FR describes is that bash does not work on this host. The tool for planning the fix is disabled by the bug being planned.
**Prior art:**
- [FR-951-declare-utf8-at-text-boundaries.md](FR-951-declare-utf8-at-text-boundaries.md) — the parent, ENFORCED 2026-09-02. Its Out of Scope names "POSIX path and shell assumptions in test fixtures" and defers them here. Same host, same enforcement run, different boundary: FR-951 was a *codec* boundary, this is an *interpreter* boundary.
- [FR-950-windows-safe-bridge-fork-registration.md](FR-950-windows-safe-bridge-fork-registration.md) — removed the import-time `os.register_at_fork` blocker and made the Windows suite runnable at all. This class only became visible because of it. Different mechanism (a POSIX-only API vs an absent interpreter).
- [FR-140-clean-git-env-test-fixture.md](FR-140-clean-git-env-test-fixture.md) — notes that gate tests run "bash scripts with embedded git commands via subprocess". It normalized the *git environment* those scripts see; it never questioned whether the interpreter exists. Adjacent, not overlapping.
- [FR-224-cli-graph-commands-test-coverage.md](FR-224-cli-graph-commands-test-coverage.md) — contains `test_windows_skips_with_warning`, evidence that platform-conditional skipping is an accepted idiom here for a single command. Not a general contract.
- [FR-207-standalone-scripture-methodology-repo.md](FR-207-standalone-scripture-methodology-repo.md) — treats POSIX shell as a deliberate portability floor for `render.sh`. It argues *for* shell; this FR does not dispute that choice, only the tests' silent assumption that the shell is present.
- Retrieval is filename-noun IDF ranked. It finds "bash" in 100+ files as a code-fence language tag, which is noise; the absence of a governing FR is a floor, not proof.

## Summary

149 of the 261 Windows test-failure blocks are one defect:
`subprocess.run(["bash", ...])` resolves to the WSL stub, which exits **1** with
a message on stderr the tests never read. The tests then assert against exit
codes and conclude the *script* failed.

## Value Statement

A Windows contributor's test run reports the defects that exist rather than 149
invented ones, and the log names the missing interpreter instead of blaming the
gate script under test.

## Problem

On this host `bash` resolves to `C:\Windows\system32\bash.exe` — the WSL
launcher, with no distribution installed:

```
$ bash -c "echo hi"
<3>WSL (10 - Relay) ERROR: CreateProcessCommon:818: execvpe(/bin/bash) failed: No such file or directory
exit=1
```

That exit code is the whole problem. It is not 127 ("command not found") and
`subprocess.run` does not raise `FileNotFoundError`, because the executable
*was* found and *did* run. It returns **1** — the most ordinary failure code a
shell script can produce. So this assertion:

```python
assert _run(JUDGE, [], tmp_path, None).returncode == 64
E   assert 1 == 64
```

reads as "`scripts/judge.sh` returned 1 instead of the documented usage exit
64". The truth is that `judge.sh` never executed a single line. This is
`plausible_wrong_answer` at a platform boundary: the value passes every type
and shape check and is semantically wrong, and 181 blocks of the log assert
confidently about scripts that never ran.

### Scale

`pytest tests/unit/ -q --no-cov -m "not slow" -n auto` on 2026-09-02:
`277 failed, 6100 passed, 97 skipped, 18 errors` across 70 modules. Classifying
all 261 failure blocks, extras first and then by explicit shell markers
(`execvpe(/bin/bash)`, `WSL (`, `.sh`, `/bin/sh`, `args=['bash'`):

| Class | Blocks | Disposition |
|---|---:|---|
| Shell launch | 149 | **this FR, D-1/D-2** |
| Windows path separators (`not normalized`, backslash, `WinError`) | 54 | this FR, D-3 |
| Unclassified | 23 | this FR, D-3 — must be classified before scope freezes |
| Absent optional extras | 18 | FR-952 |
| POSIX-only APIs (`signal.alarm`, `SIGALRM`) | 10 | this FR, D-3 |
| Symlinks | 7 | this FR, D-3 |

The 149 is a conservative floor: the marker set is deliberately explicit, and
part of the 23 unclassified blocks are likely shell-launched too.

The heaviest modules are `test_precommit_hooks.py` (26),
`test_fr758_judge_review_wrappers.py` (18),
`test_automated_post_merge_finalization.py` (16), the `test_ci_*_gate` family,
and `test_fr425_phase_b_hook_emit.py` (11) — i.e. the tests that guard the
repository's own enforcement infrastructure. **The gates are the least tested
surface on Windows, and they fail loudly enough to be ignored.**

### The obvious fix does not work

A real POSIX shell *is* installed here — Git for Windows ships
`C:\Program Files\Git\bin\bash.exe` (`uname -s` → `MINGW64_NT-10.0`). Prepending
it to `PATH` and re-running still produced WSL errors inside the subprocess:

```
args=['bash', '-lc', 'source scripts/gate_artifact_semantics.sh ...']
<3>WSL (88 - Relay) ERROR: ... execvpe(/bin/bash) failed
```

So resolution is not simply a `PATH` question, and the causal chain is not yet
proven. Per `investigation_before_fix`, deliverable D-1 below is that proof,
not a fix.

## Ideal Result

Every first-party test that needs a POSIX shell resolves one explicitly, and
fails loudly and correctly when none exists. A run on a host without a shell
reports "skipped: no POSIX shell" for those tests and zero failures; a run on a
host with one exercises the real scripts. No test can ever again attribute an
interpreter's absence to the script it was asked to test — because the
interpreter is resolved at one boundary that refuses to return a usable handle
for a stub.

## Proposed Solution

Normalize at the boundary where the interpreter enters, and split investigation
from fix.

**D-1 — Prove the causal chain.** A committed investigation: why does an
explicit `PATH` prepend not change subprocess resolution, and what does
`CreateProcess` actually select for the bare name `bash`? The output is the
failing test the fix must satisfy, not a patch.

**D-2 — One shell-resolution boundary.** A single helper that returns a shell
path or `None`, used by every test that shells out:

```python
def posix_shell() -> Path | None:
    """Resolve a real POSIX shell, never the WSL stub."""
```

It must *verify*, not guess — run a trivial command and confirm the output — so
a stub that exits 1 can never be mistaken for a shell. Tests consume it through
one fixture that skips with a named reason when it returns `None`.

**D-3 — Classify and disposition the remaining 94.** The 54 path-separator, 10
POSIX-API, 7 symlink and 23 unclassified blocks: each either fixed or skipped
with a platform reason, in a committed table. No silent xfail, and no block
left in the unclassified bucket when scope freezes.

**D-4 — A witness that the misattribution cannot return.** A test that stubs a
launcher returning exit 1 with WSL text on stderr and asserts the boundary
raises rather than reporting a script failure.

Not authorized: rewriting any `.sh` gate in Python; adding a WSL or Git-Bash
installation requirement to CI or contributor docs as *the* fix; a Windows CI
matrix; changes to the scripts under test; work on the optional-extras class
(FR-952).

## Acceptance Criteria

- [ ] AC-01 A committed investigation record explains, with cited commands and outputs, why `bash` resolves to the WSL stub and why a `PATH` prepend did not change it.
- [ ] AC-02 A single resolution boundary returns a verified POSIX shell or `None`; verification executes a command and checks its output, never merely `shutil.which`.
- [ ] AC-03 Every test that shells out consumes that boundary through one fixture; no test invokes the bare name `bash` via `subprocess` directly.
- [ ] AC-04 On a host with no POSIX shell, the shell-dependent tests **skip** with a reason naming the missing interpreter; zero of them fail.
- [ ] AC-05 On a host with Git Bash, the same tests **run** and their pass/fail reflects the scripts, proven by at least one deliberately-broken-script witness.
- [ ] AC-06 A witness proves a stub launcher returning exit 1 with WSL stderr is rejected at the boundary rather than reported as a script failure.
- [ ] AC-07 The 94 non-shell, non-extras blocks are each dispositioned in a committed table: fixed, or skipped with a platform reason. The unclassified bucket is empty. No bare xfail.
- [ ] AC-08 The Windows non-slow unit diagnostic is recorded with its command and counts; failures attributable to shell launch reach **zero**, while aggregate pass/fail remains context.
- [ ] AC-09 RED before GREEN in separate commits; `type: fix` changelog fragment; CAP/REQ allocated; diary entry with a `Seed:`.

## Alternatives Considered

| # | Mechanism | Benefit | Objection | Disposition |
|---|---|---|---|---|
| A1 | Verified shell-resolution boundary + skip fixture | Fixes the misattribution where the interpreter enters; works on hosts with and without a shell; the stub can never masquerade again | Touches ~70 test modules; needs the D-1 investigation first | **Chosen** |
| A2 | `shutil.which("bash")` and skip if absent | Two lines | `which` **finds** the WSL stub — it is a real executable on `PATH`. This is the naive fix that produces exactly today's wrong answer | Rejected: it is the bug |
| A3 | Require Git Bash / WSL on every Windows dev machine | No test changes | An environment the contributor must remember is not a boundary (FR-951's `PYTHONUTF8` argument); and the measured evidence shows a Git Bash on `PATH` did **not** fix resolution | Rejected |
| A4 | Rewrite the `.sh` gates in Python | Kills the dependency at the root; the gates become unit-testable everywhere | Enormous, rewrites reviewed enforcement infrastructure, and `infrastructure_self_exempt` warns against touching the guardrail casually. A separate FR if ever | Rejected here, noted as a long-term direction |
| A5 | `pytest.mark.skipif(sys.platform == "win32")` on the affected modules | One decorator per file, immediate green | Skips on hosts that **do** have Git Bash, permanently blinding Windows CI to gate regressions — trades a false red for a false green | Rejected: the more dangerous error |
| A6 | Assert on stderr content instead of exit code | Small, targeted | Encodes WSL's error text into the tests; brittle, and still runs 181 tests that cannot pass | Rejected: symptom detection without boundary correction |

**Strongest dissent (A5).** 181 failures on a platform with no CI coverage is
arguably not worth ~70 files of churn; skipping the class costs nothing today.
It is rejected because these are the tests guarding the repository's own gates,
and a permanent skip converts an audible false alarm into a silent blind spot —
the same trade `detection_without_enforcement` names as a defect.

**`is_this_a_graph`?** No. Interpreter resolution and test fixtures; no model
call, no fan-out.

## Related

- `tests/unit/test_fr758_judge_review_wrappers.py:90` — `assert 1 == 64`, the clearest instance
- `tests/unit/test_precommit_hooks.py`, `tests/unit/test_ci_diary_gate.py`, `tests/unit/test_fr425_phase_b_hook_emit.py`, `tests/unit/test_automated_post_merge_finalization.py`
- `tests/unit/test_ramp_installer.py` — `ManifestError: source not normalized`, the path-separator half of D-3
- `scripts/judge.sh`, `scripts/review.sh`, `scripts/research.sh`, `.github/hooks/**/*.sh` — the scripts falsely accused
