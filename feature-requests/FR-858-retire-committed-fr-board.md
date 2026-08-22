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

## Related

- scripts/fr_board.py, scripts/tests/test_fr_board.py
- scripts/vscode/now.py (lines 253–288)
- .github/skills/session-introspection/SKILL.md
- .pre-commit-config.yaml (fr-board-check)
