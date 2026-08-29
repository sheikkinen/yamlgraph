# Feature Request: Session Worktree Lifecycle — Worktree at Session Start, Checkpoint Commit per Turn

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS folded ([judgement](FR-902-session-worktree-lifecycle.judgement.md), 2026-08-29)
**Effort:** 3-4 days
**Requested:** 2026-08-29
**First consumer / first event:** the next VS Code Copilot agent session that opens in this repo — at its first `SessionStart` hook fire, a session lane exists and the briefing names it; at its first `Stop` hook fire, its turn output is committed as a checkpoint.
**Research:** in-body dispositioned alternatives table (§Alternatives Considered) + witnessed incident record (§Problem) + quantitative evidence table (§Evidence) from the FR-898 session ledger.
**Prior art:** FR-888 (main-write guard — this FR is its completion: guard denies, this provides the lane the guard points at); FR-898 (session ledger — supplies the `Session-Id`/`Request-Index` join keys and the quantitative evidence); FR-742 (undelivered-diary detection — same session-death boundary, different artifact); scripts/worktree.sh (manual worktree route — mechanized here at SessionStart); one_session_one_repo Scripture entry (the ritual this FR replaces with mechanism); FR-908 (unrelated digest FR that previously held the 902 number before the renumber arc).

## Summary

Give every agent session its own git worktree at session creation (SessionStart hook), enforce lane ownership mechanically at the PreToolUse guard, commit the working tree as a fenced **checkpoint commit** on the session branch after every agent turn (Stop hook), and hand the finished branch to the merge boundary where all enforcement already lives. Turn-level commits carry `Session-Id` + `Request-Index` trailers, making the cost ledger (FR-898) joinable to git history at turn/request granularity.

## Ideal Result

An agent session cannot corrupt another session's index, working tree, or untracked files — denied mechanically, not by ritual; nothing a session produces is ever lost (every turn is committed); and every tree delta is traceable to the exact conversation turn — and therefore the exact credits — that produced it. Doctrine enforcement is untouched: it fires once, at the merge boundary, as Scripture already demands.

## Evidence (R-6)

FR-898 session ledger replay (`scripts/vscode/session_ledger.py --csv`, chatSessions store `a7be91fc-41b5-4d46-b3f5-acaad7314ed3`, run 2026-08-29). Merged result of that session: squash `77cbea05`, 20 files, +1,643/−77 lines.

| Phase | Requests | Credits | % |
|---|---|---|---|
| plan + judge | r1–r22 | 1,946.1 | 29.9% |
| enforce RED+GREEN | r23–r36 | 2,181.3 | 33.6% |
| reports/archaeology | r37–r44 | 386.6 | 5.9% |
| push/PR/CI/merge | r45–r51 | 1,984.9 | 30.5% |
| **Total** | **51** | **6,499.0** | 100% |

Joining these credits to the landed diff required manual archaeology because git commits and ledger requests share no key — the gap this FR closes.

## Value Statement

Every parallel agent session (the operator routinely runs 3+) gains collision immunity and turn-level provenance for the cost of one worktree per session.

## Problem

Three witnessed incident classes, all from this repo's own record:

1. **Shared-index corruption (`one_session_one_repo`, Scripture entry, third strike 2026-07-14):** four interleave incidents in one day — staged files swept into foreign commits, `checkout`/`add -u` destroying WIP, pip reinstall deleting console scripts mid-run. The Scripture's current cure is a *ritual* (staged-check, explicit file lists, immediate commits) — behavioral, not mechanical.
2. **Untracked-file loss at teardown (FR-898 landing, 2026-08-29):** worktree removal was blocked by a foreign sister-session's untracked diary file that existed nowhere else; only manual preservation saved it. Untracked files have no recovery path (`boundary_inventory` trap).
3. **Cost/provenance gap (FR-898 ledger, 2026-08-29):** the FR-898 session cost 6,499 credits; joining that cost to the 1,643 landed lines required manual archaeology because git commits and ledger requests share no key. The diary Seed "cost-per-FR join via the FR spine" names this gap.

Additionally, per-turn work currently lives uncommitted for hours: a session crash (they die exactly when reflection is due — FR-742) loses everything since the last manual commit.

## Proposed Solution

Three small mechanisms wired into existing hook infrastructure (`.github/hooks/session-probe.json` already dispatches `SessionStart`, `Stop`, `SessionEnd` with `session_id` in the payload):

### 1. SessionStart: create the session lane (R-1, R-2, R-3)

`.github/hooks/scripts/session-worktree.sh` (new, invoked from the existing `SessionStart` entry) — a thin hook wrapper over an extended `scripts/worktree.sh session <session-id>` mode, reusing the existing substrate (`.venv`/`.env` provisioning, `cd` target output) instead of a parallel raw `git worktree add`.

