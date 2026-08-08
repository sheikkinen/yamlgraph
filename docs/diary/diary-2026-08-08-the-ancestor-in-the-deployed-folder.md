# Diary — 2026-08-08 — The Ancestor in the Deployed Folder

**Context:** field inspection of `~/Documents/deviant-working/` — a
hand-rolled DeviantArt publishing automation (Oct 2025 era), examined at
the operator's request the day after FR-779/FR-780 hardened the
research-agent demo.

## What it is

Two shell scripts form the whole system. `loop.sh`: a 30-iteration while
loop feeding a todo-file prompt to `claude -p`, with 5-hour-limit
detection and countdown sleeps — an FSM wearing a while-loop costume.
`claude-deployed.sh`: a 15-second polling watcher on `deployed/` — new
PNG → shrink to 10% for cheap analysis → image-art-analyzer agent →
grep the title out of freeform prose → write `<Title>.md` post
description → rename the PNG → append to a `.processed_files` ledger,
with orphan detection and before/after file-set diffs. The publishing
doctrine lives in `DEVIANTART-JULKAISUOHJE.md`: poetic English title,
3–4 mythic paragraphs, closing epigram, character quote — a prompt spec
written as an instruction for humans, executable by agents.

## Reflection: this is pre-yamlgraph yamlgraph

Every pattern the framework later mechanized exists here informally, and
every trap the Scripture names was paid for here in production:

- **Title extraction by grep from freeform response** — no schema, no
  Pydantic boundary. The `plausible_wrong_answer` surface FR-779 just
  closed in research-agent was wide open here; it mostly worked, which
  is worse than failing.
- **The todo.md troubleshooting section is a proto-diary**: "same file
  gets first renamed and then reprocessed" (idempotence at the rename
  boundary), ".processed_files duplicate entries" (ledger hygiene).
  Boundary lessons, paid for, recorded as checked checkboxes — and
  therefore unsearchable, ungraduatable. Checkboxes are where lessons
  go to be forgotten; the diary format exists precisely because a
  closed todo conveys *that* something was fixed but not *what it
  taught*.
- **The pairing invariant rotted silently**: the script's own orphan
  check (every PNG must have an .md twin) is 100% violated today — 15
  titled PNGs, zero descriptions, newest from Aug 5, last successful
  run 2025-10-30. Same lesson as FR-779's demo rot: an automation that
  stops running doesn't announce itself; its invariants decay invisibly
  until someone looks. A gate that only runs while the watcher runs is
  a gate scoped to the watcher's lifetime, not the artifact's.

## The asymmetry worth naming

The 10%-shrunk temp image for analysis is boundary cost-engineering that
yamlgraph does NOT yet have a primitive for — the old shell script is
*ahead* of the framework on one axis. Reflection cuts both ways: the
ancestor is cruder everywhere except where production pressure forced an
optimization the clean framework never felt.

**Seed:** the `deployed/` folder currently holds 15 orphaned PNGs and a
ready-made prompt doctrine (the julkaisuohje). This is a fully-specified
yamlgraph graph waiting to exist: watch/batch node → vision analysis
with an inline schema (title, description, tags, quote) → shell tools
(rename, write md) → the FR-779-style gate (no description below
confidence threshold — never publish a hallucinated myth). The old
system is the requirements document; its todo.md is the test plan. Does
converting it earn more than reviving it — and is the 10%-shrink trick
the first candidate for a shared vision-tool manifest?
