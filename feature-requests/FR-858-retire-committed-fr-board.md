# Feature Request: Retire the Committed FR Board (docs/fr-board.md)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (revisions folded 2026-08-30)
**Effort:** 0.5 days
**Requested:** 2026-08-22
**First consumer / first event:** every FR commit — the drift hook tax
disappears; `scripts/vscode/now.py` at the next situational check —
reads live state instead of a stale cache.

## Summary

Delete `docs/fr-board.md` and its drift hook; keep `scripts/fr_board.py`
as an on-demand query tool. The committed board is a materialized view
whose only reader is its own generator.

## Value Statement

Every FR commit stops paying the regenerate-and-stage tax for an
artifact nobody reads; plan-state queries switch from stale cache to
live source of truth.

## Problem

The Scripture already convicted this artifact twice:
`who_reads_this_when` cites "fr-board's only reader was its own
generator", and `where_is_the_repo_boundary` records fr-board F7
(embedding another repo's working tree). Current state (2026-08-22):
457 lines, 52 PARSE-FAILURE rows ranked first; the `fr-board-check`
pre-commit hook forces regeneration on every FR-touching commit (fired
on every FR commit in the 08-22 session, including one full
commit-failure loop). The single live consumer, `scripts/vscode/now.py`,
reads the committed file — but the file is a cache of what
`fr_board.py` computes from FR files in milliseconds. Doctrine: the FR
is the source of truth; a committed derived view that lags it is
status noise.

## Ideal Result

Plan state has exactly one form: computed on demand. `python
scripts/fr_board.py` prints the board when a reader actually asks;
`now.py` invokes it (or the parser directly) live; no committed
artifact, no drift hook, no per-commit regeneration. PARSE-FAILURE rows
become actionable output at query time instead of committed noise.

## Proposed Solution

Revised per judgement (R-1 test obligations, R-2 CLI surface, R-4 `now.py`
modes):

1. Delete `docs/fr-board.md`; remove the `fr-board-check` hook from
   `.pre-commit-config.yaml`.
2. `scripts/fr_board.py` becomes **stdout-only** (R-2): the `--out` and
   `--check` flags are removed, there is no default write-to-docs path, and
   no repo-writing mode remains. `collect_rows`, `active_rows`,
   `validate_gates`, `load_gates`, and `render_board` are preserved
   unchanged (C-2 protects FR-740 behaviour).
3. `scripts/vscode/now.py` computes plan state live in **both** modes (R-4):
   `--brief` no longer prints a `docs/fr-board.md` path, and default output
   no longer counts table rows from the committed file. If live computation
   fails it surfaces the failure in the existing script error style — never
   a silent fall back to stale committed state (C-5).
4. Tests (R-1): the drift-lint test is **removed** — it pins the freshness
   ceremony this FR retires — and a new witness proves `fr_board.py` renders
   to stdout and creates/modifies no file. Parser, active-set, gates, DAG,
   render, and missing-project coverage are preserved.
5. Update `session-introspection` SKILL reference (board row → command).
6. Disposition FR-740 (the board's creator): the gates-schema, parser,
   question drafting, active-set scoping, and ephemeral cross-repo stdout
   view all survive as query output; only the committed cache and its
   freshness ceremony retire.

## Acceptance Criteria

Adopted verbatim from the judgement (R-1..R-4 folded). **R-3 narrows the
absence gate to active enforcement references**: historical FRs, diaries,
recaps, and doc provenance may keep mentioning the board, and satisfying a
gate by editing them is forbidden (C-3).

- [ ] AC-01: `docs/fr-board.md` is deleted from tracked files
- [ ] AC-02: `.pre-commit-config.yaml` contains no active `fr-board-check` hook and no active `scripts/fr_board.py --check` entry
- [ ] AC-03: No active CI workflow, hook, runtime script, or skill instruction requires `docs/fr-board.md`; historical FR/diary/doc provenance references are not part of this absence gate
- [ ] AC-04: `python scripts/fr_board.py` prints the own-repo board to stdout, exits 0 when gates are valid, and does not create or modify `docs/fr-board.md`
- [ ] AC-05: `scripts/fr_board.py` no longer exposes active repo-writing or drift-check CLI modes (`--out` / `--check`), while preserving `collect_rows`, `active_rows`, `validate_gates`, `load_gates`, and `render_board` behavior
- [ ] AC-06: `scripts/tests/test_fr_board.py` continues to cover status parsing, parse-failure preservation, companion exclusion, active-set scoping, gates validation, rendered table/DAG output, and missing-project notices
- [ ] AC-07: A test covers the new stdout-only CLI/no-write behavior for `scripts/fr_board.py`
- [ ] AC-08: `scripts/vscode/now.py --brief` reports plan state from live `fr_board` data and does not print a `docs/fr-board.md` path
- [ ] AC-09: Default `scripts/vscode/now.py` output reports plan state from live `fr_board` data and does not count rows by reading `docs/fr-board.md`
- [ ] AC-10: `.github/skills/session-introspection/SKILL.md` routes "What's next?" to the live command/source rather than the committed board file
- [ ] AC-11: FR-740 is dispositioned in FR-858 as superseding the committed cache plus drift gate, while preserving the parser, gates schema, question drafting, active-set scoping, and ephemeral cross-repo stdout view
- [ ] AC-12: One `changelog/unreleased/` removal fragment records the user-visible retirement

## Alternatives Considered

- **Fix the 52 PARSE-FAILURE rows instead**: repairs the cache, not the
  readerlessness; the tax remains.
- **Keep board, drop hook**: an uncommitted-but-stale file is worse
  than none.
- **Supersede with semantic grep (FR-857)**: wrong tool — statuses are
  structured; the mechanical parser answers this; 857 is parked.

**Prior art:** FR-740 (board + gates schema) — partially superseded,
disposition above; FR-765 retirement arc — precedent that deletion via
the FR pipeline is the safest operation in the repo; Scripture
`who_reads_this_when` / F7 — the standing conviction this FR executes.

## Evidence Refresh (2026-08-30, still unjudged)

Filed 2026-08-22; eight days later the cited evidence has **decayed, not
stabilised**, and a third failure mode has appeared that the original
Problem section does not name.

| Metric | At filing (08-22) | Now (08-30) |
|---|---|---|
| `docs/fr-board.md` lines | 457 | **526** |
| PARSE-FAILURE rows | 52 | **62** |
| `fr-board-check` hook | present | present (`.pre-commit-config.yaml:291`) |
| `now.py` reads committed cache | yes | yes (`scripts/vscode/now.py:328,368`) |

### New failure mode: the concurrency tax

The original Problem convicts the board on **readerlessness** and the
**per-commit regeneration tax**. The FR-909/910/915 retirement arc
(2026-08-29/30) surfaced a third, more expensive one: with five sessions
active, `docs/fr-board.md` is a **guaranteed merge-conflict point**.

It conflicted on **every** rebase in that arc — three for three — and every
resolution was byte-identical:

```bash
git checkout --ours docs/fr-board.md && python scripts/fr_board.py && git add docs/fr-board.md
```

A conflict whose resolution is always "discard both sides and re-derive" is
not a conflict; it is a **lock**. Two sessions cannot touch any FR
concurrently without serialising on a cache neither of them reads. This
compounds with parallel-session count, so it gets worse as the chaplain
runtime and manual sessions scale — the opposite direction from the
per-commit tax, which is flat.

Precedent this strengthens: **FR-179** de-tracked `CHANGELOG.md` for exactly
this reason ("eliminates merge conflicts entirely") and the cure held. The
board is the same artifact class with the same cure and an existing,
successful in-repo precedent.

### Sibling candidates (not claimed by this FR)

The same "derived view under version control" class covers
`reference/module-map.md`, `examples/dependency-taxonomy.yaml`, and
`ARCHITECTURE.md`'s capability tables — all regenerated by scripts, all
tracked, all of which drifted or conflicted during the same arc. This FR
retires **only** `docs/fr-board.md`; the others are named here so a future
FR can dispose of them as a class rather than rediscovering them one
conflict at a time.

Witness: `docs/diary/diary-2026-08-30-the-gate-that-asked-me-to-forge-evidence.md`
(`generated_artifact_in_git_is_a_conflict_magnet`) — whose seed independently
re-derived this FR's proposal without knowing it existed, which is itself
evidence that the problem is legible from the symptoms alone.

## Related

- scripts/fr_board.py, scripts/tests/test_fr_board.py
- scripts/vscode/now.py (lines 253–288)
- .github/skills/session-introspection/SKILL.md
- .pre-commit-config.yaml (fr-board-check)

## Judgement (2026-08-30)

**Verdict:** APPROVED WITH REVISIONS — full judgement:
[FR-858-retire-committed-fr-board.judgement.md](FR-858-retire-committed-fr-board.judgement.md)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | "existing parser tests pass unchanged" was ambiguous — the drift-lint test pins the very ceremony being retired | Solution item 4 + AC-06/AC-07: drift test removed, parser/gates/DAG coverage preserved, new stdout/no-write witness added |
| R-2 | CLI surface unspecified; `--out`/`--check`/default write contradict "computed on demand" | Solution item 2 + AC-05: `--out` and `--check` removed, no repo-writing mode remains |
| R-3 | "no references remain" too broad — history necessarily cites the board | AC-03 narrowed to active hook/CI/runtime/skill references; C-3 forbids editing historical artifacts to pass it |
| R-4 | `now.py` live behaviour not mechanically checkable | Solution item 3 + AC-08/AC-09 naming both `--brief` and default modes; C-5 requires explicit failure surfacing |

**Conditions:** C-1–C-5 per judgement — notably C-2 (do not weaken FR-740
parser/render/gates behaviour), C-3 (never satisfy an absence check by
editing historical evidence), C-4 (sibling generated artifacts need their
own FRs), C-5 (`now.py` must fail loudly, never fall back to stale state).

**Scope frozen:** deliverables D-1–D-9 per judgement.

## Implementation Status (2026-08-30)

**Enforced** on branch `feat/fr858-evidence-refresh`. RED witnesses committed
before implementation (`scripts/tests/test_fr858_board_retirement.py`, 6
assertions, all failing).

- D-1: `docs/fr-board.md` untracked (`git rm --cached`) and added to
  `.gitignore` under the FR-179 `CHANGELOG.md` precedent.
- D-2: `fr-board-check` hook removed from `.pre-commit-config.yaml`.
- D-3: `fr_board.py` CLI is stdout-only — `--out` and `--check` removed, the
  default write path deleted, and `check_board()` (the drift-lint function)
  removed with them. `collect_rows`, `active_rows`, `validate_gates`,
  `load_gates`, `render_board` and the `--project` cross-repo stdout view are
  untouched (C-2).
- D-4: the drift test `test_check_passes_on_fresh_board_and_fails_on_drift`
  removed; its docstring pin rewritten to point at the new witness. Parser,
  active-set, gates, DAG, render, and missing-project tests unchanged.
- D-5: `now.py` gained `live_plan_state()`; both `--brief` and default modes
  print `plan state: N active FRs, M gates (live)`. Verified live: 255 active
  FRs, 8 gates.
- D-6: `session-introspection` SKILL routes "What's next?" to
  `python3 scripts/fr_board.py`.
- D-7: this section. D-8: `changelog/unreleased/fr-858-retire-committed-fr-board.md`.

**AC-11 — FR-740 disposition:** superseded *in part*. Retired: the committed
cache and its freshness ceremony (`check_board`, the drift hook, the
`--out`/`--check` CLI). Preserved intact: the parser, active-set scoping,
gates schema and validation, pre-drafted questions, the rendered table/DAG,
and the ephemeral `--project` cross-repo view. FR-740's value was the *view*;
only its materialization retires.

**C-5 verified by construction:** `live_plan_state()` returns
`plan state: unavailable (<ExcType>: <msg>)` on failure rather than falling
back to stale state. This fired for real during enforcement — an early version
passed a `list` where `collect_rows` wanted a `Path`, and the tool printed the
`TypeError` instead of silently degrading. The gate caught my own bug.

**Deviation:** three `S603` confessions (CONF-432/433/434) were required for
the witness test, plus `PLC0415`/`BLE001` (CONF-435/436) in `now.py`. The
subprocess calls are deliberate: AC-04/AC-07 witness the *CLI contract*
(stdout only, writes nothing), which an in-process call cannot exercise.

**Verification:** unit suite 6261 passed / 97 skipped / 1 xfailed; script
suite 15 passed; `noqa_coverage --strict` clean. AC-01, AC-02, AC-03, AC-05,
AC-10, AC-12 pass mechanically; AC-04/AC-06/AC-07/AC-08/AC-09 pass by test.