- **Hook input contract:** parse hook JSON from **stdin** (same as `session-probe.sh`); validate `session_id` as a UUID-shaped safe path segment; reject path traversal and malformed ids with non-success status + audit entry.
- **Naming:** full sanitized session id — branch `session/<full-session-id>`, lane `tmp/worktrees/session/<full-session-id>`. No short ids (collision-unsafe).
- **Idempotency:** no-op when branch and worktree already match the expected lane (re-fire on PostCompact/resume); if the branch exists without the expected lane, refuse and print a recovery instruction. It must **never delete an existing `session/*` branch** — the current `worktree.sh new` branch-deletion path is explicitly not inherited.
- **Setup-diff fix:** session setup must not dirty the tree (e.g. `worktree.sh` appending `.venv` to a `.gitignore` that already contains `.venv/`); setup alone produces no checkpoint.
- **Mechanical ownership contract:** a hook alone cannot move the agent's cwd, so lane delivery is enforced, not advised. Once a session lane exists, the PreToolUse guard **denies write-capable tools and write-shaped terminal commands targeting this repo whose resolved target/cwd is outside the session's own lane**. The denial prints the absolute lane path and the command shape to work there. Read-only commands stay allowed. One audited escape hatch (FR-888-style env var) bypasses only this denial class — never the `--no-verify`/Co-authored-by/FR-888 guards.
- `session-briefing.sh` output names the lane path to the agent.

### 2. Stop: checkpoint commit per turn (R-3, R-4)

`.github/hooks/scripts/session-checkpoint.sh` (new, invoked from the existing `Stop` entry).

**Fenced checkpoint policy** — hook-free commits are permitted only when ALL hold:

1. executed inside `.github/hooks/scripts/session-checkpoint.sh` (not agent tool calls),
2. `HEAD` is on `refs/heads/session/*`,
3. `git diff-index --quiet HEAD --` proves a tree change exists,
4. the commit carries `Session-Id` and `Request-Index` trailers and message `checkpoint(session): turn <N>`.

No `--allow-empty-message` (the message is never empty). `git add -A` respects `.gitignore` (witness test: `.env`-style file never staged).

- **Request-Index derivation:** replayed from the committed platform store (`chatSessions/*.jsonl`, same contract as `session_ledger.py`) or a fixture-tested hook payload field. Store not yet flushed → bounded retry, then skip-with-audit; never a fabricated index.
- **Duplicate-Stop idempotency:** the same request index produces no second commit unless the tree changed after the previous checkpoint; detection metadata is fixture-tested.
- **Doctrine reconciliation (`automation_inherits_doctrine`):** checkpoints are event-log entries, not commits destined for main. `enforcement_at_merge_boundary` is Scripture — the PR gauntlet fires untouched, and squash merge keeps checkpoints off main. `pre-command-guard` still denies agent-issued `--no-verify` (existing tests stay green; no carve-out).
- **Human-review gate (C-2):** the hook/guard enforcement diff is reviewed by the operator before the policy is treated as live.

### 3. Merge handoff + GC (R-5)

- FR complete → session branch is pushed and enters the normal PR gauntlet (squash merge; checkpoints vanish from main history).
- Session dies mid-FR → the branch **is** the recovery artifact: every turn committed, nothing untracked to lose. Successor sessions adopt the *branch* (visible in `scripts/vscode/now.py` sweep), not the worktree.
- **GC algorithm** (`--gc`, operating on `session/*` branches/worktrees ONLY, via a prefix-aware extension of `worktree.sh rm-safe` which currently hardcodes `feat/`):
  - `--dry-run`/list mode classifies each lane: live, merged, stale-clean, dirty, untracked-present, unpushed, unmerged.
  - Prune deletes only **merged** lanes and **stale-clean** lanes — last checkpoint older than N=14 days AND commit identical to merge-base with `main` AND zero untracked files.
  - Refuses with a printed reason on: untracked files present, unpushed commits, any checkpoint not represented at the merge boundary.
  - Never uses `git worktree remove --force` or `git branch -D` as an automatic path.

### Provenance join (delivers two Scripture seeds)

Checkpoint trailers give `checkpoint SHA ↔ Session-Id + Request-Index ↔ ledger request ↔ credits`. This mechanizes `artifact_carries_code_identity` (seed) and the FR-898 diary Seed (cost-per-FR join): `git log --format='%H %(trailers:key=Request-Index)'` joined against `session_ledger.py --csv` yields **turn/request-level provenance** — the request, checkpoint SHA, model, and credits behind each tree delta. (Not credits-per-line: a checkpoint identifies the turn that produced a delta; apportioning credits to individual lines across later edits is out of scope.)

## Acceptance Criteria (frozen by judgement — AC-01..AC-14)

