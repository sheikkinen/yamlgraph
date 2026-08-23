# Feature Request: Spike-End Detector — Warn When an Unenforced Repo Goes Live

**Priority:** MEDIUM
**Type:** Feature
**Status:** Draft — awaiting judgement
**Effort:** 0.25 day
**Requested:** 2026-08-23
**Parent:** none — deliberately excluded from FR-864's family (parent
judgement R-6 / C-5: enforcement-infrastructure changes require their
own judgement). Filed now because the ramp family's measure of success
("the next repo to go live gets its gates the same week") is
unreachable without detection — deferral-until-needed is the exact
failure mode `docs/plan-ramp-spike-to-governed.md` documents.
**First consumer / first event:** the operator, at the next spike's
transition to production. First event: an agent commits a workflow
containing `schedule:` into a repo with an empty `.git/hooks/`, and the
PreToolUse guard prints a warning naming `scripts/ramp.sh` — instead of
nothing, which is what deviant-daily got on 2026-08-19.

**Prior art:** **FR-864** named this detector, excluded it, and its
judgement made the exclusion a GATE (C-5) pending a separate
enforcement-infrastructure FR — this is that FR. **FR-865…FR-868** are
non-overlapping: they build and apply the ramp; this FR only detects the
moment the ramp is for.
`docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md` and
`diary-2026-08-23-nothing-announces-the-absent-guard.md` are the
evidence record: the transition is written in a commit with a timestamp,
and absent enforcement is silent. No REJECTED prior art occupies this
territory.

## Summary

Extend the Copilot PreToolUse guard (`pre-command-guard.sh`) with two
**warn-only** checks scoped to git-commit commands running in a foreign
cwd (outside this repo): (1) the commit's repo has an empty or missing
`.git/hooks/pre-commit` — the unenforced-repo warning; (2) staged
content introduces `schedule:` or `secrets.` into `.github/workflows/`
— the spike-end signal. Both print one line naming the condition and
`scripts/ramp.sh`; neither ever blocks.

## Value Statement

The transition from spike to production stops being silent: the agent
that commits the cron is the same agent that is told, at that moment,
that the repo has no gates and a ramp exists.

## Problem

deviant-daily crossed into production on 2026-08-19 (`71e80b9`,
`eeca704`) and nothing noticed for four days: ~10 commits ran against an
empty `.git/hooks/`, zero CI, and the operator learned of the transition
from four production failures in two hours. Both facts — the cron
entering a workflow, and the hooks directory being empty — were
mechanically visible to the guard that was already running in the
session. It was not looking.

## Ideal Result

Every guard-mediated commit into an unenforced repo carries one warning
line; every commit that introduces a schedule or secret into an
unenforced repo carries a second, louder one. The human decides; the
agent is constrained only by having been told (`warn, never block:
inform the human, constrain the agent` — the plan's frozen wording).
The next deviant-daily is offered its ramp at commit time, not four
days and four incidents later.

## Proposed Solution

- Detection lives in `pre-command-guard.sh` (or a check script it
  sources), keyed on `git commit` commands whose cwd resolves to a repo
  other than this one.
- **Check 1 — unenforced repo:** `.git/hooks/pre-commit` missing or
  empty → warn: `⚠ this repo has no pre-commit hooks — scripts/ramp.sh
  <repo> --tier 1 exists`.
- **Check 2 — spike ending:** staged diff (`git diff --cached`) adds
  `schedule:` or `secrets.` under `.github/workflows/` → warn: `⚠ this
  commit takes an unenforced repo live`. Fires only when Check 1 also
  fires — a repo with gates going live is not a finding.
- Filesystem inspection only, mirroring FR-865 R-5: no mutating git
  command against the foreign repo; `git diff --cached` is read-only.
- Exit code is never affected: **warn-only, permanently** — not
  warn-then-block-later. A blocking version would be a new FR.
- One-line suppression: a repo can opt out via a marker file
  (e.g. `.ramp-declined`), so a deliberate Tier-0 spike is not nagged
  on every commit; the marker's presence is itself greppable.

## Acceptance Criteria

- [ ] AC-01: Committing in a foreign repo with empty `.git/hooks/`
      prints the unenforced-repo warning and exits with the guard's
      normal allow decision; test via fixture scratch repo.
- [ ] AC-02: A staged workflow diff adding `schedule:` or `secrets.` in
      an unenforced fixture repo prints the spike-end warning; the same
      diff in a hooked fixture repo prints nothing.
- [ ] AC-03: Neither check ever changes the guard's exit code or denies
      a command; tests assert allow-with-warning for every trigger case.
- [ ] AC-04: No mutating git command runs against the foreign repo;
      source scan asserts read-only inspection only.
- [ ] AC-05: A `.ramp-declined` marker in the foreign repo suppresses
      both warnings; test covers presence and absence.
- [ ] AC-06: Commits inside this repo, and non-commit commands, are
      unaffected — guard latency for the common path is unchanged
      (no new subprocess unless the command is a foreign-cwd commit).
- [ ] AC-07: Tests added before implementation (RED/GREEN), following
      `.github/hooks/` existing test conventions.
- [ ] AC-08: The guard's audit log records each warning emitted, so
      "was the operator told?" is answerable after the fact.

## Risks

**Warning fatigue.** A daily-driver unenforced repo warns on every
commit. That is the point — the cure is ramping or `.ramp-declined`,
both of which are recorded acts.

**Guard latency.** The checks add filesystem stats and one read-only
git call, only on foreign-cwd commits. AC-06 keeps the common path
untouched.

**Enforcement-infrastructure surface.** This edits the guard that
edits everything else (`infrastructure_self_exempt` applies in reverse:
the guard gets the same TDD and review rigor it enforces). Warn-only
scope keeps the blast radius at one printed line.

## Alternatives Considered

- **A cron/scheduled scanner over sibling repos.** Rejected: the diary
  finding is that the transition is visible *at the commit*; a scanner
  reintroduces the four-day lag and needs its own home and schedule.
- **Block instead of warn.** Rejected by the plan's frozen wording:
  the tier decision is the operator's; a block would make the guard
  decide repo governance policy.
- **Fold into FR-865.** Rejected: parent judgement C-5 makes guard
  changes a separate enforcement-infrastructure judgement.

## Related

- `feature-requests/FR-864-ramp-spike-to-governed.md` (named and excluded this)
- `docs/plan-ramp-spike-to-governed.md` — sequence step 5
- `docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md`
- `docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md`
