# FR-1007 research — where should the one-word vocabulary live?

**Prior art:** [FR-1007-command-book.md](FR-1007-command-book.md) — the FR this record serves; [FR-1007-command-book.judgement.md](FR-1007-command-book.judgement.md) — the judgement whose R-1 required this record. Precedent for the subject matter is dispositioned in the FR's own `**Prior art:**` line.

`is_this_a_graph: No` — a reference table; no model call.

## Question

The manual loop is driven by one-word operator verdicts. The stages are written
(`.github/copilot-instructions.md`, Sermon of the Chaplain: Research · Plan ·
Judge · Enforce · Purge · Submit · Distill); the routes are written (five
`.github/skills/*/doctrine.md`); the *words* and what each one obliges are not.
Where should that contract live, if anywhere?

## Precedent (exact lines)

- `docs/development-process.md` §3.1 — "the operator judges (often with a
  one-word verdict — 'reflect', 'diary', 'commit push')". Names the phenomenon;
  no vocabulary.
- `docs/development-process.md` §2.1 — canonical doctrine files + sole routes
  vs operational `SKILL.md` procedures. The classification the book must reuse.
- `.github/copilot-instructions.md`, Submit step — "First `scripts/outsider.sh
  <pr>` … advisory, never a gate" (outsider before review); Judge step — "the
  SOLE execution route is the YAMLGraph adapter"; Enforce — "Obey the Judgement".
- `.github/skills/review-pr/doctrine.md` — review is advisory; the merge
  decision belongs to a human.
- `reference/release-checklist.md` — release is a *recommended* command
  sequence, not a declared sole route.
- `reference/onepager-development-process.md` — one page on the process; no
  command vocabulary.
- FR-995 §"First consumer" — outsider runs on a fresh PR before `review.sh`.
- Incident, 2026-09-05: PR #597 auto-merged (armed at `pr` time) before its
  own amendments were pushed; two commits landed on an orphaned branch and main
  carried a stale plan for an hour. Diary
  `docs/diary/2026-09-05-reflection-fr-1001-the-expectations-were-about-the-other-model.md`
  ("Also seen").
- Incident, same day: PR #603 (`feat`) had auto-merge armed without
  `scripts/review.sh` having run. Caught by the operator's question "any command
  missing"; review was run afterwards.
- Operator standing correction (calibration memory, FR-765 arc): after any
  composing/wrapping artifact, propose retirement of what it supersedes,
  unprompted.

## Solution classes

| # | Class | For | Against | Disposition |
|---|---|---|---|---|
| 1 | Reference page `reference/command-book.md` | Sits beside the other operational references (`release-checklist.md`, `onepager…`); linkable from PR bodies; no byte ceiling; can be revised without Scripture graduation | One more page to keep in sync with five doctrines | **CHOSEN** |
| 2 | Scripture addition (`.github/copilot-instructions.md`) | Loaded into every session automatically | FR-942 byte ceiling (14 bytes free after PR #595); graduation requires recurrence; `guard_widening_when_caught` — the session that noticed the gap should not edit Scripture | REJECTED for now; propose after use from two sessions |
| 3 | Executable `scripts/rite.sh wt fr judge …` | Mechanical; can refuse out-of-order words | Each word already has its script; the loop's value is the human verdict *between* steps — a driver script removes exactly that; `automation_inherits_doctrine` says it would need every gate re-implemented | REJECTED |
| 4 | Expand `docs/development-process.md` §3.1 | Already the place that names the verdicts | §3.1 is the *why* (measured dominance of the manual loop); a how-to table there would double the section's length and change its genre | REJECTED; link from the book instead |
| 5 | Slash-command prompt files (`.github/prompts/wt.prompt.md` …) | Discoverable in the editor; one file per word | Fifteen files to keep aligned; prompt files are executable instructions, not a contract; the artifact column (what proves it) has no home | REJECTED |
| 6 | Nothing — rely on the Sermon + skills | Zero maintenance | The two 2026-09-05 incidents happened with the Sermon loaded; the gap is at the word level, not the stage level | REJECTED |

## Preserved disagreement

- **Merge authority.** Doctrine: review is advisory and the merge decision is
  human. Practice: the operator pre-authorises — "review, reflect, commit
  reflections, merge"; "pr, dogfood, merge". The judge asked for a decision
  (R-5). Operator, 2026-09-05: *"merge — if given as in the example is
  permission to proceed. agent may abort based on review or fix the
  implementation. anyhow full authorization given."* Recorded in the FR and the
  book; the book therefore states predicates under which the agent aborts.
- **Durable witnesses.** The first draft claimed every word leaves a file whose
  absence proves omission. Not true for `wt` (worktree removed on cleanup) or
  `merge`/`release` (Git/GitHub objects, not files). The book names a witness
  per row and marks it durable or transient (R-6).
- **How many new rules.** First draft said the book adds three orderings. Two
  are existing doctrine (judge before implementation; outsider before review);
  two are new local conventions with incident evidence (auto-merge at `merge`;
  retire after release) (R-4).