- [ ] AC-01: `SessionStart` fixture feeds hook JSON on stdin; `session-worktree.sh` validates `session_id`, creates `tmp/worktrees/session/<full-session-id>` + branch `session/<full-session-id>`, provisions the same environment as `scripts/worktree.sh`, emits the absolute lane path, and is a no-op on re-fire when branch and worktree match
- [ ] AC-02: lane creation refuses path traversal, malformed ids, short-id collisions, branch-exists-with-wrong-worktree, and worktree-exists-with-wrong-branch with explicit non-success status/audit; never deletes an existing `session/*` branch as recovery
- [ ] AC-03: after a lane exists, write-shaped fixtures targeting this repo outside the owning lane are denied with the lane path; the same writes inside the lane are allowed; read-only commands remain allowed; the audited escape hatch bypasses only the FR-902 denial class and no FR-888/Co-authored-by/`--no-verify` guard
- [ ] AC-04: `Stop` fixture commits only when `git diff-index --quiet HEAD --` detects a tree change in the session lane; message is `checkpoint(session): turn <N>`; trailers carry exact `Session-Id` and `Request-Index`
- [ ] AC-05: duplicate `Stop` fixtures for the same request index create no second commit unless a later tree change exists; test asserts commit count and trailers
- [ ] AC-06: request-index derivation is tested against a replayed `chatSessions/*.jsonl` fixture or a documented hook payload field; store-not-flushed surfaces as bounded retry / skip-with-audit, never a fabricated index
- [ ] AC-07: `.gitignore` is respected under checkpointing (`.env`, `.env.*`, `.venv/`, hook logs, ignored `tmp/`); setup alone produces no checkpoint commit
- [ ] AC-08: checkpoint commits are confined to `session/*`; squash-merge fixture proves checkpoint subjects/trailers never land on `main`; existing `pre-command-guard` tests still deny agent-issued `--no-verify`
- [ ] AC-09: GC dry-run reports live/merged/stale-clean/dirty/untracked/unpushed/unmerged lanes; prune deletes only merged or stale-clean lanes and refuses every loss-bearing case with a reason
- [ ] AC-10: `now.py` lists live session lanes and unmerged orphan `session/*` branches with age, branch, worktree path, untracked count, PR/open-branch status; never deletes
- [ ] AC-11: join demo emits a mechanically checkable table for a real session: request index, checkpoint SHA, model, credits, prompt/summary availability; evidence source committed or quoted in this FR
- [ ] AC-12: hook tests live under `.github/hooks/tests/` with `@pytest.mark.req("REQ-YG-XXX")` tags; requirement/capability metadata added per ADR-001
- [ ] AC-13: human review of the hook/worktree enforcement diff is recorded before the policy is live
- [ ] AC-14: this FR carries the folded evidence table, implementation record, changelog fragment, and diary reflection

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| **Keep the behavioral ritual** (Scripture `one_session_one_repo` staged-check litany) | REJECTED — third strike already recorded; rituals decay under parallelism, mechanics don't (`two_strike_split`: mechanizable level belongs in code) |
| **Worktree keyed to FR instead of session** | REJECTED for v1 — session starts before the FR is known; FR adoption handled by successor-adopts-branch rule. FR-keyed lanes remain the manual pattern for long arcs (`tmp/worktrees/feat/*` continues to work) |
| **Lazy worktree creation on first write** (skip lane for read-only sessions) | REJECTED — requires intercepting first write intent (complex, racy); `git worktree add` is ~100 ms and GC reclaims idle lanes |
| **Per-turn `git stash` / reflog instead of commits** | REJECTED — stashes are a stack (collision-prone across turns), carry no trailers, and are invisible to `now.py`/ledger joins |
| **Run full pre-commit on every checkpoint** | REJECTED — checkpoints are event-log entries of possibly-RED states (TDD requires committing RED); gates fire at the merge boundary per Scripture, and per-turn hook latency (~10-30 s) would tax every turn |
| **Delegate final merge to a cheaper model in the same FR** | DEFERRED to follow-up FR — independently shippable; watcher2 already provides CI remediation/PR reuse/changelog gen, so the follow-up is a handoff contract, not a new agent. FR-898 measured the prize: 1,985 cr (30.5% of session) landing tax, mostly mechanical |

## Out of Scope (per judgement "Not authorized")

- The cheap-model merge lane itself (follow-up FR; depends on this one's session-branch handoff)
- Rebuilding `ledger.py` on replayed `copilotCredits` (separate Seed, FR-898 diary)
- Any change to merge-boundary gates beyond tests proving they still apply
- Any change to judge/review doctrine or sole-route adapters
- Automatic deletion of branches with unmerged/unpushed checkpoint commits
- Committing generated ledger reports or prompt-bearing CSVs (quote minimal non-sensitive rows only)

## Related

- [FR-902-session-worktree-lifecycle.judgement.md](FR-902-session-worktree-lifecycle.judgement.md) — APPROVED WITH REVISIONS; scope frozen to D-1..D-9, gates C-1..C-6
- FR-898 session accountability ledger (merged 77cbea05) — supplies the join's other half
- FR-888 main-write guard — the enforcement precedent for lane discipline
- FR-742 successor briefing — session-death recovery this FR makes lossless
- Scripture: `one_session_one_repo`, `enforcement_at_merge_boundary`, `artifact_carries_code_identity` (seed), `boundary_inventory`
- `.github/hooks/session-probe.json`, `.github/hooks/scripts/session-briefing.sh` — the wiring points
- docs/diary/2026-08-29-reflection-fr-898-event-log-plausible-ledger.md — Seed this FR delivers
