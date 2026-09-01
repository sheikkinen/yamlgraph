---
name: lan-delegate
description: "Submit ONE clean-committed workload from the mac to a FR-945-recon-verified LAN Windows host via WinRM+Copilot CLI, and return a typed diagnostic result plus artifacts. Use when: a workload would otherwise saturate the local iMac AND a fresh FR-945 recon of the target host shows admin=false + Remote Management Users membership + git + Node>=22 + Copilot CLI installed AND the local tree is clean-committed AND the pre-provisioned remote canonical clone contains the local HEAD SHA. Not a fleet manager; not a remote installer; not a bootstrap tool; not a resume/continuation channel. Refuses recursive delegation."
argument-hint: "target host + local prompt file + run ID, e.g. `--host Huutokauppakone.local --prompt-file tmp/analyze.md --run-id analyze-20260901T100000Z-abc1234`"
---

# LAN Copilot delegation skill (FR-948, REQ-YG-636)

Stateless per-run delegation of a Copilot CLI workload to a
FR-945-recon-verified LAN Windows host. Emits a Pydantic-validated
`LanDelegationResult` JSON document at
`tmp/lan/delegate/<safe-host-slug>/<run-id>.result.json` and returns
copied artifacts from a disposable per-run git worktree.

## Scope contract (frozen by FR-948 judgement C-1..C-7)

- **Stateless per invocation.** No `--resume`, no session continuation,
  no persistent worktree. Every run is one Copilot session against a
  fresh disposable detached worktree, then teardown.
- **Read-only on the mac side; workload-scoped on the remote side.**
  The mac never installs, fetches, clones, or provisions on the remote.
  The remote Copilot session runs under `--allow-all-tools` in one
  disposable worktree; `--allow-all-paths` is intentionally absent.
- **FR-945 recon is a hard precondition.** Refuses if the receipt file
  is missing, stale (> `RECON_MAX_AGE_MIN`, default 10 min), or shows
  `admin=true`, `remote_management_users_member=false`, or typed errors
  on the required fields.
- **Clean-committed local tree only.** `git status --porcelain` on the
  caller's cwd must be empty. Local HEAD SHA is recorded and must be
  present in the pre-provisioned remote canonical clone at
  `C:\Users\copilot\yamlgraph`. Uncommitted work is refused; source
  upload / fetch / clone is out of scope.
- **Recursive-delegation guard.** If `$YAMLGRAPH_LAN_DELEGATED == "1"`
  is set in the caller's environment, the skill refuses with a typed
  `RecursiveDelegationError` — an already-delegated Copilot session
  executes its workload locally in its own worktree and never re-invokes
  LAN delegation.
- **Wall-clock timeout is the sole preventive spend cap.** The wrapper
  owns a process-tree deadline (default 300 s) enforced by
  `taskkill /PID <root> /T /F` on expiry; the outer WSMan
  `operation_timeout` is set to `timeout + WSMAN_CLEANUP_MARGIN_S`.
  Reported credits are post-run diagnostics only.
- **Credential boundary.** `GH_TOKEN` from env is passed as a WinRM
  `param([string]$Token)` binding, never interpolated into the script
  literal. Literal token bytes are redacted from captured stdout/stderr
  **in memory** before any diagnostic file write, and every artifact
  is byte-scanned; a match records `TOKEN_LEAK_DETECTED` and skips
  the copy. Transformed/encoded token exfiltration is not prevented
  (dated human safety decision 2026-09-01).

## Invocation

```bash
# Reads:
#   .env: LAN_RECON_USER, LAN_RECON_PASS, GH_TOKEN
#   tmp/lan/<safe-host-slug>.json  (from FR-945 recon)
#   <prompt-file>                  (UTF-8, <= 32 KiB)
#
# Writes:
#   tmp/lan/delegate/<safe-host-slug>/<run-id>.result.json
#   tmp/lan/delegate/<safe-host-slug>/<run-id>.stdout.log  (redacted UTF-8)
#   tmp/lan/delegate/<safe-host-slug>/<run-id>.stderr.log  (redacted UTF-8)
#
# Remote side (disposable):
#   \\<host>\C$\Users\copilot\yamlgraph-runs\<run-id>   (detached worktree)
#   \\<host>\Images\yamlgraph-delegations\<run-id>\     (SMB artifact drop)

python .github/skills/lan-delegate/delegate.py \
    --host Huutokauppakone.local \
    --prompt-file tmp/analyze.md \
    --run-id analyze-$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)
# -> tmp/lan/delegate/huutokauppakone.local/<run-id>.result.json (LanDelegationResult)
```

## Refusal contract (partial; full list in delegate.py `PRE_LAUNCH_EXCEPTIONS`)

| Failure | Exception / status |
|---|---|
| `LAN_RECON_USER` / `LAN_RECON_PASS` / `GH_TOKEN` missing | `MissingCredentialError` |
| Local tree dirty | `DirtyLocalTreeError` |
| Recon receipt missing / stale / disqualifying | `MissingReconError` / `StaleReconError` / `ReconDisqualifyingFieldError` |
| Unsafe host / prompt-file / run-id | `UnsafeHostError` / `PromptFileError` / `UnsafeRunIdError` |
| Local path collision | `LocalPathCollisionError` |
| Already inside a delegated session | `RecursiveDelegationError` |
| Remote preflight failure (git / node < 22 / copilot / canonical clone / worktree / SMB) | `LanDelegationResult` with `delegation_policy_status=PREFLIGHT_FAIL` |
| Copilot exceeds wall-clock deadline | `LanDelegationResult` with `delegation_policy_status=TIMEOUT` (or `PROCESS_TREE_KILL_FAIL`) |
| Literal `GH_TOKEN` bytes found in a candidate artifact | `LanDelegationResult` with `delegation_policy_status=TOKEN_LEAK_DETECTED`; artifact not copied |

## Not this skill

- Fleet scheduling, load balancing, or picking a host from a pool.
- Installing / uninstalling / upgrading anything on the remote.
- Source transfer, `git fetch`, `git clone`, rsync of local work.
- Session continuation via `--resume`.
- Local fallback to non-delegated Copilot when the remote is down.
- Graph-level credit budgeting or spend gating.
- Wrapping FR-946 (LM Studio) or FR-945 (recon) invocations.
