# Judgement: FR-902 Session Worktree Lifecycle -- Worktree at Session Start, Checkpoint Commit per Turn

**Prior art:** gate hits are the FR's own precedent set — FR-888, FR-898, FR-742, scripts/worktree.sh, the one_session_one_repo Scripture entry — each dispositioned in the FR's Prior art line and the Reviewed-against list below; the sibling FR-902 artifact is this judgement's own subject, committed together.

**Verdict:** APPROVED WITH REVISIONS -- the problem is real and the session-lane direction is strategically sound, but authority activates only after the FR replaces advisory routing with a mechanical ownership contract, defines hook-input/request-index mechanics, reconciles checkpoint commits with doctrine, and supplies the missing quantitative evidence.

**Reviewed against:** `feature-requests/FR-902-session-worktree-lifecycle.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/hooks/session-probe.json`; `.github/hooks/scripts/session-probe.sh`; `.github/hooks/scripts/session-briefing.sh`; `scripts/worktree.sh`; `scripts/vscode/now.py`; `scripts/vscode/session_ledger.py`; `feature-requests/FR-898-session-accountability-report.md`; `feature-requests/FR-888-main-write-guard-worktree-route.md`; `feature-requests/FR-742-undelivered-diary-detection.md`; `docs/diary/2026-08-29-reflection-fr-898-event-log-plausible-ledger.md`; `.gitignore`; `.pre-commit-config.yaml`.

## What is sound

The pain is evidenced and belongs in repo automation, not developer memory. FR-902 cites the `one_session_one_repo` incident class directly (FR-902 lines 27-31), and the Scripture records the same shared-index, working-tree, environment, and staging hazards as a third-strike process failure (copilot-instructions lines 156-163). This is not speculative.

The proposal preserves the correct enforcement boundary in principle: checkpoint commits are positioned as recoverable event-log entries, while real policy gates remain at PR/squash merge (FR-902 lines 60, 66, 78-79, 101; copilot-instructions line 159). That separation is the right shape if the checkpoint path is tightly fenced.

The prior-art reuse direction is mostly right. The repo already has measured hook events on `SessionStart` and `Stop` (session-probe.json lines 3-14, 50-56), session-id extraction from hook JSON stdin (session-probe.sh lines 9-24), a session-start briefing surface (session-briefing.sh lines 9-16), a worktree substrate with `.venv`/`.env` setup (worktree.sh lines 146-181), safe removal precedent (worktree.sh lines 297-357), an orphan-worktree board surface (now.py lines 41-90), and a ledger that exposes per-session/per-request rows (session_ledger.py lines 165-205, 266-294, 317-340).

Strategic classification: process/enforcement primitive, equivalent to a repo-local framework primitive. It serves at least three real use cases -- parallel-session collision prevention, crash recovery, and turn-cost provenance -- and existing advisory rituals are explicitly insufficient (FR-902 lines 27-31, 90-95; copilot-instructions lines 156-163).

## Required revisions

### R-1: Replace advisory lane delivery with a mechanical session-ownership contract

Revise the FR so `SessionStart` does not claim the agent "receives" an isolated worktree merely because a hook created one. A hook can emit output and create files, but it cannot change the parent agent process's working directory; the current briefing script only runs `now.py --brief` after `cd "$REPO"` inside the child hook process (session-briefing.sh lines 9-14).

Add a binding enforcement mechanism: after a session lane exists, write-capable tools and terminal write-shaped commands targeting this repository are denied unless their resolved target/cwd is inside that session's own `tmp/worktrees/session/<session-id>` lane, with read-only commands allowed and a single audited escape hatch for intentional main-lane maintenance. The denial must print the exact absolute session-lane path and the command shape needed to work there. Without this, the Ideal Result ("can never corrupt another session's index, working tree, or untracked files", FR-902 line 17) is not true.

### R-2: Reuse and harden the existing worktree substrate instead of adding a parallel raw `git worktree add`

Replace the proposed raw snippet (FR-902 lines 41-45) with an extension of `scripts/worktree.sh` or a shared helper it owns. The existing substrate already provisions `.venv` and `.env` (worktree.sh lines 150-162) and prints a `cd` target (lines 175-181), so duplicating `git worktree add` would reintroduce setup drift.

The revision must add an idempotent session mode: if the session branch and worktree already point to the expected lane, it is a no-op; if the branch exists without the expected lane, it refuses and reports a recovery instruction; it must never delete an existing session branch. This is required because the current `new` path deletes a pre-existing branch (worktree.sh lines 125-128), which is unsafe for session recovery.

Also fix the setup-diff trap before checkpointing is authorized: `worktree.sh` currently appends `.venv` when `.gitignore` already contains `.venv/` (worktree.sh lines 165-166; `.gitignore` lines 11 and 96). A fresh session lane must not create a checkpoint solely from setup's own `.gitignore` normalization.

### R-3: Define hook JSON parsing, session-id validation, branch naming, and request-index derivation

