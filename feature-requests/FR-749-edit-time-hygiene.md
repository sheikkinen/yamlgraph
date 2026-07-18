# Feature Request: FR-749 Edit-Time Hygiene — format, fix, and CONF re-key as one continuous task

**Priority:** HIGH
**Type:** Enhancement (dev tooling; zero framework code)
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-18
**First consumer / first event:** every interactive enforcement arc;
first event = the next GREEN commit that does NOT bounce on
ruff-format, end-of-file-fixer, or CONF line-number rot.

## Summary

Activate and complete the edit-time hygiene loop so formatting-class
pre-commit bounces cease to exist: flip `POST_EDIT_AUTO_RUFF=1` on,
add a CONF `#LNN` re-keyer to the same pass, and provide a
pre-finalize sweep for files edited outside hooked tools.

## Value Statement

Master agents stop paying ~3-minute hook cycles for defects that a
2-second edit-time fix removes at birth; the census's most frequent
bounce classes (5 of 9) die upstream.

## Problem

Session phase census (docs/research-session-phase-census-2026-07-18.md):
one interactive session spent 201 of 535 terminal commands on git
choreography, with ~10 commit bounce cycles. The bounce log shows the
majority class is mechanical hygiene: 2× ruff-format, 1×
end-of-file-fixer, plus 2 commits bounced in a prior arc by CONF
line-number rot (noqa confessions keyed to `#LNN` anchors that move
when ruff reflows lines above them). Each bounce costs a full
pre-commit cycle (~3 min pytest) and pollutes the session transcript,
pulling compaction earlier.

Two-thirds of the cure already ships, dormant: `python-checks.sh:23-31`
has an opt-in `POST_EDIT_AUTO_RUFF=1` path running `ruff check --fix`
+ `ruff format` per edited file. It is not enabled, and CONF re-keying
does not exist.

**Prior art:** the graduated pre-commit-dry-run heuristic (user
memory, proven 3+ arcs); `POST_EDIT_AUTO_RUFF` seam
(.github/hooks/scripts/checks/python-checks.sh); noqa confessions
contract (docs/confessions.md, CONF-XXX); the census document and its
§7 correction. Disposition: this is the activation + completion of an
existing seam, not new machinery; no rejected FR occupies hygiene
territory.

## Ideal Result

A file is always hook-clean at the moment the agent finishes editing
it. Formatting, autofixable lint, and confession anchors are never
discovered at commit time, because they were never allowed to rot:
the commit gauntlet only ever sees semantic gates (tests, coverage,
doctrine), never mechanical ones.

## Proposed Solution

Minimal path back from the ideal:

1. **Enable `POST_EDIT_AUTO_RUFF=1`** for this workspace (hook env or
   settings seam — wherever the hooks read env from; discover at
   enforce time and record here).
2. **CONF re-keyer** (`scripts/conf_rekey.py`, LLM-free): for each
   `# noqa: <code>  # CONF-XXX` in a changed file, recompute the line
   number and update the corresponding `#LNN` anchor in
   `docs/confessions.md`. Runs (a) inside the POST_EDIT_AUTO_RUFF
   pass after ruff format moves lines, (b) standalone.
3. **Pre-finalize sweep** (`scripts/hygiene_sweep.sh`): ruff format +
   ruff check --fix + conf_rekey over the arc's touched files — for
   edits made outside hooked tools (terminal heredocs, external
   editors). The agent runs it once before the commit dance.

## Acceptance Criteria

- [ ] AC-01 RED: witness reproducing CONF rot — ruff reflow moves a
      noqa line; conf_rekey updates the confession anchor; noqa_coverage
      --strict passes.
- [ ] AC-02: POST_EDIT_AUTO_RUFF active in this workspace, witnessed
      by an audit-log entry (`ruff-autofix-applied`) from a real edit.
- [ ] AC-03: sweep is idempotent (second run = no-op) and touches
      only listed files.
- [ ] AC-04: one real GREEN commit after activation with zero
      hygiene-class bounces, cited here.

## Out of scope (purge list)

- Any change to pre-commit hook configs (the gates stay; only the
  defects die earlier).
- Prose-class fixes (hedging tokens) — semantic, stays with the agent.
- radon/file-size remediation — splitting is design work, not hygiene.

## Alternatives Considered

- Commit-time coordinator handling bounces reactively: rejected by
  the census correction — these classes are cheaper to kill at birth
  than to remediate at the gate.
- Re-keying confessions by content hash instead of line number:
  larger contract change to noqa_coverage; possible later FR if
  line-keying keeps hurting after re-keyer exists.

## Questions for the human (as options, or 'none')

None — activation of an existing seam plus one ~60-line script.

## Triage (generated — claims requiring disposition)

- [pending] canon: would_you_use_this: every interactive enforcement arc; first consumer is next GREEN commit with zero ruff-format, end-of-file-fixer, or CONF line-number rot bounces
- [pending] canon: who_reads_this_when: master agents at edit-time and pre-commit phases; delivery rung is commit gauntlet (pre-commit hooks)
- [pending] canon: does_the_platform_already_do_this: POST_EDIT_AUTO_RUFF seam exists dormant in python-checks.sh:23-31; CONF re-keying does not exist; this is activation + completion of existing machinery, no rejected FR occupies hygiene territory
- [pending] pre-mortem: POST_EDIT_AUTO_RUFF enabled but ruff-format still bounces on commit because env var is read at wrong hook phase or not passed through to child processes
- [pending] pre-mortem: conf_rekey.py runs and updates CONF anchors, but noqa_coverage --strict still fails because anchor update does not match the actual post-reflow line number or confession file format is not parsed correctly
- [pending] pre-mortem: hygiene_sweep.sh runs idempotently on first call but second call re-runs ruff format and creates spurious diffs, breaking the idempotency AC-03
- [pending] pre-mortem: AC-04 witness (GREEN commit with zero hygiene bounces) is never cited because a new bounce class emerges (e.g., CONF anchor rot from concurrent edits or external tool interference)
- [pending] pre-mortem: POST_EDIT_AUTO_RUFF activation is recorded but the audit-log entry ruff-autofix-applied is never generated, failing AC-02 witness requirement
- [pending] value-prop: For master agents, kills 3-minute hook cycles + session transcript pollution from mechanical bounces (ruff-format, end-of-file-fixer, CONF line-number rot), vs commit-time remediation; completable from FR text
