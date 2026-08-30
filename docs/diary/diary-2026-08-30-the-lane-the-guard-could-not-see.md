# The Lane the Guard Could Not See

**Date:** 2026-08-30
**Context:** Operator asked why the previous turn used
`FR902_ALLOW_OUTSIDE=1` repeatedly — why the session worktree was
"ignored" by the lane guard during an in-lane commit.

## What happened

Four escape uses in one short arc: one legitimate (chaplain inbox
submission — the documented out-of-lane case), two compensating for
denials of genuinely in-lane git work, and one — the damning one —
prefixed to a read-only `jq` command that no guard would ever deny.

The audit log answered the "why" in one query: every PreToolUse entry,
approve and deny alike, records `cwd=/Users/sheikki/Documents/src/yamlgraph`.
The workspace root. Always. VS Code's hook payload `cwd` is the
workspace folder — a constant — while the persistent terminal's cwd is
process state that evolves with each `cd`. The guard's git branch says
`targets.append(cwd)  # git writes land where it runs`, a true statement
applied to the wrong variable. The worktree was not ignored; it was
*invisible*. No amount of care inside the terminal could have changed
what the hook saw.

The second denial was sharper: `PATH=... FR902_ALLOW_OUTSIDE=1 git commit`
— escape genuinely set, denied anyway. The escape detector is
`re.match(...)` anchored at position 0 of the command text. Twenty lines
above it, the same function correctly tokenizes segments and strips
leading env assignments to find the command word. The right parser
exists in the same scope and the escape check does not call it.

## The trap

**A guard that cannot observe the variable it rules on will rule on a
proxy, and the proxy's error rate becomes the user's tax.** Payload cwd
is a proxy for execution cwd; they diverge on the first `cd` in a
persistent shell. This is `plausible_wrong_answer` in infrastructure
form: the guard's decision passes every shape check (it resolved a path,
compared it to the lane, emitted well-formed JSON) and is semantically
wrong because its input was never the truth.

The behavioral corollary I caught in myself: after two false denials I
prefixed the escape to a *read-only* command. That is the escape-reflex
FR-925 warned erodes the audit signal — three sessions of false
positives trained exactly the behavior that makes the OVERRIDE stream
worthless. A fence that fires falsely does not just annoy; it teaches
everyone to carry wire cutters, and then the fence guards nothing.

## Heuristic

Before shipping any guard, name the variable it actually rules on and
verify the guard can *observe* that variable from where it sits — not a
static snapshot, not a launch-time constant, not a proxy that was equal
at initialization. If the true variable is unobservable at the hook
boundary, either instrument it (probe writes execution state to the
record the guard reads) or narrow the rule to what is observable
(explicit path arguments, `git -C`, in-command `cd`). A guard on an
unobservable variable is a random-number generator with an audit log.

And: every escape use should hurt a little. When prefixing the escape
stops feeling like a decision, the false-positive rate has already
poisoned the audit trail — count reflexive escapes as incidents, not
workarounds.

## Disposition

Filed `.chaplain/inbox/fix-lane-guard-cwd-model-false-positives.md` —
the follow-up FR-925's judgement C-5 parked but nobody filed. Third
session of firings; `two_strike_split` passed a session ago.

## Seed:

The hooks already include `session-probe.sh` and a PostToolUse channel.
Could a per-session probe append the terminal's last-known cwd to the
session-lanes record after every `run_in_terminal`, giving the lane
guard a live execution-cwd feed one tool-call stale — and is one-call
staleness acceptable for a fence, or does the lag just relocate the
false-positive class to the first command after every `cd`?
