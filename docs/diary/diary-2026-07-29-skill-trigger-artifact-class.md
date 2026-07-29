# Diary 2026-07-29 — The Skill That Didn't Fire: Artifact Class vs Task Phrasing

## Context

Same session as FR-766 enforcement. Operator said "mv hello-runpod to
same folder as hello". I copied the hello demo, adapted graph.yaml
(provider, temperature), rewrote the README, linted, smoked, committed
with a demo-output.log witness. Then the operator said: reflect on the
graph-authoring skill — instructions to have it as the only way.

## Trap: skills trigger on task phrasing, not artifact class

The graph-authoring skill (FR-765, created days ago, doctrine +
adapter + sole-route language already in copilot-instructions) did not
fire. Not because I weighed it and declined — it never entered
deliberation. The request was phrased as a *file move*, so my task
classifier filed it under "shell operation", even though the outcome
was a brand-new committed demo: new graph.yaml, new provider binding,
new README, new demo-output.log. Every element of the doctrine's
artifact boundary.

The near-miss that proves the point: my first graph.yaml draft put
`provider: runpod` at top level, where it silently has no effect — the
demo ran green *on deepseek*. Only `yamlgraph graph lint` (W016)
caught that the run was a lie. I ran lint out of habit, not because a
doctrine told me to. Habit is not a gate. A session without the habit
ships a demo whose witness log proves the wrong provider works.

This is `instruction_boundary_uncrossed`'s benign cousin: the
instruction existed, was loaded in context, and still didn't bind,
because its trigger description ("asked to create a new graph") and
the request's surface form ("mv") didn't intersect. Routing by verb is
routing by costume.

## Cure applied: bind on the artifact, not the verb

Amended three surfaces so the trigger is the artifact class:

- `copilot-instructions.md` — graph-authoring doctrine is "the ONLY
  way to author graphs"; any task creating or materially modifying
  `graph.yaml`/`prompts/*.yaml` IS graph authoring, however phrased
  (mv, copy, adapt, tweak).
- `SKILL.md` description — added the phrasing-independent trigger so
  skill discovery matches on outcome, with the 2026-07-29 witness.
- `doctrine.md` — new "Trigger boundary" section: a copy of a
  committed graph is a new artifact entering at precedent-search (the
  copy IS the precedent); lint + smoke remain mandatory.

The retrospective comfort: the work I did *happened* to satisfy the
doctrine (precedent copy, lint, smoke, honest witness, README-audit
gate). The doctrine's value is precisely that the next session doesn't
need my habits.

## Heuristic

When writing any skill/instruction trigger, enumerate the *artifact
classes it governs*, not the verbs users might say. Users compress:
"mv" meant "productize that tmp demo". The artifact reveals the task;
the phrasing conceals it. (Candidate for Scripture if it recurs: the
judge-fr and review-pr sole-route clauses already bind on execution
route, but their triggers also enumerate phrasings — same exposure.)

**Seed:** could a PostToolUse hook close this mechanically — detect a
create/edit touching `**/graph.yaml` or `**/prompts/*.yaml` in a
session that never read `graph-authoring/doctrine.md`, and warn once?
The gate would bind on the artifact write itself, immune to phrasing.
