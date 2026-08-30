# The Guard That Denied Its Own Cure

**Date:** 2026-08-30
**Context:** FR-925 fold + enforce — SessionStart lane delivery via
`hookSpecificOutput.additionalContext`.

## What happened

Enforcing the fix for "the lane guard is the only thing that tells you
the lane exists" required escaping the lane guard four times. Every
denial was a false-positive class the FR itself had already catalogued
as out-of-scope follow-up material:

1. `cp` with lane-relative paths → resolved against hook cwd, denied.
2. `$LANE/...` shell-variable paths → unresolvable, root-resolved, denied.
3. `git add`/`git commit` from inside the lane → git writes resolved to
   hook cwd, denied.
4. Bonus: `SKIP=pytest ... && git show | tail` → the pytest-pipe guard
   pattern-matched the *environment variable* `SKIP=pytest` plus an
   unrelated `| tail`, denied.

The work was genuinely in-lane; the guard's path model could not see
that. Each unblock was `FR902_ALLOW_OUTSIDE=1` — the exact escape-reflex
training the FR warns "erodes the audit signal."

## The trap

Recursive enforcement blindness: infrastructure that guards a boundary
is itself exercised hardest by work *on* that boundary. The
false-positive classes were documented in prose (FR-925 Related) but
not condemned by tests, so they fired freely against the very session
fixing the delivery seam. Documentation of a defect is not containment
of a defect — `detection_without_enforcement`, one hop inward.

Denial #4 is a sharper instance: a guard that pattern-matches command
*text* (`pytest` + `| tail`) rather than command *structure* will match
its trigger inside an env-var assignment. `regex_fourth_exclusion`
applies to guards too — the fourth special case in a command-string
regex means the guard needs a parser, not another pattern.

## The heuristic

When enforcing a fix to guard infrastructure, count the escapes you
needed. Each `ALLOW_OUTSIDE` invocation during enforcement is a live
witness of a guard false positive — log-verifiable in audit.jsonl, free
to harvest, and stronger evidence than any synthetic reproduction. The
enforcement session of guard-adjacent work IS the test fixture for the
guard's next FR.

## Seed

The audit log already records every `FR902_ALLOW_OUTSIDE=1` use with
the denied command. Could a scheduled sweep cluster those escapes by
denial reason and auto-draft the false-positive FR when one class
crosses two strikes — turning the escape reflex itself into the
graduation pipeline's input?
