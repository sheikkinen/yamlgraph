# Feature Request: Judge-Route Adoption Nudge

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-25
**First consumer / first event:** the next interactive "judge NNN" turn in
any session — the moment it starts rendering a verdict without the sole
route's lineage sentinel.

**Prior art:** the sole judge route itself (judge graph via `scripts/judge.sh`,
NC-412/NC-415 lineage; doctrine `.github/skills/judge-fr/doctrine.md`) — this
FR builds no judge, it closes the *adoption* gap FR-884 priced. FR-767
(Enforced) is the mechanism precedent: per-run sentinel + PreToolUse guard
made the authoring route mechanically sole; this FR applies the same
sentinel pattern to judging, advisory-first. The reasoning-pattern sentinel
(`reasoning-pattern-check.sh`, one-shot denial) is the existing delivery
channel. Scripture `two_strike_split` is the doctrinal basis: instruction
text ("never judge in the author's session") has already lost to practice
twice — the level belongs in code.

## Summary

A mechanical, advisory-first nudge that fires when a session produces
judgement-shaped output on an FR file without a `judge.sh` lineage
sentinel, pointing at the sole route — with a re-census acceptance
criterion measured by the FR-884 classifier.

## Value Statement

The operator recovers the single largest priced inefficiency of the census
(~120M premium tokens, 18.5% of the window) by routing judging to the
pinned gpt-5.5 graph that already exists.

## Problem

FR-884 (docs/FR-884-session-task-shapes.md): judge-fr is 18.5% of window
tokens *despite the sole route existing the entire window* — one sampled
session spent ~29/30 turns on serial interactive judging
(docs/FR-884-raw-read-log.md S-R3). This is `builders_never_call` with a
price tag: ~19% of window tokens flowed interactively through shapes that
had a governed instrument. Doctrine text alone did not hold.

## Ideal Result

Interactive judging becomes the exception that requires deliberate
override: a session that begins judging an FR without judge.sh lineage gets
one advisory interruption naming the command; the following 30-day census
(same classifier graph, same window semantics) measures interactive judge
share **< 5%**. Deny-mode exists but stays off unless the census shows no
shift.

## Proposed Solution

1. **Detection (code, not prompt):** PostToolUse check in `fr-checks.sh`
   territory — a write to `feature-requests/*.judgement.md` (or a
   `**Verdict:**` line into an FR) without the judge sentinel armed for
   this run.
2. **Delivery:** arm the existing one-shot reasoning sentinel with an
   advisory pointing at `scripts/judge.sh <fr-path>`; consumed on next tool
   call. Advisory (allow + message), not deny, in phase 1.
3. **Escape hatch:** re-entry guard preserved — an agent launched BY the
   adapter carries the sentinel and is never nudged (csap NC-414 class
   exception already in doctrine).
4. **Measurement:** AC ties to the FR-884 classifier re-run; the nudge is
   judged by the instrument that justified it.

## Acceptance Criteria

- [ ] Hook detects judgement-shaped writes without lineage sentinel; unit
      tests in `.github/hooks/tests/` (fixture writes, no live judging)
- [ ] Advisory fires at most once per session run (one-shot), never blocks
      in phase 1; re-entry (adapter-launched) sessions exempt — witnessed
      by a test
- [ ] Audit trail rows in `.github/hooks/logs/audit.jsonl` for every fire
- [ ] Re-census criterion recorded: interactive judge-fr share < 5% over
      the next 30-day window via the FR-884 classifier; measurement command
      documented in the FR
- [ ] Deny-mode implemented but shipped OFF, flag documented
- [ ] Changelog fragment; diary reflection

## Alternatives Considered

- **More doctrine text** — already lost twice; `two_strike_split` says stop
  rewording.
- **Immediate deny-mode** — punishes before offering the measured advisory
  path; the census provides the escalation evidence if needed.
- **Cheaper interactive judging (model switch)** — leaves the input-closure
  violation (author's-session judging) intact; the route is the point, not
  only the price.

## Related

- FR-884 census + raw-read log (evidence); FR-767 (sentinel mechanism)
- `.github/skills/judge-fr/` (the route being adopted)
- Scripture: `two_strike_split`, `builders_never_call`, `boring_enforcement`
