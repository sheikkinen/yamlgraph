# Feature Request: Retire the Committed FR Board (docs/fr-board.md)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
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

1. Delete `docs/fr-board.md`; remove the `fr-board-check` hook from
   `.pre-commit-config.yaml`.
2. `scripts/fr_board.py` keeps `--check`-free query mode (stdout);
   drop the write-to-docs default.
3. `scripts/vscode/now.py` switches from reading `docs/fr-board.md`
   to invoking the parser live.
4. Update `session-introspection` SKILL reference (board row → command).
5. Disposition FR-740 (the board's creator): the gates-schema and
   pre-drafted-questions machinery in `fr_board.py` survives as query
   output; only the committed cache and its freshness ceremony retire.

## Acceptance Criteria

- [ ] `docs/fr-board.md` deleted; no hook or CI references remain
- [ ] `fr_board.py` runs as pure query (no repo write); existing parser
      tests pass unchanged
- [ ] `now.py` shows plan state via live invocation; session-introspection
      SKILL updated
- [ ] FR-740 dispositioned in this FR (supersede: cache + drift gate;
      keep: parser, gates schema, question drafting)
- [ ] Changelog fragment (removal)

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
