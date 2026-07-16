# 2026-07-16 — Wrong twice in opposite directions, therefore trusted

**Context:** FR-741/742 enforcement — orphan triage, diary-debt
detection, and the arc's terminal artifact: a posthumous diary paying
a 120-day-old debt. The Distill for the pair.

**The double cross-examination is the story.** The diary-debt verdict
was wrong twice on its first real input, in *opposite* directions:
a false UNWRITTEN (the `…-nc393-…` filename didn't match ref `NC-393`
— hyphens as boundary noise) and a false DELIVERED (a loose `FSM` ref
matched `multi-fsm` filenames from an unrelated arc). Both lies were
caught the same way: **git cross-examined the tool** — the doctrine
the FRs themselves had just bound ("in git we trust") applied to the
instrument's own output. And both cures went in RED-first, so the
calibration is now pinned, not remembered. The metacognitive point:
a verdict that survived adversarial correction from an independent
source deserves *more* trust than a mechanically clean first run —
clean runs leave the failure modes undiscovered. Wrong twice in
opposite directions means the boundary has been probed from both
sides. (`first_unattended_hours_are_the_real_judge` confirmed within
the same day it was named — twice.)

**Substance-over-presence, third strike today.** The naive
any-entry-in-window verdict said LIKELY DELIVERED for all three debts
— vacuous in a repo that diaries daily. Same shape as the altimeter's
phantom witness (a gate against too-few, none against corrupt) and
FR-740's 700-row board (completeness without scoping). Three
occurrences of `gate_checks_shape_not_substance` in one day, each in
a *freshly built* instrument: the trap is not legacy code, it is the
default shape of a first draft. The cure each time was reading the
raw data the gate summarizes.

**The posthumous diary closed a loop with a recursion inside it.**
The FSM planner's recovered insight — its judgement catches lived on
the *failure path* (uninitialized index, fd leak on connect failure)
— is itself an instance of the pattern that recovered it: the todo
store is the failure path of session lifecycles, the place where
plans go when execution dies. Reading failure paths is where the
value was, at both levels. Intentions die; records don't; the
pipeline from frozen intention to paid debt now runs end-to-end:
store → forensics → judged FR → briefing → posthumous payment.

**Process debt, two-strike fired:** confession line-number rot. The
`noqa_coverage` checker keys on exact line numbers; both GREEN
commits today bounced because insertions above the noqa shifted it
(L36→L52→L108). Same guard, same failure class, twice —
`two_strike_split` says the abstraction belongs in code: key
confessions on (file, code) or a content anchor, not a line number
that rots on every edit above it. Filed as the next mechanical
improvement to the confession gate.

**Seed:** the dispositions sidecar now holds verdict-annotated
history (`DELIVERED`, `PAID POSTHUMOUSLY`, `superseded`) — a labeled
dataset of how intentions actually resolve. After a few weeks it
answers a question nobody could ask before: what *fraction* of agent
intentions die, get delivered elsewhere, or rot — the metabolism of
planning itself, measurable per week, per repo, per session type.
