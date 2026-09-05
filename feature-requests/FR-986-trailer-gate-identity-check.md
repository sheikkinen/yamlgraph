# Feature Request: Reject Co-authored-by trailers by commit identity, not just trailer text (make the gate merge-blocking)

**Priority:** HIGH — the ban is doctrine (Scripture Commandment 6 context, `.github/hooks/README.md:76,135`), a CI job and a `commit-msg` hook both already exist, yet 241/2735 commits on `main` carry a real trailer, and 3 landed *after* the gate existed.
**Type:** Bug (detection gap) + Enforcement infrastructure
**Status:** Proposed
**Effort:** ~1 day
**Requested:** 2026-09-04
**First consumer / first event:** the `copilot-trailer-gate` CI job and `scripts/block_ai_coauthor.py` pre-commit hook, at the next PR whose branch carries a commit authored/committed under a mismatched identity (fixture email, bot workflow identity, or AI agent no-reply address) — today that check runs and passes even though the resulting squash commit on `main` will carry the trailer.
**Research:** in-body dispositioned alternatives table below (equivalent committed record; each entry carries a measured probe, not a rhetorical strawman — see Alternatives Considered).
**Prior art:**
- `terveystalo/customer-service-agent-platform` `feature-requests/NC-486-trailer-gate-ci-rejection.md` + `.judgement.md` (PR #334, merged 2026-09-04) — **the identical problem, independently discovered in a sibling repo the same day.** Judged APPROVED WITH REVISIONS; not yet implemented there either. This FR ports that design (shared typed detector, identity denylist, required-status-check activation) rather than reinventing it. Differs from NC-486 in one material way: yamlgraph already has a `copilot-trailer-gate` CI job and a `block_ai_coauthor.py` commit-msg hook (NC-486's repo had neither, only documentation claiming them) — so this FR is a *rewrite of existing text-only detectors to add identity checking*, not a from-scratch build.
- `.github/hooks/README.md:76,135` — documents the ban and names `copilot-trailer-gate` and `block-ai-coauthor` as the enforcers; this FR closes the gap between that claim and what the checks actually catch (`detection_without_enforcement`, `gate_checks_shape_not_substance`).
- `feature-requests/FR-385-*.md` / `FR-409-*.md` (superseded, not contradicted) — added the literal-trailer-text CI job and generalized its pattern from Copilot-only to any AI name. Both only ever matched trailer *text already present in a commit message*; neither checked commit author/committer identity, which is the actual mechanism GitHub uses to synthesize the trailer at squash time.

## Summary

`copilot-trailer-gate` (`.github/workflows/commitlint.yml`) and `block_ai_coauthor.py` (`.pre-commit-config.yaml`, `commit-msg` stage) both detect a `Co-authored-by:` trailer only if the literal text is already present in a commit message. Neither checks the commit's `author_email`/`committer_email`. GitHub's squash-merge synthesizes the trailer on `main` from the **distinct git identity of the source commit**, added at merge time — after both checks have already run and passed. The literal-text checks are structurally blind to this, and `copilot-trailer-gate` additionally is **not a required status check** (verified via `gh api repos/{owner}/{repo}/branches/main/protection` — only `commitlint`, `test (3.11)`, `test (3.13)` are required; `copilot-trailer-gate` can fail and the PR still merges).

## Problem

Measured on `main` at `722d3717` (HEAD), 2735 total commits:

| Scope | Commits | Commits w/ ≥1 trailer | Trailer lines | Identities |
|---|---|---|---|---|
| All of `main` | 2735 | **241** | 318 | 215 `Test <test@test.com>`, 89 `Copilot <223556219+Copilot@users.noreply.github.com>`, 11 `Sami J P Heikkinen <sami.j.p.heikkinen@gmail.com>` (own alt-email), 3 `recap-bot <recap-bot@users.noreply.github.com>` |
| Since the FR-409 gate landed (`d3192320^..722d3717`) | 1387 | **3** | 3 | all `recap-bot` (2026-08-18, -24, -31 — weekly recap PRs #473/#475/#542) |

The post-gate 3 are the proof this isn't merely historical debt: `.github/workflows/weekly-recap.yml:52-53` sets `git config user.name "recap-bot"` before committing, opens a PR, and the PR merges via squash. `recap-bot` never appears as literal trailer text in the source branch commit — GitHub adds it at squash time purely because the commit author differs from the merging actor. No regex over commit-message text, run at any point before merge, can see a trailer that does not yet exist. `block_ai_coauthor.py`'s pattern (`copilot|claude|chatgpt|gemini|gpt-?[0-9]+|github\s+copilot`) also would not have matched `recap-bot` even if it ran post-squash — the identity isn't on the AI-name list, it's a workflow bot, and the doctrine ban (`.github/hooks/README.md:76`) is stated as *all* Co-authored-by trailers, not only AI ones.

## Ideal Result

Every commit that reaches `main` with a `Co-authored-by:` trailer is one that a human explicitly reviewed and accepted at merge time — never a silent squash-merge artifact of an agent's fixture identity, a bot workflow's local git config, or an unreviewed AI no-reply address. The gate that enforces this is a required status check (merge-blocking, not advisory), and it checks the thing that actually determines the outcome — the source commits' author/committer identity within the PR range — not just text that may not exist yet at check time.

## Proposed Solution

Port NC-486's judged design (customer-service-agent-platform), adapted to reuse yamlgraph's existing enforcers instead of creating them from scratch:

1. **`scripts/ci/trailer_gate.py`** (new, shared): typed detector per NC-486's revised (post-judgement) shape —
   - `Commit` / `Violation` as `pydantic.BaseModel` with `ConfigDict(strict=True, extra="forbid")` — git output is external boundary data (Commandment 5).
   - `find_violations(commits: list[Commit]) -> list[Violation]` — pure, no I/O, unit-tested directly.
   - Three mutually exclusive CLI modes: `--range A..B` (CI, parses `git log --format=%H%x1f%ae%x1f%ce%x1f%B%x1e`), `--msg-file PATH` (commit-msg hook), `--pr-body` (stdin) — exactly one required, else exit 2.
   - Detects **both**: literal `^\s*co-authored-by:` trailer text (any identity — doctrine bans all, not only AI, pending Owner decision D-1 below) **and** a denylisted `author_email`/`committer_email` on the PR-range commits, which is the only channel that can catch a trailer before GitHub synthesizes it at squash.
   - Non-zero exit with a named failure class for git failure, bad range, or unreadable file — never a silent pass.

2. **`.github/workflows/commitlint.yml`**: replace the `copilot-trailer-gate` step's bash grep with a call to `trailer_gate.py --range "origin/${{ github.base_ref }}..HEAD"` (checkout already uses `fetch-depth: 0`... verify and add if missing) and a second `--pr-body` invocation for the PR body (unchanged trigger — `edited` is already in the `on.pull_request.types` list, so no R-2-equivalent fix is needed here).

3. **`.pre-commit-config.yaml` / `scripts/block_ai_coauthor.py`**: replace the narrow AI-name regex with a call into the shared `trailer_gate.py --msg-file`, so the local feedback hook and the CI gate agree on one detection surface instead of two independently-drifting patterns.

4. **Branch protection**: add `copilot-trailer-gate` to `required_status_checks.checks` via `gh api -X PUT repos/{owner}/{repo}/branches/main/protection/required_status_checks` (or the full protection PUT, preserving existing checks) — read-only `gh api .../branches/main/protection` output recorded in this FR showing the context present, closing the "visible but mergeable" gap.

## Owner-approved policy decisions (mirrors NC-486 D-1/D-2/D-5 — human decisions, not judge decisions)

| # | Decision | Approved |
|---|---|---|
| D-1 | Reject **all** `Co-authored-by` trailers, not only AI ones — matches `.github/hooks/README.md:76` ("Trailers in commits, merges, file writes") and NC-486's D-1. | _pending owner_ |
| D-2 | Identity denylist on author **and** committer email. Candidate patterns: `@test\.com$`, `Copilot@users\.noreply\.github\.com$`, `noreply@anthropic\.com$`. **Open question specific to this repo:** is `recap-bot@users.noreply.github.com` (a first-party scheduled workflow, not an AI agent) meant to be denylisted too, or should `weekly-recap.yml` instead commit as `github-actions[bot]` so no co-author credit is generated at all? | _pending owner_ |
| D-3 | Merged violations on `main` (241 commits) are **not** rewritten (force-push forbidden); they remain this FR's incident record, same as NC-486 D-3. | recorded |
| D-4 | Owner reviews the final detector, workflow, hook, and branch-protection diff before the required-status-check flip (adversarial enforcement input, same as NC-486 D-5). | _pending owner_ |

## Acceptance Criteria

- [ ] AC-01: **Behavioral RED** — new test module adds an importable typed skeleton (`find_violations` returning `[]`, models defined) and fails on assertions (expected violations not yet returned by the old text-only logic); not an import error.
- [ ] AC-02: `trailer_gate.py --range d3192320^..722d3717` (pinned) reports exactly the 3 `recap-bot` violations by identity, proving the new detector catches what the current text-only gate misses on a real, already-merged range.
- [ ] AC-03: identity denylist patterns from D-2 are covered by unit tests (each pattern: one matching fixture, one near-miss that must NOT match).
- [ ] AC-04: `copilot-trailer-gate` present in `gh api repos/{owner}/{repo}/branches/main/protection` → `required_status_checks.checks`; output recorded in this FR.
- [ ] AC-05: `.pre-commit-config.yaml`'s `block-ai-coauthor` hook and the CI job both invoke the same `trailer_gate.py`; config witness test asserts hook id, `commit-msg` stage, exact entry, and the CI job step command.
- [ ] AC-06: Owner has approved D-1, D-2, and D-4 (dated in the table above) before the required-status-check flip is applied.
- [ ] AC-07: `capabilities/CAP-148-ci-copilot-trailer-gate.yaml` and `ARCHITECTURE.md` updated to describe identity-based detection; tests carry `@pytest.mark.req(...)`.
- [ ] AC-08: changelog fragment in `changelog/unreleased/`; diary entry naming the cross-repo-simultaneous-discovery insight.

## Alternatives Considered

*(Probed, not rhetorical — each row below is a measured or verified fact, not a strawman.)*

| Alternative | Probe | Disposition |
|---|---|---|
| Do nothing — rely on the existing `copilot-trailer-gate` + `block_ai_coauthor.py` | Verified both are literal-text-only (read `commitlint.yml`, `scripts/block_ai_coauthor.py`); verified `copilot-trailer-gate` is absent from `required_status_checks.checks` via `gh api`; verified 3 `recap-bot` violations landed *after* both existed. | Rejected — measured to already be failing. |
| Disable GitHub's squash-merge co-author auto-crediting via repo setting | Checked `gh api repos/{owner}/{repo}` — only `squash_merge_commit_message` (`COMMIT_MESSAGES`/`PR_BODY`/`BLANK`) and `squash_merge_commit_title` exist; no field controls co-author trailer synthesis. | Rejected — not a configurable surface; GitHub's behavior is structural. |
| Rewrite `main` history to strip existing trailers | Forbidden by operational-safety doctrine (no force-push/rewrite of shared `main` without explicit confirmation); NC-486 D-3 makes the same call independently. | Rejected — 241 commits become the incident record, not a rewrite target. |
| Fix only the local `commit-msg` hook, skip CI | The `recap-bot` commit's own local commit message never contains the trailer text — the hook running locally, even with a perfect regex, cannot see an identity-based violation that GitHub synthesizes later at squash. | Rejected — identity checking must run in CI against the PR range, where the source identity is still visible. |
| Port NC-486's typed detector + identity denylist + required-status-check activation | Same root cause, already judged APPROVED WITH REVISIONS in a sibling repo the same day; reuses a vetted design instead of re-deriving one. | **Chosen.** |

## Related

- `.github/workflows/commitlint.yml` (`copilot-trailer-gate` job)
- `.pre-commit-config.yaml` (`block-ai-coauthor` hook), `scripts/block_ai_coauthor.py`
- `.github/hooks/scripts/pre-command-guard.sh:182-186` (PreToolUse denial message already promises these controls)
- `capabilities/CAP-148-ci-copilot-trailer-gate.yaml`
- `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`, `tests/unit/test_fr409_ci_coauthored_by_gate_generalization_red.py` (existing text-only test coverage to extend/supersede)
- `.github/workflows/weekly-recap.yml:52-53` (source of the 3 post-gate violations)
- `terveystalo/customer-service-agent-platform` PR #334, `feature-requests/NC-486-trailer-gate-ci-rejection.md` + `.judgement.md` (sibling-repo precedent, same-day discovery)
