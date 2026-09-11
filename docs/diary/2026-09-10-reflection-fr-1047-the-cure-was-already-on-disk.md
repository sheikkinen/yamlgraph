# Reflection FR-1047 — The Cure Was Already On Disk

**Date:** 2026-09-10
**Trigger:** operator: "check dirty main"
**Arc:** incident → misdiagnosis → recovery → FR-1047 → judged → enforced

## What happened

Main showed one untracked file. I traced it to a sibling worktree, called it a
`one_session_one_repo` leak, and proposed deleting it. Then my own
`git pull --ff-only` re-created the full 13-path version of the same dirt,
which presented as an active parallel writer.

Both readings were wrong. It was `partial_pull_against_lock`: a pull that
writes the unlocked paths and dies `Permission denied` on the FR-889-locked
roots, leaving already-merged content wearing the costume of local changes.

The correction did not come from thinking harder. It came from
`docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md` — an entry written
seven days earlier, by a session that hit the same failure, named the trap, and
recorded the exact recovery sequence I then executed verbatim. The knowledge
was on disk, in this repository, before the incident started.

## The trap

`recorded_but_unrouted`: a cure can be written down, correct, and still not in
force. The diary entry and the `/memories/repo/hook-lessons.md` FR-889 section
were both accurate and both unreachable from "check dirty main". Three words
of operator prompt did not resolve to the artifact that answers them, so the
diagnosis was re-derived from zero — and the second derivation was worse than
the first, because this time I got as far as proposing a deletion.

This is distinct from `audit_as_ritual` (a process that runs but does nothing).
Here nothing ran at all. The artifact was inert because no path led to it. The
Scripture already says *precedent lives in three places — search ALL before
designing*; the gap is that a diary entry is a fourth place, and nothing
searches it at incident time.

Note also which diagnostic I reached for first. I asked *where did this file
come from* (origin-tracing: which worktree, which session, which branch) when
the decidable question was *do these exact bytes exist in origin/main*. The
first question is archaeology and has no reliable answer. The second is one
`git show | diff` and settles it. `first_person_tool_horizon` again: I ran an
expensive human judgement instead of the cheap mechanical one.

## The cure

FR-1047: `scripts/dirty_main_triage.py` plus a `clean-dirty-main` skill, and —
the part that actually closes the trap — one line in
`.github/copilot-instructions.md` routing the literal phrase to the skill. The
classifier is the cheap question mechanised; the route is what makes it fire
without someone remembering it exists.

The judge caught three defects that are all the same defect. I wrote
`git clean -fd` unscoped into the recovery recipe of a document whose purpose
is preventing bad discards. I wrote "structurally impossible" about a read-only
tool that cannot stop a later git command. I wrote acceptance criteria that
checked whether the skill *mentions* the cause letters — `gate_checks_shape_not_substance`,
committed in an FR written the same hour I read that entry. Knowing a trap by
name does not prevent firing it; only a gate does, and here the gate was
another agent reading the artifact cold.

One correction from the judge is worth keeping separately: I claimed four
witnessed causes, but only one has a committed witness in this repo. The other
three rest on operator-memory notes outside the input closure. Uncommitted
memory reads as evidence to the agent holding it and as nothing at all to
anyone else — the `private_language` trap, wearing a provenance costume.

## Heuristic

**A cure is not in force until a phrase routes to it.** When an incident's
recovery is re-derived from scratch and the recipe turns out to have already
existed, the defect is not the misdiagnosis — it is the missing route. Fix the
route, not the reasoning. Ask: what did the operator actually type, and does
that string reach the artifact?

Corollary for diagnostics: prefer the question with a mechanical answer.
*Where did this come from* is archaeology; *do these bytes exist in the
target* is a lookup. Reach for the lookup first.

**Seed:** The diary is where cures go to be correct and unreachable. FR-1047
routed one phrase to one skill by hand. What would it take to invert that —
for a diary entry that names a trap to *register* its trigger phrases, so the
knowledge graph is built from incidents rather than curated after them? The
corpus is finite and enumerable, which is the corpus-map-reduce signal: every
entry under `docs/diary/` already carries a **Trap** and a **Trigger**. What
stops the census from emitting the routing table?
