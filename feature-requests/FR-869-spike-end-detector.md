# Feature Request: Spike-End Detector — Warn When an Unenforced Repo Goes Live

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-23), R-1…R-5 folded
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

### Warning delivery channel (R-1)

The hook contract returns JSON on stdout; a raw warning line would
corrupt the hook response. Contract: **warnings go to stderr; stdout
remains exactly the approve JSON.** Exact shapes — no warning: approve
JSON only; one warning: one `⚠ ...` line on stderr; two warnings: two
lines, unenforced-repo first. Tests prove the warning is visible in
captured hook output, stdout stays parseable JSON, and no
`permissionDecision: "deny"` appears in any FR-869 trigger case. If the
Copilot hook runtime later documents an approve-JSON warning field,
switching to it is a mechanical follow-up, not a scope change.

### Foreign-repo and command-form resolution (R-2)

| Case | Resolution |
|---|---|
| hook-owning repo root | resolved from `pre-command-guard.sh`'s own location |
| command repo root | resolved from the hook payload `cwd`, walking up to the nearest `.git` |
| nested dir inside either repo | normalized to its repo root |
| this repo | never warns |
| non-git cwd | never warns |
| supported command form | plain `git commit` (any flags) with repo taken from payload `cwd` |
| `git -C <path> commit`, leading `cd <path> && git commit` | **out of scope, named limitation** — a known bypass, not accidental behavior; revisit if witnessed in practice |

### Check 1 — unenforced repo: exact predicate (R-3)

The governance witness is **`pre-commit` alone**. The predicate is:
`.git/hooks/pre-commit` missing, **or** zero bytes, **or** the entire
`.git/hooks/` directory absent/empty. Other hooks (`commit-msg` etc.)
do not count — a repo whose only gate is a commit-msg hook is still
unenforced for this detector's purpose. Warn:
`⚠ this repo has no pre-commit hooks — scripts/ramp.sh <repo> --tier 1 exists`.

### Check 2 — spike ending: exact matcher (R-4)

Inspects **staged added lines only** (`git diff --cached`, `+` lines,
excluding `+++` metadata) in `.github/workflows/*.yml` and
`*.yaml`. Match terms: an added `schedule:` key or an added `secrets.`
reference. Deleted lines, context lines, comments outside workflow
files, and non-workflow paths never trigger. Fires only when Check 1
also fires — a repo with gates going live is not a finding. Warn:
`⚠ this commit takes an unenforced repo live`.

**Data-leakage boundary:** warning text and audit entries never include
diff content, secret names, secret values, or workflow line text — only
repo identity, a stable reason code, and whether the spike-end
condition was present.

### Shared constraints

- Filesystem inspection plus read-only `git diff --cached` only,
  mirroring FR-865 R-5: no mutating git command against the foreign
  repo; the guard never creates files there.
- Exit code is never affected: **warn-only, permanently** — not
  warn-then-block-later. A blocking version would be a new FR.
- Suppression: a repo-root `.ramp-declined` marker — never created by
  the guard — suppresses both warnings but still writes a non-secret
  audit entry (`reason=ramp-declined`), so suppression stays
  forensically visible.
- Every emitted warning writes an audit entry with a stable reason
  name, answering "was the operator told?" after the fact.
- Common path untouched: no new subprocess unless the command is a
  foreign-cwd commit.

### Human-review gate (R-5)

This edits the guard that edits everything else. The final guard diff,
exact warning strings, suppression semantics, and audit reason names
receive **recorded human review before activation**, logged in this
FR's implementation section. That review authorizes only this guard
change — no ramp installer, CI, graph, judge/review doctrine, or
target-repo changes.

## Acceptance Criteria

Superseded by the judgement's revised set (2026-08-23); folded verbatim.

- [ ] AC-01: FR-869 is revised to define the warning output channel, foreign-repo resolution table, hook-state predicate, suppression marker contract, staged diff matcher, audit reason names, data-leakage boundary, and human-review gate from R-1 through R-5.
- [ ] AC-02: A fixture foreign repo with `pre-commit` missing according to the revised predicate, invoked through the supported plain `git commit`/payload-cwd command form, emits exactly the unenforced-repo warning through the approved non-blocking channel and returns parseable approve JSON with no deny decision.
- [ ] AC-03: A fixture foreign repo with a zero-byte or otherwise in-scope missing/empty `pre-commit` state emits the unenforced-repo warning; a fixture repo outside that predicate does not.
- [ ] AC-04: A staged added line matching `schedule:` in `.github/workflows/*.yml` or `.github/workflows/*.yaml` in an unenforced foreign repo emits the spike-end warning in addition to the unenforced-repo warning.
- [ ] AC-05: A staged added line matching `secrets.` in `.github/workflows/*.yml` or `.github/workflows/*.yaml` in an unenforced foreign repo emits the spike-end warning in addition to the unenforced-repo warning.
- [ ] AC-06: The same staged workflow diff in a fixture repo with the revised hook-state predicate satisfied as "enforced" emits no FR-869 warnings and still returns approve JSON.
- [ ] AC-07: Deleted lines, context lines, diff metadata, comments if excluded by the revised matcher, and non-workflow files do not trigger the spike-end warning.
- [ ] AC-08: Commits inside this repo, non-commit terminal commands, and non-terminal tools do not run the new foreign-repo git-diff inspection path and preserve the existing approve/pass behavior.
- [ ] AC-09: A repo-root `.ramp-declined` marker suppresses both FR-869 warnings, is never created by the guard, and records a non-secret suppression audit entry.
- [ ] AC-10: Every emitted warning records a non-secret audit entry with a stable reason name; audit details include no staged diff content, secret names, secret values, absolute paths outside the minimum repo identity policy, hook logs, or token-bearing text.
- [ ] AC-11: Source scans or targeted tests prove the implementation performs no mutating git command against the foreign repo and never changes the guard's deny/allow decision for FR-869 trigger cases.
- [ ] AC-12: Tests are added before implementation for the revised behavior above, using fixture scratch repos and isolated `HOOK_LOG_DIR`, with RED/GREEN evidence recorded in the FR.
- [ ] AC-13: The final guard diff, warning strings, suppression behavior, and audit schema receive recorded human review before activation.

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
scope, the stderr channel (stdout JSON untouched), and AC-13's human
review keep the blast radius at printed lines.

**Known bypass.** `git -C <path> commit` and `cd <path> && git commit`
are out of scope by the R-2 resolution table — a named limitation,
revisited if witnessed in practice.

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
