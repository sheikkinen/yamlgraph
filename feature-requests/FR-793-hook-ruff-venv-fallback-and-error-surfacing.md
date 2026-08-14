# Feature Request: Hook ruff venv fallback and hook-error surfacing

**Priority:** MEDIUM
**Type:** Bug
**Status:** In Progress (judged APPROVED WITH REVISIONS 2026-08-14; R-1..R-5 folded below)
**Effort:** 0.5 days
**Requested:** 2026-08-14
**First consumer / first event:** the very next agent `.py` edit in this
repo — `post-edit-python-checks` fires on it and, today, silently skips
all ruff feedback because `command -v ruff` fails in the hook runner's
PATH. Second consumer: the human running `.github/hooks/cmd status`, who
today cannot see that a hook has been erroring 1,818 times.

## Summary

The `post-edit-python-checks` PostToolUse hook resolves ruff via
`command -v ruff`. Ruff is installed only in the repo venv
(`.venv/bin/ruff`, v0.15.18), not globally, so the lookup has failed
**1,818 times between 2026-05-20 and 2026-08-14** (last occurrence
today, 14:04 UTC). Each failure logs `error/ruff-missing` to
`audit.jsonl` and silently skips lint + format feedback. Nothing
monitors the audit log, so a hook erroring on ~3.5% of all invocations
stayed invisible for three months. Fix the resolution (venv fallback)
and close the self-monitoring gap (error counts in `cmd status`).

## Value Statement

Agents get the edit-time ruff feedback the hook was built to provide,
eliminating the pre-commit bounce cycle (~3 min pytest per bounce) that
this hook exists to prevent; the human gets a one-command view of hook
health so a silently failing hook can never accrue 1,800 errors again.

## Problem

Two defects, one incident:

1. **Broken binary resolution.** `python-checks.sh` (and any sibling
   check that shells out to ruff) uses `command -v ruff`. The Copilot
   hook runner's PATH does not include the repo venv, and ruff is not
   installed globally. Result: on every `.py` edit, the ruff lint check,
   the format check, and the FR-433 auto-fix pass are all skipped. The
   errors only surface later, at pre-commit, costing a full hook cycle
   per bounce (see user memory `precommit-dry-run`: each bounce ≈ 3 min).

2. **Self-exempt infrastructure.** FR-414 added the `ruff-missing`
   audit entry precisely "so the gap is visible in the audit trail" —
   but visibility without a consumer is `detection_without_enforcement`
   (Scripture). No surface reports hook error rates; `cmd status`
   reports lockdown state only. The enforcement layer violates
   `infrastructure_self_exempt`: it gates everything except itself.

Evidence (audit.jsonl, 2026-05-20 → 2026-08-14, 51,848 invocations):

```
1818 "decision": "error"  — 100% reason: ruff-missing
     spread over 53+ distinct days; still firing today
```

## Ideal Result

Every `.py` edit gets real ruff feedback at edit time regardless of the
hook runner's PATH, and `.github/hooks/cmd status` shows per-hook error
counts so any hook failing silently becomes visible in the same command
the human already runs. The `ruff-missing` error becomes what FR-414
intended: a rare signal of a genuinely broken environment, not a
3-month-old steady state.

## Proposed Solution

**1. Venv-fallback ruff resolution in `common.sh`** (shared, so all
check scripts inherit it). Resolver contract (R-4, binding):

1. If `HOOK_RUFF_BIN` is set (test seam): use it iff executable, else fail.
2. Else resolve from PATH (`command -v ruff`).
3. Else `$repo_root/.venv/bin/ruff`, where `repo_root` is derived from the
   hook script's own location (`git -C <script_dir> rev-parse --show-toplevel`),
   not the cwd or the edited file.
4. Return failure without output when none exists.

All ruff invocations in `python-checks.sh` use the resolved absolute
command via `"$RUFF_BIN"` — no remaining `command -v ruff` or bare
`ruff` calls. `ruff-missing` is audit-logged exactly once per inspected
Python file when resolution fails (FR-414 contract preserved).

**Implementation decision (deviation from R-4 literal text):** the
`HOOK_RUFF_BIN` env seam is added so tests can simulate both total
absence and fixture-path presence deterministically without depending
on the developer's real `.venv` — R-4's own test-determinism
requirement is unsatisfiable without a seam, because the fallback
anchors to the hook script's repo, which in tests IS the real repo.

**2. Hook-error surfacing in `cmd status`** (R-1: the real surface is
the sentinel-command interception inside
`.github/hooks/scripts/pre-command-guard.sh`, not a standalone `cmd`
file). The existing python3-in-hook status summary (R-2: no jq/awk —
the hook already depends on python3) is extended with last-7-days
error counts grouped by hook + reason:

```
Audit: N total entries. Decisions: ... Lockdown: no
Hook errors (7d): post-edit-python-checks/ruff-missing=3
```

Zero errors prints an explicit `Hook errors (7d): none` line so absence
of the section can never be confused with absence of errors.