Replace the undefined shell variables in the FR (`SESSION_ID_SHORT`, `SESSION_ID`, `N`, and `WT`; FR-902 lines 43-57) with a concrete parser contract. The scripts must read the hook JSON from stdin, just as `session-probe.sh` does (session-probe.sh lines 9-24), validate `session_id` as a safe UUID/path segment, and use a collision-safe branch/path name. Prefer the full sanitized session id; if a short id is retained, add a collision test.

Define `Request-Index` as a value derived from the committed platform store by replay or from a tested hook payload field. The committed ledger's request index is one row per request (session_ledger.py lines 190-205), but FR-902 must specify when the `Stop` hook can trust that the store has flushed and what it does when no matching request exists yet. The checkpoint script must be idempotent across duplicate `Stop` fires: the same request index must not produce multiple checkpoint commits unless the tree changed after the previous checkpoint, and the metadata used to detect that fact must be fixture-tested.

### R-4: Fence hook-free checkpoint commits as a narrow event-log exception

Do not leave `git commit --no-verify --allow-empty-message` as a naked implementation detail (FR-902 lines 55-57). Repo doctrine says automation inherits doctrine and specifically says "no --no-verify bypass" (copilot-instructions line 156), while judge doctrine treats hook changes as adversarial enforcement-infrastructure changes requiring a human-review gate (judge doctrine lines 96-100).

Fold an explicit policy into the FR: hook-free checkpoint commits are permitted only inside `.github/hooks/scripts/session-checkpoint.sh`, only on `refs/heads/session/*`, only after `git diff-index --quiet HEAD --` proves there is a tree change, and only with `Session-Id` and `Request-Index` trailers. Remove `--allow-empty-message`; the message is not empty. Add tests proving agent-issued `--no-verify` is still denied by `pre-command-guard` (FR-902 line 79), and add a human-review GATE for the hook/worktree enforcement diff before rollout.

### R-5: Make GC branch-namespace-safe and lossless

Replace the high-level GC sentence (FR-902 line 68) with a precise algorithm. It must enumerate only `session/*` branches/worktrees, refuse deletion when untracked files exist, refuse deletion when the branch contains unpushed or unmerged commits, and support a dry-run/list mode. Existing safe-removal logic hardcodes `feat/` branch names and `tmp/worktrees/feat/...` paths (worktree.sh lines 315-317), so the FR must authorize either prefix-aware `rm-safe` support or a session-specific safe remover with equivalent tests.

The "older than N days and identical to its merge-base" clause must define N, the merge base, the remote-push requirement, and the exact status printed when GC refuses deletion. A branch with any checkpoint not represented at the merge boundary must survive.

### R-6: Repair the research/evidence field and demote unsupported precision claims

The Research field says quantitative FR-898 evidence and a phase breakdown are "cited below" (FR-902 line 9), but the FR body contains no phase breakdown and no committed receipt for the `a7be91fc / 51 requests / 6,499 credits / 1,643 landed lines` claim (FR-902 lines 29, 95). Fold in a committed evidence artifact or an in-body table generated from `scripts/vscode/session_ledger.py --csv`, whose CSV contract is committed (session_ledger.py lines 1-14, 266-294).

