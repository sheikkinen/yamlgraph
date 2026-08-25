# Feature Request: Judge-Route Adoption Nudge

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged (APPROVED WITH REVISIONS 2026-08-25, R-1..R-5 folded)
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

1. **Detection (code, not prompt — R-3 mechanical rules):** a dedicated
   PostToolUse check (in `fr-checks.sh` or a sibling script wired into the
   hook runner) fires ONLY on: (a) writes creating/updating
   `feature-requests/*.judgement.md`, or (b) writes adding a
   verdict-taxonomy line (`**Verdict:** APPROVED | APPROVED WITH
   REVISIONS | REJECTED | SPLIT`) to a feature-request file. Explicit
   exclusions: ordinary FR prose, cited prior judgements, template text,
   and `tmp/*.md` drafts.
2. **Lineage sentinel (R-1 — judge.sh amendment authorized):** the current
   `JUDGE_EXECUTION=1` env is child-process-only and invisible to hooks;
   `scripts/judge.sh` is amended to write a per-run sentinel file
   (`.github/hooks/state/judge-sentinel` pattern per FR-767: token +
   fr-path + timestamp, created at launch, validated by token match and
   freshness, cleaned at exit). Tests: matching token exempts; missing,
   stale, or mismatched token does not; adapter-launched re-entry carries
   the sentinel and is never nudged.
3. **Delivery (R-2 — advisory channel, NOT the deny-path):** the existing
   reasoning-pattern sentinel DENIES its next tool call, so it is not
   reused; phase 1 emits either immediate PostToolUse feedback or a new
   one-shot advisory sentinel that returns allow + message. Phase 1 never
   denies. At most one advisory per unsentineled judgement write.
4. **Measurement (R-4 — follow-up, not an implementation gate):** the
   30-day re-census is a documented follow-up. Exact command:
   `yamlgraph graph run examples/demos/session-shapes/graph.yaml --var
   input_file=tmp/fr884-skeletons.jsonl` over a fresh skeleton corpus
   (`scripts/vscode/fr884_skeletons.py`, window = last 30 days), output
   `tmp/fr884-classified.json`; the metric is judge-fr token-weighted
   share (target < 5%), computed as in `docs/FR-884-session-task-shapes.md`.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: Unsentineled writes creating/updating
      `feature-requests/*.judgement.md` trigger exactly one advisory naming
      `scripts/judge.sh <fr-path>`
- [ ] AC-02: Unsentineled verdict-taxonomy additions to
      `feature-requests/*.md` trigger exactly one advisory; FR prose, cited
      judgement text, templates, and `tmp/*.md` drafts do not
- [ ] AC-03: judge.sh-launched executions carry a hook-visible lineage
      sentinel and are exempt; missing/stale/mismatched sentinel does not
      exempt
- [ ] AC-04: Phase 1 never denies; one advisory per unsentineled judgement
      write, no repeats within the session absent a new trigger
- [ ] AC-05: Every fire writes an audit row (hook, session id, FR path,
      decision, reason)
- [ ] AC-06: Deny-mode behind a documented flag, default OFF; both modes
      tested
- [ ] AC-07: Hook tests cover detection, false positives, lineage
      exemption, one-shot behavior, audit, deny-default
- [ ] AC-08: FR records the exact re-census command, window semantics, and
      artifact path for the <5% follow-up measurement
- [ ] AC-09: Changelog fragment; diary reflection

**Enforcement gates (judgement):** phase-1 advisory only (deny needs a new
scope); no chat-transcript reading — detection inputs are the tool event,
path, content, sentinel, repo files; hook/sentinel diffs require human
review (PR + sole review route per operator decision); no existing guard
weakened.

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
