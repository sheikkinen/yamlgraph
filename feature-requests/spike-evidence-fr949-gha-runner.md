# Spike evidence: FR-949 channel C — GHA self-hosted runner delegation

**Prior art:** [spike-evidence-fr948-copilot-remote.md](spike-evidence-fr948-copilot-remote.md) — channel A (WinRM push) spike for the same pain; this record is the channel C (pull/runner) counterpart, same evidence discipline. [FR-949-issue-queue-delegation.md](FR-949-issue-queue-delegation.md) — the judged channel B proposal this spike informs; the refit will fold this evidence into its alternatives table. [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md) — coexisting channel A; its credit-diagnostic and no-orphan contracts are re-tested here, not modified.

**Date:** 2026-09-01
**Spike target:** this iMac (`Sami-iMac`, macOS 26.3.1, x86_64) as the worker — chosen by operator to isolate the channel design from the WinRM comms issues the FR-948 enforcer was concurrently debugging. Channel shape is identical for a Windows worker; Windows-specific behavior remains to be witnessed there.
**Comms repo:** `sheikkinen/yamlgraph-delegation` (private, comms-only; labels `delegate`/`done`/`failed`; one workflow `.github/workflows/delegate.yml`)
**Runner:** actions-runner 2.337.0, registered as `imac-spike` via `gh api .../registration-token` (token used inline, never persisted); `./run.sh` foreground for the spike.

## Setup cost (measured)

Repo + labels + workflow + runner download/register/start: ~8 minutes wall clock, zero code beyond one 60-line workflow YAML. Compare: FR-949 channel B judgement priced a poller + state machine + heartbeat + chunk/retry machinery (24 ACs).

## Witness 1 — happy path (issue #1, run 33533557837)

Issue posted with `delegate` label → workflow triggered within seconds → job green in **26s**, end-to-end issue-to-closed ~40s:

- `claimed by Sami-iMac — run 33533557837 — 2026-09-01T16:44:08Z` comment posted.
- Copilot CLI ran the issue-body prompt; haiku posted back as issue comment.
- **Credits parseable from output**: `AI Credits 11.79 (5s)`, `Tokens ↑ 18.8k • ↓ 21` — FR-948's credit-diagnostic contract transfers unchanged.
- **C-3 credential scrub is one `env:` scope, not eight ACs**: `GH_TOKEN` given only to the `gh` steps; copilot step logged `scrub-ok: GH_TOKEN absent in copilot step` and exited 0 on its own ambient auth.
- Lifecycle: `delegate` removed → `done` added → issue CLOSED. All by `github-actions` with the job-scoped `github.token`; no PAT anywhere.

## Witness 2 — timeout (issue #2, run 33533677464)

Prompt instructed the agent to `sleep 600`; job `timeout-minutes: 3`.

- Job killed at exactly 3m0s (`The job has exceeded the maximum execution time of 3m0s`).
- `if: always()` post step **did** run after cancellation: failure comment posted, `delegate` removed, `failed` added, issue left OPEN — the retry-by-relabel contract works natively.
- **FINDING (the spike's paid lesson): the runner's cancellation kill is not a full process-tree kill.** `sleep 600` (PID 74329), a grandchild spawned by copilot's shell tool, **survived** the job cancellation and was killed manually. FR-948's no-orphan invariant is NOT free in channel C: the copilot step must run its child in a dedicated process group and a cleanup step (`if: always()`) must kill the group. R-6 survives in reduced form.
- Minor: the cancelled run's output comment was empty — stdout capture file existed but unflushed at kill time; capture should `tee` incrementally, not redirect-and-read.

## What the spike proves

| FR-949(B) judged contract | Channel C status |
|---|---|
| Queue + claim recovery (R-3) | GitHub-owned; lost runner fails the run visibly. Not our code. |
| Wall-clock cap | `timeout-minutes`, native, exact. |
| Heartbeat (R-7) | Runner online/offline via API/UI. Not our code. |
| Credential isolation (R-4/C-3) | Per-step `env:` scope; witnessed. One AC. |
| Output on issue (R-5) | `gh issue comment` in workflow steps; witnessed. Chunking still ours for >64KiB artifacts. |
| Credit diagnostics | Parseable from copilot output; witnessed. |
| No-orphan kill (R-6) | **NOT free** — process-group cleanup step required (witnessed orphan). |
| Label lifecycle + retry-by-relabel | Witnessed, including failure path. |

## Residual for the FR refit

1. Process-group kill cleanup step (the one piece of R-6 that survives).
2. Incremental output capture (`tee`) so timeout/failure comments carry partial output.
3. SHA-pinned checkout of the target repo (`sheikkinen/yamlgraph` read PAT as repo secret) — not exercised in this spike; the prompt was self-contained.
4. Windows worker witness (Huutokauppakone) — runner install + Copilot CLI under the runner service account.
5. Prompt-injection boundary: issue body went to copilot verbatim; author allowlist (CAP-109) must gate the workflow (`if: github.event.issue.author_association` / explicit login check).