Also revise "exact credits-per-line" (FR-902 line 72) to "turn/request-level provenance joined to changed files/commits" unless the FR adds a tested line-attribution algorithm. A commit can identify the turn that produced a tree delta; it does not by itself apportion credits to individual lines across subsequent edits.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/hooks/session-probe.json`: register the session-worktree command on `SessionStart` and the session-checkpoint command on `Stop`, ordered so briefing sees the lane path. |
| D-2 | `.github/hooks/scripts/session-worktree.sh`: stdin JSON parser, safe session-id validation, idempotent lane creation/adoption, lane-path output for briefing/guards. |
| D-3 | `.github/hooks/scripts/session-checkpoint.sh`: checkpoint-only commit logic, request-index lookup, duplicate-Stop idempotency, trailer emission, and explicit failure/audit behavior. |
| D-4 | `scripts/worktree.sh` or a shared helper under `scripts/`: reusable idempotent session-lane creation, no setup-only `.gitignore` diff, prefix-aware safe removal if reused for GC. |
| D-5 | `.github/hooks/scripts/pre-command-guard.sh` and tests, only as needed to enforce the session-ownership contract from R-1 without weakening FR-888 or other guards. |
| D-6 | `scripts/vscode/now.py`: list live session lanes and unmerged orphan `session/*` branches, preserving the existing flagged-not-deleted behavior. |
| D-7 | `scripts/vscode/session_ledger.py` or a small sibling join script: emit `request -> checkpoint commit -> credits` for one real session using the existing replayed CSV data. |
| D-8 | `.github/hooks/tests/` plus any required capability/requirement metadata: fixture tests for SessionStart, Stop, guard routing, GC refusal, ignored secrets, and join output. |
| D-9 | `feature-requests/FR-902-session-worktree-lifecycle.md`, `changelog/unreleased/`, and `docs/diary/`: fold this judgement, implementation status, changelog, and reflection. |

Not authorized: any change to judge/review doctrine or the sole-route adapters; any change to merge-boundary gates beyond tests proving they still apply; the cheap-model merge lane; rebuilding `ledger.py` on replayed `copilotCredits`; automatic deletion of branches with unmerged/unpushed checkpoint commits; broad changes to YAMLGraph runtime behavior; committing generated ledger reports or prompt-bearing CSVs.

## Revised acceptance criteria

- [ ] AC-01: `SessionStart` fixture feeds hook JSON on stdin; `session-worktree.sh` validates `session_id`, creates `tmp/worktrees/session/<full-session-id>` and branch `session/<full-session-id>`, provisions the same environment links as `scripts/worktree.sh`, emits the absolute lane path, and is a no-op on re-fire when branch and worktree match.
- [ ] AC-02: Session lane creation refuses path traversal, malformed ids, short-id collisions, branch-exists-with-wrong-worktree, and worktree-exists-with-wrong-branch cases with explicit non-success status/audit; it never deletes an existing `session/*` branch as recovery.
- [ ] AC-03: After a lane exists, write-tool and terminal write-shaped fixtures targeting this repo outside the owning session lane are denied with the lane path; the same writes inside the lane are allowed; read-only commands remain allowed; the audited escape hatch bypasses only the FR-902 session-lane denial class and no FR-888/Co-authored-by/`--no-verify` guard.
- [ ] AC-04: `Stop` fixture commits only when `git diff-index --quiet HEAD --` detects a tree change in the session lane; the commit message is `checkpoint(session): turn <N>` and trailers include exact `Session-Id` and `Request-Index`.
- [ ] AC-05: Duplicate `Stop` fixtures for the same request index create no second commit unless a later tree change exists; the test asserts the commit count and trailers.
- [ ] AC-06: Request-index derivation is tested against a replayed `chatSessions/*.jsonl` fixture or an explicitly documented hook payload field; a store-not-flushed case is surfaced as a bounded retry/skip-with-audit, not a fabricated index.
- [ ] AC-07: `.gitignore` is respected under checkpointing: `.env`, `.env.*`, `.venv`, `.venv/`, hook logs, and ignored `tmp/` artifacts are not staged; setup alone produces no checkpoint commit.
- [ ] AC-08: Checkpoint commits are confined to `session/*`; a squash-merge or equivalent fixture proves checkpoint commit subjects/trailers do not land on `main`, and existing `pre-command-guard` tests still deny agent-issued `--no-verify`.
- [ ] AC-09: GC dry-run/list mode reports live, merged, stale-clean, dirty, untracked, unpushed, and unmerged `session/*` lanes; prune mode deletes only merged or stale-clean lanes and refuses every loss-bearing case with a reason.
- [ ] AC-10: `now.py` lists live session lanes and unmerged orphan `session/*` branches with age, branch, worktree path, untracked count, and PR/open-branch status; it never deletes.
- [ ] AC-11: Join demo command emits a mechanically checkable table for a real session: request index, checkpoint commit SHA, model, credits, and prompt/summary availability status; the evidence source is committed or quoted in FR-902.
- [ ] AC-12: Hook tests live under `.github/hooks/tests/` and carry `@pytest.mark.req("REQ-YG-XXX")`; any new requirement/capability metadata needed for those tags is added consistently with ADR-001.
- [ ] AC-13: Human review of the hook/worktree enforcement diff is recorded before the policy is treated as live.
- [ ] AC-14: FR-902 contains the folded research/evidence table or receipt, the implementation record, changelog fragment, and diary reflection.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement from the current FR text until R-1 through R-6 are folded into `feature-requests/FR-902-session-worktree-lifecycle.md`; authority is revision-gated. | GATE |
| C-2 | No hook or guard rollout is treated as live policy until a human has reviewed the enforcement-infrastructure diff; judge doctrine requires human review for hook/CI/doctrine changes. | GATE |
| C-3 | No implementation may create, delete, or prune a session branch/worktree by shortening, guessing, or collision-prone session identifiers; validation and collision tests are mandatory. | GATE |
| C-4 | No implementation may use broad `git worktree remove --force` or `git branch -D` for automatic session cleanup; lossless safe-removal predicates must pass first. | GATE |
| C-5 | No implementation may weaken existing FR-888 main-write, Co-authored-by, `--no-verify`, branch-creation, authoring-route, diary, changelog, or merge-boundary gates. | GATE |
| C-6 | No prompt-bearing ledger CSV/report may be committed as a demo artifact; quote only the minimal non-sensitive rows required to prove the join. | GATE |

Authority granted: after the required revisions are folded, enforcement may build a session-scoped worktree lifecycle for this repository's Copilot hooks, with checkpoint commits on `session/*` branches, lossless GC, now.py visibility, and a turn-to-credit join; nothing outside the frozen surfaces is authorized.
