# Feature Request: FR-749 Edit-Time Hygiene — format, fix, and CONF re-key as one continuous task

**Priority:** HIGH
**Type:** Enhancement (dev tooling; zero framework code)
**Status:** Judged
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

- [accepted] canon: would_you_use_this: every interactive enforcement arc; first consumer is next GREEN commit with zero ruff-format, end-of-file-fixer, or CONF line-number rot bounces — consumer and event named; AC-04 is its witness.
- [accepted] canon: who_reads_this_when: master agents at edit-time and pre-commit phases; delivery rung is commit gauntlet (pre-commit hooks) — rung/reader/moment named.
- [accepted] canon: does_the_platform_already_do_this: POST_EDIT_AUTO_RUFF seam exists dormant in python-checks.sh:23-31; CONF re-keying does not exist; this is activation + completion of existing machinery, no rejected FR occupies hygiene territory — verified against source in judgement.
- [accepted] pre-mortem: POST_EDIT_AUTO_RUFF enabled but ruff-format still bounces on commit because env var is read at wrong hook phase or not passed through to child processes — real: nothing loads hook env today; F1 puts the delivery mechanism in scope and AC-02 witnesses it.
- [accepted] pre-mortem: conf_rekey.py runs and updates CONF anchors, but noqa_coverage --strict still fails because anchor update does not match the actual post-reflow line number or confession file format is not parsed correctly — AC-01's RED witness exists to kill exactly this.
- [accepted] pre-mortem: hygiene_sweep.sh runs idempotently on first call but second call re-runs ruff format and creates spurious diffs, breaking the idempotency AC-03 — AC-03 asserts second-run no-op mechanically.
- [deferred] pre-mortem: AC-04 witness (GREEN commit with zero hygiene bounces) is never cited because a new bounce class emerges (e.g., CONF anchor rot from concurrent edits or external tool interference) — concurrent-edit rot is bounded by F3 (post-edit path scoped to edited file); residual classes recorded at AC-04, remediated in a follow-up if they recur.
- [accepted] pre-mortem: POST_EDIT_AUTO_RUFF activation is recorded but the audit-log entry ruff-autofix-applied is never generated, failing AC-02 witness requirement — the entry name verified in source; AC-02 requires it from a REAL edit, not a test.
- [accepted] value-prop: For master agents, kills 3-minute hook cycles + session transcript pollution from mechanical bounces (ruff-format, end-of-file-fixer, CONF line-number rot), vs commit-time remediation; completable from FR text — F2 adds the counter-metric (edit-failure delta) so the claimed win is net, not gross.

## Judgement (2026-07-18)

**Verdict: AUTHORITY GRANTED** — scope frozen with the pins below.

Claims verified against source before judging (judge_as_junior_pr):
the seam is real (`python-checks.sh` guards on `POST_EDIT_AUTO_RUFF=1`
and emits the exact `ruff-autofix-applied` audit entry AC-02 cites);
`docs/confessions.md` is `#LNN`-anchored and `noqa_coverage.py`
parses `#L(\d+)` — CONF rot is mechanically real and re-keying is
mechanically well-defined; the census §7 correction exists. No
rejected FR occupies hygiene territory. Prior art dispositioned.

**F1 — The env seam does not exist yet; discovering it IS in scope.**
`POST_EDIT_AUTO_RUFF` is referenced only by the seam itself and its
tests; nothing in `common.sh` or the hook entry points loads env.
"Activation" therefore requires a delivery mechanism. Pin: adding a
minimal env-file source to the hook bootstrap (e.g. source
`.github/hooks/env` if present) is activation machinery and IN scope;
it is not a gate change and does not violate the purge list. AC-02 is
the witness that the mechanism actually reaches a real hook process —
the pre-mortem's "wrong phase / not passed through" is exactly what
AC-02 exists to kill.

**F2 — Auto-format-after-edit can fight the editing agent.** Post-edit
reformatting invalidates the agent's memory of file content, so
subsequent string-replacement edits can miss (stale oldString). This
is the strongest case against the FR and it is not in the FR. Pin:
AC-02/AC-04 evidence must record the edit-failure delta (count of
failed edit-tool calls per arc before/after activation, from the
audit log or transcript). If activation trades commit bounces for
edit bounces at ≥1:1, the verdict at AC-04 is "deactivate + record",
not silent tolerance.

**F3 — conf_rekey writes shared state in a parallel-session repo.**
`docs/confessions.md` is one file shared by 4+ live sessions
(`one_session_one_repo`). Pin: the post-edit path of conf_rekey may
only rewrite anchors whose **File** entry equals the edited file;
whole-file re-keying is reserved for the standalone/sweep invocation.
Idempotency (AC-03) applies to both paths.

**F4 — end-of-file-fixer is not a ruff concern.** The sweep must also
terminate final newlines for non-Python files it is pointed at,
or the FR must drop the end-of-file bounce class from its Value
Statement. Cheapest: sweep adds the trailing-newline fix (a two-line
shell fragment), keeping the claimed 5-of-9 coverage honest.

**F5 — AC-04 is the only gate that matters; the rest are scaffolding.**
One real GREEN commit with zero hygiene-class bounces, cited with its
SHA in this FR. A demo of the re-keyer on a fixture is necessary
(AC-01) but not sufficient — the census was measured on real arcs, so
the cure is witnessed on one.

Triage claims: all dispositioned by F1–F5 (the five pre-mortems map
to F1, AC-01's contract, AC-03's contract, F2/F4, and F1
respectively; canon claims verified above).
