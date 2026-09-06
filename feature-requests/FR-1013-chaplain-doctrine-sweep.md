# Feature Request: Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

**Priority:** LOW
**Type:** Enhancement (docs; Scripture edit — human gate C-4)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 3 of 5; prerequisite FR-1012 **merged** (FR-1010 C-3)
**First consumer / first event:** a new agent session reading
`.github/copilot-instructions.md` → "Sermon of the Chaplain" → following
`docs/development-process.md § 3 "The Chaplain: Autonomous Plan → Judge →
Enforce"` → `.chaplain/scripts/start-system.sh`, which no longer exists.
The first ENOENT on a doctrine-cited path is the event; today that chain is
three hops long and every hop is live text.
**Research:** [FR-1010 § Alternatives Considered](FR-1010-chaplain-archival-plan.md#alternatives-considered-r-1-six-solution-classes);
the sweep inventory below is the evidence record (line refs read
2026-09-06). `is_this_a_graph`: **no** — a fixed list of documents with
known line numbers; a grep, not a corpus.
**Prior art:**
- [FR-193-mass-graduation-scripture-patterns.md](FR-193-mass-graduation-scripture-patterns.md)
  — the last Scripture-wide edit; established that Scripture edits go
  through judge + human review and never same-session with the observation
  that motivated them (`guard_widening_when_caught` at Scripture scale).
- [FR-207-standalone-scripture-methodology-repo.md](FR-207-standalone-scripture-methodology-repo.md)
  — `ramp/` renders Scripture-derived assets from `_templates/`; the
  `ramp/assets/tier2/.../judge-fr/doctrine.md` copy must be regenerated,
  not hand-edited, or `ramp/curation-diffs.md` drifts.
- [FR-1011-relocate-chaplain-live-parts.md](FR-1011-relocate-chaplain-live-parts.md)
  — already changed the one *path* mention in Scripture (`:163`,
  `.chaplain/inbox/` → `proposals/`). This FR changes *wording*; the
  boundary is deliberate: FR-1011 was a relocation, this is doctrine.
- [FR-1012-chaplain-subtree-archive-and-removal.md](FR-1012-chaplain-subtree-archive-and-removal.md)
  — wrote `docs/archive/chaplain.md`, the single page this sweep may
  point to.

## Summary

Make every doctrine and reference document describe the SDLC that is
actually practised — operator-driven plan → `scripts/judge.sh` → worktree
enforcement → `scripts/review.sh` → human merge — and stop describing the
FSM daemon as the process. One archive pointer replaces the runtime
narrative wherever it appeared as live instruction; historical FRs, diary,
changelog and `docs/memento/` are untouched.

## Value Statement

Doctrine stops sending readers to a directory that no longer exists, and
`docs/development-process.md`'s own § 3.1 ("the manual rite dominates —
83 % of commits are direct") becomes the description rather than the
footnote.

## Problem

Sweep inventory (`grep -ciE chaplain`, 2026-09-06; FR-1011/FR-1012 leave
these untouched by design):

| File | Lines | What is there | Change |
|---|---|---|---|
| `.github/copilot-instructions.md` | 204 | `## Sermon of the Chaplain` heading | rename → `## Sermon` (the seven steps are unchanged); one-line note that the Chaplain was the daemon that once ran this sermon, archived FR-1010 |
| `.github/copilot-instructions.md` | 176 | canonical-sources line names `docs/development-process.md (doctrine, chaplain pipeline, enforcement rings)` | drop "chaplain pipeline" |
| `.github/copilot-instructions.md` | 163 | `diary_graduation_pipeline` seed already says `proposals/` (FR-1011) | verify only |
| `docs/development-process.md` | 121–176 § 3 + mermaid; 177–… § 3.1 | § 3 describes the dual-FSM as the process; § 3.1 says the manual rite dominates | § 3 → "The rite as practised" (operator + author/judge/review scripts + worktree-per-PR), 15 lines; § 3.1 folded in as the measurement; the FSM description reduced to two sentences + archive link; mermaid deleted |
| `reference/onepager-development-process.md` | 31, 45, 138, 154 | inbox path, "or open a GitHub issue with the `chaplain` label", flow step 1, sources line | `proposals/`; drop the issue-label route (importer is gone); flow step 1 → "Write spark → `proposals/`"; sources: drop `docs/context/chaplain-system.md` |
| `reference/audit-index.md` | 65–71 | seven rows: Chaplain Pipeline, Dispatcher FSM, Pipeline FSM, Inquisitor, Philosopher, Author allowlist, ID registry | delete six; Philosopher row → `graphs/philosopher/graph.yaml`; add one row "Chaplain (archived)" → `docs/archive/chaplain.md` |
| `reference/graph-yaml.md` | 610, 1469 | comment "Based on .chaplain/watcher2.sh pattern"; prose "(chaplain …)" example for `path:` vs `module:` | drop the comment; example → `graphs/fr_triage` |
| `examples/README.md` | 57, 74, 171 | philosopher stub row; note "relocated to `.chaplain/graphs/`"; "witnesses live under `.chaplain/demos/`" | delete row (stub gone, FR-1011); note → `graphs/`; witnesses line deleted (demos gone, FR-1012) |
| `CLAUDE.md` | — | `grep -c chaplain` → 0 on main 2026-09-06 | verify only |
| `.github/skills/feature-request/SKILL.md` | description front-matter "submitting a proposal to the chaplain inbox"; § Submitting (already `proposals/` after FR-1011) | description → "submitting a proposal to `proposals/`" |
| `.github/skills/judge-fr/doctrine.md` | 133, 135 | "chaplain-era prompts used APPROVE/AMEND"; "Chaplain runtime (`.chaplain/`) is the historical origin" | keep 133 (true history); 135 → point at `docs/archive/chaplain.md` |
| `ramp/assets/tier2/github/skills/judge-fr/doctrine.md` | 133, 135 | rendered copy of the above | regenerate via `ramp/render.sh`; verify `ramp/curation-diffs.md:42` still true |
| `docs/context/chaplain-system.md` | 53 lines (whole file) | full FSM description | **move** to `docs/archive/chaplain-system.md` (git mv; it is the long-form of the archive note) and link from `docs/archive/chaplain.md` |
| `docs/context/fr-698.md` | 347, 357, 359 | historical FR context naming `.chaplain/lib/watcher/*` | leave (historical record, allowlisted by FR-1011's invariant) |

Allowlist (untouched, by FR-1010 AC-12): `feature-requests/`, `changelog/`,
`docs/diary/`, `docs/memento/`, `docs/archive/`, `docs/ebook/`,
`docs/research-*.md`, `ramp/curation-diffs.md` history lines.

## Ideal Result

`grep -rn '\.chaplain' --include='*.md' . | grep -vE '^\./(feature-requests|changelog|docs/diary|docs/memento|docs/archive|docs/ebook|docs/research-|docs/context/fr-698|tmp|\.venv|build)/'`
→ empty. `grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md`
→ 0. `docs/development-process.md § 3` describes what § 3.1 measured.
`reference/audit-index.md` has one Chaplain row pointing at the archive.
`ramp/render.sh` is a no-op after the sweep (rendered assets match).

## Proposed Solution

One PR, docs-only, judged and **human-reviewed before merge** (Scripture
edit; FR-1010 C-4). Never in the same session that observed the need —
this FR is filed in the planning session; enforcement happens later.

1. `.github/copilot-instructions.md:204` heading; `:176` sources line.
2. `docs/development-process.md § 3` rewritten as above; § 3.1's numbers
   kept verbatim as the evidence line.
3. Reference files per the table.
4. `git mv docs/context/chaplain-system.md docs/archive/chaplain-system.md`;
   link from `docs/archive/chaplain.md`.
5. `ramp/render.sh` → regenerated tier2 assets; `git diff --stat ramp/`
   shows only the judge-fr doctrine copy.
6. Witness `tests/unit/test_fr1013_doctrine_sweep.py`: the grep above
   returns empty; the heading is gone; `docs/archive/chaplain-system.md`
   exists; `reference/audit-index.md` has exactly one row containing
   "Chaplain". Tagged with the REQ that already covers
   `test_knowledge_graph_fr193.py` (Scripture structure witness) —
   verified at RED.
7. Existing doc-witness tests that assert the old strings
   (`test_chaplain_readme_documentation.py`, `test_concurrency_safety_doc.py`,
   `test_fr748_fr_atlas.py`, `test_knowledge_graph_fr193.py`) — FR-1012's
   census will have deleted or kept each; the kept ones are updated here
   for the new wording, listed by name in the PR.
8. Changelog fragment `type: removal`, scope `doctrine` (fragment types in
   use: feat/fix/refactor/removal).

## Acceptance Criteria

- [ ] AC-01: the exclusion-grep in § Ideal Result returns empty.
- [ ] AC-02: `grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md` → 0; the seven Sermon step names are byte-identical before/after (`diff <(grep -oE '^\*\*[A-Z][a-z]+\.\*\*' old) <(… new)` empty).
- [ ] AC-03: `docs/development-process.md` § 3 contains no `stateDiagram`, no `start-system.sh`, and does contain `scripts/author.sh`, `scripts/judge.sh`, `scripts/review.sh`, `scripts/worktree.sh`, and the § 3.1 measurement sentence verbatim.
- [ ] AC-04: `reference/audit-index.md` — exactly one row matches `/Chaplain/` and it links `docs/archive/chaplain.md`.
- [ ] AC-05: `docs/archive/chaplain-system.md` exists (rename score ≥ 90 % via `git diff --name-status -M90% <base>...HEAD`); `docs/context/chaplain-system.md` does not.
- [ ] AC-06: `ramp/render.sh && git status --porcelain ramp/` → empty after commit.
- [ ] AC-07: `pytest tests/unit/test_fr1013_doctrine_sweep.py tests/unit/test_knowledge_graph_fr193.py -q` green; full non-slow suite green.
- [ ] AC-08: Human review recorded in this FR before merge (C-4); the reviewer confirms the Scripture diff is heading + one sources clause only.
- [ ] AC-09: FR-1010 AC-12 and AC-13 ticked with this FR's merge SHA; FR-1010 Status → `Completed`.
- [ ] AC-10: Changelog fragment `changelog/unreleased/fr-1013-doctrine-sweep.md`.

## Purge list

- No new doctrine. No new Knowledge-Graph entry (the diary entry
  `2026-09-06-…-sole-consumer-of-a-dead-file…` may graduate later via its
  own FR; not here).
- No edits under the allowlist.
- No rewrite of `docs/development-process.md` beyond § 3/§ 3.1.

## Alternatives Considered

| Option | Why not |
|---|---|
| Fold into FR-1012 | FR-1012 is a destructive PR; Scripture edits need their own judge + human read (FR-193 precedent; C-4). |
| Delete `docs/context/chaplain-system.md` | It is the only long-form description of a system that ran for six months; the archive repo holds code, this holds the design. Move, don't delete. |
| Keep § 3 and add a "retired" banner | § 3.1 already says the FSM was never the primary path; keeping 55 lines of FSM diagram as the process description is the `working_system_inertia` trap in prose. |
| Rename "Sermon of the Chaplain" to something new | The steps are the sermon; the Chaplain was the reader. `## Sermon` loses nothing. |

## Related

- FR-1010 (plan; this FR completes it), FR-1012 (prerequisite),
  `docs/archive/chaplain.md`

## Judgement (pending)
