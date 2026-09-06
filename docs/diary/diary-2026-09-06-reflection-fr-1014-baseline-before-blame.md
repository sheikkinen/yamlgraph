# Baseline Before Blame

**Date:** 2026-09-06
**FR:** FR-1014 dir-aware authoring guard for `graphs/` (Phase 0 of FR-1010)
**Session:** Claude Code on the Windows host; enforced from the plan merged in PR #611, not the FR author's judge session

## What happened

The change itself was four regex lines. Two arms added to the guard's
`governed_path()`, the same two `^`-anchored in `check_authoring_proof.py`,
the same two in the pre-commit selector. RED failed exactly where the FR
said it would — twelve cells, four dir-style rows across three surfaces —
and GREEN turned them. That part took twenty minutes.

Everything else was reading instruments.

The full unit suite came back with 267 failures and 18 errors on the
branch. The doctrine forbids the phrase "pre-existing failure" for a good
reason: the phrase is usually a way of not looking. So I looked in the
cheapest way I could think of — I ran the identical command on the
untouched `main` checkout and `comm`-diffed the two lists of failing test
ids. 284 ids on each side, one id only on mine. That one was real: the
changelog fragment claimed REQ-YG-423 for FR-1014 while CAP-158's `fr:`
field still said FR-446 alone. Fixed in GREEN, one line. The other 284 were
tests that call WSL or exec a bash script and belong to the host, not to
the change.

Then the confession gate. `noqa_coverage.py --strict` reported 231
undocumented suppressions after I had documented mine. On `main` it
reports 230 undocumented — every single `# noqa` in the tree. A gate whose
failure rate is 100% on the untouched tree is not a verdict on my
confession; it is a broken instrument (backslash paths versus
forward-slash links). I wrote CONF-461 in the documented form and left the
gate to CI, where it can read.

Then the hook tests. `.github/hooks/tests/test_authoring_guard.py` cannot
run here: it execs the bash hook directly and Windows answers WinError 193.
The witness I owed was the hook's behaviour, not pytest's exit code, so I
piped the same JSON payloads through `bash pre-command-guard.sh` and
recorded twelve decisions in the FR. The pytest form is CI's.

## The trap

**Reading the instrument as the verdict.** Three times the same shape: a
red number appears, and the reflex is to treat the number as a fact about
the change. The doctrine's `pre-existing failure` prohibition is right to
forbid the excuse — but the cure is not to own 284 WSL failures. The cure
is a control: run the same instrument on the unchanged tree first. If the
output is identical, you are reading the instrument. If it differs by one
line, that line is yours and you now know exactly which.

The `changelog_first_diagnostic` cure already says "enumerate changes
since last known good before reproduction." This is its sibling for gates:
**baseline before blame** — before attributing a gate's failure to the
change, run the gate against the pre-change tree and diff the outputs. It
costs one extra run and turns a wall of red into a single addressable
line. It also exposes broken instruments (the 100% failure rate) that no
amount of staring at the change would reveal.

## The second, quieter trap

The FR named two surfaces. FR-1011's judge found the third — the
pre-commit `files:` selector — and the plan folded it in. Had it not, the
predicate fix would have been unreachable for dir-style-only commits: a
correct patch on two copies of a contract that lives in three places.
`partial_remediation` is in the Scripture as "fix all occurrences, not
just cited one"; what the selector taught is that you must first *count*
the occurrences, and the count comes from grepping for the contract's
shape (the regex text), not for its name. The truth-table test now asserts
the three copies agree. That is a tripwire, not a cure: a fourth copy
would pass every existing test.

## Heuristic

Before blaming a change for a red gate, run the same gate on the unchanged
tree and diff. Identical output means the instrument, not the change, is
speaking. Then check the instrument's failure rate: 100% on a clean tree
means it cannot read this host at all, and the honest move is to write the
artifact in the documented form and name who owns the verdict.

**Seed:** the agreement test guards three copies of one predicate. At what
copy count does an agreement test stop being enough and the predicate
deserve a single source the other surfaces are generated from — and is
that count already reached when the fourth copy sits in `ramp/assets/`,
where the same guard is curated for other repositories?