**3. Tests use synthetic audit fixtures (R-3):** the live
`.github/hooks/logs/audit.jsonl` is gitignored and local-only; tests
write synthetic entries under `HOOK_LOG_DIR` — one recent error, one
older-than-7-days error, one no-error case — making the 7-day window
mechanically checkable.

## Acceptance Criteria (frozen by judgement 2026-08-14)

- [ ] AC-01: A test demonstrates that when `ruff` is absent from PATH but
      present at a deterministic fixture path, a Python edit with a ruff
      violation produces ruff feedback instead of `ruff-missing`.
- [ ] AC-02: A test demonstrates that when `ruff` is absent from both PATH
      and the fallback, `post-edit-python-checks` logs exactly one
      `decision: "error", reason: "ruff-missing"` entry per inspected file.
- [ ] AC-03: A test demonstrates `POST_EDIT_AUTO_RUFF=1` uses the same
      resolved binary and still emits `ruff-autofix-applied` on change.
- [ ] AC-04: All ruff invocations in `python-checks.sh` use the shared
      resolved command; no `command -v ruff`, bare `ruff check`, or bare
      `ruff format` calls remain in that script.
- [ ] AC-05: `.github/hooks/cmd status` output (produced by
      `pre-command-guard.sh`) includes last-7-days hook error counts
      grouped by hook and reason when synthetic recent errors exist.
- [ ] AC-06: Status output includes an explicit zero-error line when the
      synthetic audit log contains no recent error entries.
- [ ] AC-07: The status test proves the 7-day window by excluding an
      older-than-7-days synthetic error from the displayed count.
- [ ] AC-08: `.github/hooks/README.md` documents the venv fallback, the
      retained `ruff-missing` failure mode, and the status output shape.
- [ ] AC-09: The FR records implementation decisions and deviations before
      enforcement is marked complete.

## Alternatives Considered

- **Install ruff globally (brew/uv tool).** Fixes this machine only;
  unversioned drift from the pinned dev environment (FR-761 governs
  reproducibility). Rejected.
- **Export venv PATH in the hook runner config.** Couples every hook to
  one venv layout and fixes nothing for sibling repos in the workspace.
  Rejected — resolution belongs at the boundary where the binary is
  needed (`callsite_fix` inverted: the shared `common.sh` IS the right
  utility here because every check script has the identical need).
- **A separate hook-health dashboard/daemon.** Over-engineering; the
  human already runs `cmd status`, so the counts belong there
  (`who_reads_this_when`: the reader and moment already exist).

## Related

**Prior art:** FR-414 (Enforced) added the `ruff-missing` audit entry —
visibility without a consumer; this FR adds the consumer. FR-433
(Implemented) added the auto-ruff pass — dead when resolution fails;
revived by the same fallback. Noun-scan hits FR-512, FR-482, FR-485,
FR-669, FR-499 are all dm-v2/extraction-domain matches on generic words
(ruff/fallback/error/surfacing) — no territorial overlap with hook
infrastructure; dispositioned as spurious.

- FR-414 (Enforced): added the `ruff-missing` audit entry — visibility
  without a consumer; this FR adds the consumer.
- FR-433 (Implemented): auto-ruff pass, currently dead when resolution
  fails; revived by the same fallback.
- `.github/hooks/scripts/checks/python-checks.sh`,
  `.github/hooks/scripts/checks/common.sh`, `.github/hooks/cmd`
- Scripture: `detection_without_enforcement`,
  `infrastructure_self_exempt`, `substance_over_presence`
- Incident evidence: `.github/hooks/logs/audit.jsonl` (1,818 ×
  `ruff-missing`, 2026-05-20 → 2026-08-14)

## Judgement (2026-08-14)

**Verdict:** APPROVED WITH REVISIONS (draft: `tmp/draft-judgement.md`;
judge run: `tmp/judge-fr793.log`, model gpt-5.5 via `scripts/judge.sh`)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | `cmd status` is intercepted inside `pre-command-guard.sh`, not a standalone file | Status deliverable = changes to `pre-command-guard.sh`, `test_pre_command_guard.py`, README command-channel docs |
| R-2 | "awk/jq pass" is an undeclared dependency choice | Use the existing python3-in-hook parser style; no jq |
| R-3 | Live audit.jsonl is gitignored — not committed evidence | Tests create synthetic `HOOK_LOG_DIR` fixtures: recent error, >7d error, no-error |
| R-4 | Resolver contract loose; conftest prepends `.venv/bin` to PATH, masking the bug | Contract frozen (see Proposed Solution); tests simulate PATH absence deterministically via `HOOK_RUFF_BIN` seam |
| R-5 | Enforcement-infrastructure change | Human review required before merge (GATE) |

**Purge list:** hook daemons/dashboards; global ruff install or PATH
mutation; jq; changes outside the hook subsystem; mining the live audit
log for tests.

**Scope frozen:** D-1 `common.sh` resolver; D-2 `python-checks.sh` call
sites; D-3 `pre-command-guard.sh` status extension; D-4/D-5 hook tests;
D-6 README; D-7 this FR.

### Questions for the human (as options, or 'none')

C-2 GATE: human review of the hook diff required before merge — this
changes enforcement infrastructure. Everything else: none.
