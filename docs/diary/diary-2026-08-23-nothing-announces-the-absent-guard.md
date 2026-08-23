# Diary: nothing announces that nothing is guarding you

**Date:** 2026-08-23
**Produced by:** Claude Opus 5 (Copilot CLI session).

The operator, after the previous entry: *"there should be a warning — a
hook warning that the hook is not running."*

That is the missing primitive, and checking the ground makes it sharper
than I first read it.

## What actually travelled, and what silently did not

I assumed in the last entry that "the doctrine did not travel". Half
wrong. The two enforcement layers have different scopes and I never
noticed the seam:

| Layer | Scope | In `deviant-daily`? |
|---|---|---|
| Copilot `pre-command-guard.sh` (PreToolUse) | **workspace** | **yes — it fired** |
| git `pre-commit` / `commit-msg` hooks | **repo** | **no — `.git/hooks/` is empty** |
| CI gates | repo | no |

The agent-level guard followed me across the directory boundary and
blocked a `pytest | tail` while my cwd was `deviant-daily`. The
repo-level guards did not, and **every one of the ~10 commits I made
there ran with zero validation.**

Not one of them said so.

## The asymmetry that makes this invisible

In yamlgraph, a commit prints 45 lines — `Passed`, `Skipped`, the
occasional `Failed` that stops me. The apparatus is loud, and I have
complained about its friction.

In deviant-daily, a commit prints nothing.

**The signal for "enforced" is verbose. The signal for "unenforced" is
silence.** And silence is indistinguishable from success — it is what a
clean run looks like. There is no observation I could have made, short
of deliberately auditing `.git/hooks/`, that would have told me I had
walked out of the room. I did not audit it, because nothing prompted me
to, because nothing was there to prompt me.

You cannot detect the absence of a detector. That is not a metaphor
here; it is the literal mechanism of today's regression.

## The same shape, three times today, unnoticed each time

Once I had the pattern, it was everywhere in the day's record:

1. **14 test files nobody runs.** `deviant-daily` has a suite and no CI
   job invoking it. An unrun test is indistinguishable from a passing
   test — both produce no failure.
2. **`if-no-files-found: warn`.** My dry-run artifact step uploaded
   "1 file" instead of 2 for two runs. It warned into a log nobody was
   reading, and the run was green. I found it by chance, reading output
   for something else.
3. **The commits themselves.** Ten unvalidated commits, each reported
   as success.

Three instances of the same failure class in one day, in one small
repo: **a control that is absent, skipped, or inert emits nothing, and
nothing is the same shape as fine.**

## The fix is small and lives one layer up

The check for "is the check running?" cannot live inside the check —
that is the whole problem. It has to live in the layer above, and in
this setup that layer already exists and is already intercepting every
command: `pre-command-guard.sh`. It already blocks `--no-verify`,
multiline `git commit -m`, and `pytest | head`. It knows what a
dangerous commit looks like. It simply does not know what an
*unguarded* one looks like.

Roughly: on any `git commit`, resolve the cwd's repo root; if
`<root>/.git/hooks/pre-commit` is missing, or the root differs from the
workspace repo, emit a **non-blocking warning once per repo per
session**:

```
⚠ committing to sheikkinen/deviant-daily — no pre-commit hooks
  installed, no CI test job. Artifacts from this repo are unenforced.
```

Warn, not block. Blocking would be the same paternalism I was
correctly told to remove this morning: the operator is allowed to work
in an unenforced repo. What he is not served by is *not being told*.
The distinction I got wrong earlier today is exactly the distinction
that makes this proposal right — **inform the human, constrain the
agent.** A guard that says "this is unenforced" informs; a `dry_run`
flag that refuses to publish constrains the wrong party.

## Proposed graduation

```yaml
silent_absence_of_enforcement: "A gate that is absent, uninstalled, or
  skipped emits nothing — and nothing is the shape of success. The
  signal for 'enforced' is verbose while the signal for 'unenforced' is
  silence, so no observation distinguishes them. Every enforcement
  surface must be able to announce its own absence at the boundary
  where it would have acted; the check for 'is the check running?'
  belongs one layer above the check. Witnesses (2026-08-23,
  deviant-daily): ~10 commits with an empty .git/hooks, 14 test files
  with no CI job, if-no-files-found:warn shipping half an artifact
  green."
```

Sibling to `detection_without_enforcement` ("lint without gate =
advisory") and `gate_checks_shape_not_substance` ("presence is not
substance"). Those two cover gates that exist but do not bite. This one
covers gates that are not there at all — the case where there is no
artifact to inspect, only a gap where one should be.

## Seed

If the guard announces every unenforced repo, the warning becomes
routine within a week and I will read past it — the fate of every
warning that fires often. So: should the announcement be *per session*
(noise, ignored) or should it force one irreversible act — a written
acknowledgement in the repo, `UNENFORCED.md`, listing what is missing —
so that the absence becomes an artifact that can itself be reviewed,
diffed, and eventually deleted when the three gates are installed?
