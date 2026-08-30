# Feature Request: Deny agent-issued gh pr merge --admin

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (judgement folded 2026-08-30; enforcement gated on FR-934 completion per C-2). GATE UNREACHABLE (2026-08-30): FR-934 phase 2 is BLOCKED BY PLATFORM — the merge_queue rule is org-only and this repo is user-owned; operator chose to stay on the strict regime. Without a queue, agents have no compliant merge verb when strict blocks green PRs, so denying `--admin` would deadlock the flow. Enforcement stays dormant unless the repo moves to an org or the judgement is revisited.
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the first agent session after FR-934's
merge queue is live that reflexively types `gh pr merge --squash
--admin` — the guard denies it and points at the queue verb. Witnessed
frequency: at least four distinct sessions used `--admin` as the routine
merge verb on 2026-08-30 alone (PRs #519, #520 among them), including
after the deadlock that justified it was already cured.
**Research:** [FR-935.research.md](FR-935.research.md) — equivalent
committed record per FR-890 R-6 (five dispositioned solution classes
with precedent lines, preserved subtractionist dissent, explicit
`is_this_a_graph: No`), composed after two sole-route failures on
2026-08-30 (librarian_structure 400-char cap, exit 65, defect in
FR-932's in-flight territory); to be superseded by a sole-route rerun
when the route heals. Problem evidence:
`feature-requests/research-briefs/fr934-merge-integration-toll-brief.md`
(Witnessed incidents) and `docs/plan-research-merge-queue.md`
§"The `--admin` habit is the real enemy".
**Prior art:** the PreToolUse guard
(`.github/hooks/scripts/pre-command-guard.sh`) already denies
`--no-verify`, Co-authored-by trailers, multiline `git commit -m`, and
unpiped pytest — this FR conforms to that existing pattern (Commandment
4) rather than inventing a new enforcement surface.
`reference/break-glass.md` owns the documented exception path and is not
modified. FR-438 polices vendor-default thoughtcrimes at the same
boundary. No prior or REJECTED FR governs the merge verb.

## Summary

Add a PreToolUse guard rule denying agent-issued `gh pr merge`
invocations that carry `--admin`, in any flag order. There is no
agent-settable escape (judgement R-3): the denial message names the
compliant verb (`gh pr merge --squash`, which auto-enqueues under
FR-934's queue) and points the operator at `reference/break-glass.md` —
the human emergency path stays outside the agent command boundary.

## Dependency gate (judgement R-2)

Enforcement of this FR may begin only after FR-934 is merged and its
implementation record proves the merge queue is required on `main`,
`strict` is false, and the required merge-group contexts report
successfully. Denying the current routine escape before the replacement
path works is not authorized.

## Value Statement

The merge queue (FR-934) only serializes what passes through it; this
guard makes the bypass exceptional and audited instead of the default
verb, so the required checks gate reality again.

## Problem

`enforce_admins` is disabled on `main`, so `gh pr merge --admin`
bypasses every required context unconditionally. The habit was
rational while docs-only PRs deadlocked (FR-889 §4d), but the cure is
live — witnessed green on docs-only PR #520 — and the habit outlived
its justification the same day: sessions kept admin-merging PRs whose
checks would have passed. A queue that everyone bypasses serializes
nothing; detection without enforcement is advisory
(`detection_without_enforcement`), and the enforcement belongs at the
boundary where the command enters (`the_one_law`), which for agent
sessions is the PreToolUse guard.

## Proposed Solution

In `.github/hooks/scripts/pre-command-guard.sh`, following the existing
denial-rule pattern (judgement R-3/R-4):

- Deny terminal command segments that actually invoke `gh pr merge` and
  include `--admin`, regardless of the relative order of `--admin` and
  other flags. Do not deny plain `gh pr merge --squash`, other `gh`
  subcommands, or grep/echo text that merely mentions the forbidden
  command — the guard already encodes this executable-context vs
  textual-mention distinction for another forbidden flag.
- No agent-settable bypass: `BREAK_GLASS=1 gh pr merge --admin` (or any
  variable/sentinel prefix) remains denied. A bare variable the same
  agent can prepend to its next command is not an authorization
  boundary. The human emergency path is `reference/break-glass.md`
  (admin authority, named emergencies, diary incident record within
  24h) and is exercised outside the agent PreToolUse boundary; that
  document is not modified.
- Denial message: one line naming `gh pr merge --squash` as the queue
  verb plus the `reference/break-glass.md` pointer; one stable
  `decision: deny` audit reason in `.github/hooks/logs/audit.jsonl`.

Witnesses live in `.github/hooks/tests/test_pre_command_guard.py`
(the existing behavioral suite, using the `HOOK_LOG_DIR` isolation
seam): denied in both flag orders, denied under a `BREAK_GLASS=1`
prefix, plain queue verb and textual mentions approved, stable audit
reason asserted. `.github/hooks/README.md` active-check table and
audit-reason documentation updated.

Traceability (judgement R-5): this is a new capability — new
`capabilities/CAP-XXX-*.yaml` with a new `REQ-YG-XXX` (not REQ-YG-527,
which governs branch-create denial guidance), matching
`ARCHITECTURE.md` entries, every new test tagged, the changelog
fragment referencing the same requirement.

Non-goals: no change to `enforce_admins` (admin overrides remain the
operator's documented single-dev flow at the GitHub settings level;
this FR governs the agent command boundary, not the human's browser),
no change to `reference/break-glass.md`, no server-side enforcement,
no generalized shell parser.

## Acceptance Criteria

Superseded per judgement: the revised acceptance criteria AC-01 through
AC-08 in
[FR-935-deny-admin-merge-outside-break-glass.judgement.md](FR-935-deny-admin-merge-outside-break-glass.judgement.md)
govern enforcement verbatim — real-hook denial witnesses in both flag
orders, `BREAK_GLASS=1` prefix still denied, false-positive contract
(plain verb, other subcommands, textual mentions approved), stable
audit reason via `HOOK_LOG_DIR`, README documentation, new capability +
`REQ-YG-XXX` traceability with green `req_coverage --strict`, RED
before GREEN in PR history, changelog fragment + implementation record
+ diary reflection.

## Alternatives Considered

| alternative | disposition |
|---|---|
| Enable `enforce_admins` server-side | REJECTED — removes the operator's own documented single-dev override and the break-glass path with it; server setting can't distinguish agent from human |
| Strip admin scope from the agent credential (subtraction) | DEFERRED — the strongest dissent, preserved in FR-935.research.md; requires operator/agent credential separation that doesn't exist today; becomes the mandated escalation if this guard is ever witnessed bypassed |
| Advisory doctrine line ("don't use --admin") | REJECTED — the doctrine already implies it and four sessions used it in one day; `detection_without_enforcement` names this failure |
| Delete gh CLI access for agents | REJECTED — destroys the entire PR flow to police one flag |
| PreToolUse guard denial, no agent-settable escape (this FR) | PURSUED — conforms to the existing guard pattern, keeps the human emergency path outside the agent boundary, costs one rule plus witnesses |

## Related

- FR-934 (companion — the queue this guard protects; this FR is sequenced after FR-934 lands)
- FR-889 §4d (the deadlock whose cure removed the bypass's justification)
- `.github/hooks/README.md` (guard architecture), `reference/break-glass.md` (exception path)
- docs/plan-research-merge-queue.md §"The `--admin` habit is the real enemy"
