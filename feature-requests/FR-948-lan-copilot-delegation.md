# Feature Request: LAN Copilot-CLI delegation channel (supersedes FR-947)

**Priority:** HIGH
**Type:** Feature (with subtractionist scope: retires FR-947)
**Status:** Proposed (revised 2026-09-01 to fold judgement R-1..R-5 from re-judgement)
**Effort:** 3 days
**Requested:** 2026-09-01
**First consumer / first event:** an agent that has verified FR-945 recon (with `admin=False` and `remote_management_users_member=True`) invokes `.github/skills/lan-delegate/` with a clean-committed local SHA and a local prompt file, and gets back a validated diagnostic result recording exit code, delegation-policy status, timeout state, matched local/remote SHA, parsed reported credits, run ID, artifact root, and typed errors. **First event:** the next attempt to run heavy work (e.g. the repository's `run-code-analysis` skill invoked over the delegation channel) that would otherwise saturate the iMac. Sanitized spike record: [FR-948-spike-evidence.md](FR-948-spike-evidence.md).
**Research:** [FR-948.research.md](FR-948.research.md) (persona-shaped record; the substantive alternatives table below in § R-1 is the FR-body disposition the judge required.)
**Prior art:**
- [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) [Proposed, superseded by this FR] — SSH+WSL2+pytest-xdist design. Retired via subtractionist path in the same commit as lifecycle bookkeeping.
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) [Proposed] — the read-only WinRM inventory foundation this FR consumes as a precondition. No schema amendment under FR-948 authority.
- [FR-945.research.md](FR-945.research.md) — retrieval hit. Substantively unrelated to FR-948's channel design; distinguished (research artifact for a different FR).
- [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md) [Proposed] — orthogonal (LM Studio inference channel, different tool, different auth).
- [FR-766-runpod-provider.md](FR-766-runpod-provider.md) [Judged] — remote-inference to cloud. Distinguished: FR-948 is LAN, WinRM, not HTTPS-inference.
- [FR-899-org-repo-census-azure.md](FR-899-org-repo-census-azure.md) [Implemented] and [FR-899-org-repo-census-azure.judgement.md](FR-899-org-repo-census-azure.judgement.md) — retrieval hits on shared nouns; unrelated (Azure DevOps census). Dismissed.
- [CAP-30-copilot-node.yaml](../capabilities/CAP-30-copilot-node.yaml) — precedent for local Copilot invocation. **Not modified** by FR-948 (out of scope per judgement C-8).
- [CAP-249-tool-slot-binding.yaml](../capabilities/CAP-249-tool-slot-binding.yaml) — research-vocabulary noise, unrelated. Dismissed.

## Summary

A `.github/skills/lan-delegate/` skill that submits one clean-committed workload from the mac to a FR-945-verified LAN host over an already-hardened WinRM transport, runs it inside a disposable per-run detached git worktree with a **wrapper-owned process-tree deadline**, returns a Pydantic-typed diagnostic result plus artifacts via SMB, and refuses to launch a recursive delegation from within a delegated Copilot session. **Strategic classification: contrib/example, not framework primitive.** This is one host, one immediate channel, reusing existing skill convention + Copilot CLI precedent + FR-945 transport.

## Value Statement

Agents move heavy workloads off the saturated iMac onto Huutokauppakone via an empirically-verified, code-identity-frozen, recursion-guarded channel — bounded by a wrapper-enforced wall-clock deadline, with byte-scanned credential redaction and exact-artifact isolation.

## Problem

- iMac freezes under concurrent full workloads (operator report 2026-09-01).
- FR-947's SSH+WSL2+pytest-xdist design unimplemented and superseded by the empirical WinRM+Copilot channel (spike evidence in [FR-948-spike-evidence.md](FR-948-spike-evidence.md)).
- No existing repo capability wraps the "WinRM → disposable worktree → Copilot skill invocation → SMB artifacts" pattern; each future delegation would reinvent it.

## Ideal Result

`python .github/skills/lan-delegate/delegate.py --host Huutokauppakone.local --prompt-file tmp/prompt.md --run-id <utc-plus-sha>` against a clean-committed tree refuses non-zero and actionable on any precondition failure. On success: one Copilot session runs against a per-run detached worktree, tracked by the wrapper with a hard deadline; outputs drop into that worktree's `.delegate-out/`; the wrapper (never the model) byte-scans candidates for the token and copies clean ones to `\\<host>\Images\yamlgraph-delegations\<run-id>\`. Result includes `local_sha == remote_sha` proof, credit diagnostics, wrapper deadline state, and typed errors. `GH_TOKEN` bytes appear nowhere across success + every failure path.

## Proposed Solution

### R-1 Alternatives evaluated (unchanged from prior fold; retained)

| # | Solution class | Verdict | Preserved dissent |
|---|---|---|---|
| A | **WinRM + Copilot CLI, stateless, wrapper-deadline, disposable worktree** | **Chosen (v1)** | Reuses FR-945 transport; skill contract via `--add-dir`; empirical spike; wall-clock cap via wrapper process-tree kill. |
| B | WinRM + deterministic PowerShell RCE (no LLM) | Rejected | Loses skill contract; only rigid workloads. Retain as fallback consideration. |
| C | FR-947 SSH+WSL2+pytest-xdist | Rejected (retired same commit) | Unimplemented; days of infra; assumption disproven by spike. |
| D | Self-hosted GHA runner | Rejected v1 | Widens secret exposure to LAN Windows box. Revisit if v1 <90% delegation success in month 1. |
| E | CI-only (subtractionist counterpart) | Documented escape | Operator explicitly rejected retiring local workflow. |

This delegation channel is **not a graph** — graphs *consume* its output; the channel itself is a process boundary. `.github/skills/lan-delegate/` is one skill in an external-method category.

### 2. Dependency

`pypsrp>=0.9,<1.0` (matches FR-945's actual pin in [pyproject.toml](../pyproject.toml)). No new Python deps. Remote-side (git, node ≥ 22, `@github/copilot`) are FR-948 preconditions **verified by the remote preflight in § 5, not installed by this FR**.

### 3. R-1 & R-3 Input boundary contract for `delegate.py`

`delegate.py --host TARGET --prompt-file PATH --run-id RUN_ID [--max-reported-credits N] [--timeout SEC]`:

1. **Local-tree freeze**: refuse if `git status --porcelain` on caller cwd is non-empty. Record `local_sha` = `git rev-parse HEAD`.
2. **FR-945 receipt validation**: load `tmp/lan/<slug>.json`. Refuse if absent or `probe_ended_at` older than `RECON_MAX_AGE_MIN` (default 10 min). Validate ONLY the fields FR-945 actually emits: `resolved_address`, `computer_name`, `probe_started_at`, `probe_ended_at`, `admin==False`, `remote_management_users_member==True`, and typed `errors` marking those fields.
3. **Prompt boundary**: `--prompt-file` must exist locally, be UTF-8, ≤ 32 KiB. Read locally; pass as WinRM `param([string]$Prompt)` binding.
4. **Run ID**: match `^[A-Za-z0-9._-]+$`, ≤ 64 chars.
5. **Pre-WinRM local-path collision refusals** (added per R-3): refuse if `tmp/lan/delegate/<host-slug>/<run-id>.result.json` or `.stdout.log` or `.stderr.log` already exists.
6. **Remote paths** (derived): canonical clone `C:\Users\copilot\yamlgraph`; per-run worktree `C:\Users\copilot\yamlgraph-runs\<run-id>`; artifact drop `\\<host>\Images\yamlgraph-delegations\<run-id>\`.
7. **Recursive-delegation guard** (R-5): refuse with typed `RecursiveDelegationError` if `os.environ.get("YAMLGRAPH_LAN_DELEGATED") == "1"` — an already-delegated Copilot session may execute the workload locally in its worktree, but must never re-invoke LAN delegation from itself.
8. **Credential**: `GH_TOKEN` from env (single canonical name). Passed as `param([string]$Token)`. Wrapper clears `$env:GH_TOKEN` in `finally`.
9. **`--timeout SEC` (default 300)**: the **wrapper-owned process-tree deadline** (see § 5). The outer WSMan `operation_timeout` is set to `timeout_s + WSMAN_CLEANUP_MARGIN_S` (default 60 s cleanup margin) — that outer bound is transport-failure protection, **not** the preventive spend cap.
10. **`--max-reported-credits N` (default 60)**: post-run acceptance threshold. Missing/malformed/over-threshold credit output → `credit_status` non-`OK`, CLI non-zero, artifacts preserved.
11. **No `--resume`** in v1 CLI at all.

### 4. Pre-launch exception classes (R-1)

Enumerated typed classes raised by `delegate.py` **before** WinRM connect or when preflight refuses:

- `DirtyLocalTreeError` — local `git status --porcelain` non-empty.
- `MissingReconError` — FR-945 receipt file absent.
- `StaleReconError` — receipt older than `RECON_MAX_AGE_MIN`.
- `ReconDisqualifyingFieldError` — `admin=True`, `remote_management_users_member=False`, or typed `errors` on receipt-relevant fields.
- `MissingCredentialError` — `GH_TOKEN` unset or empty.
- `PromptFileError(reason: "missing" | "not_utf8" | "too_large")`.
- `UnsafeRunIdError`.
- `LocalPathCollisionError(path: str)`.
- `RecursiveDelegationError`.

**Pre-launch failures raise these typed exceptions; no `LanDelegationResult` is produced. CLI status non-zero + actionable stderr.**

### 5. R-2 Transport, deadline, and remote wrapper contract

Transport (from FR-945):
- HTTP 5985 + `auth="negotiate"` + `encryption="always"` (asserted in tests).
- Basic + CredSSP explicitly banned; enum-checked.
- Pinned resolved address from FR-945 (no re-resolution downstream).
- Outer WSMan `operation_timeout` = `timeout_s + WSMAN_CLEANUP_MARGIN_S`.

Wrapper `wrapper.ps1` (fixed, committed, ASCII, no interpolation of caller-controlled text; `param([string]$Token, [string]$Prompt, [string]$RunId, [int]$TimeoutS, [string]$LocalSha)`):

1. `chcp 65001`; `Set-ExecutionPolicy Bypass -Scope Process -Force`.
2. `try { ... } finally { Remove-Item Env:GH_TOKEN -EA SilentlyContinue }`.
3. **Remote preflight** (non-LLM): emit `RemoteCopilotPrerequisites` (§ 6 schema) — refuse each typed failure before worktree add.
4. **Collision guards** (R-3): refuse if `Test-Path $worktreePath` OR `Test-Path $smbDest`. Do NOT enumerate or copy into a pre-existing destination.
5. **Worktree create** (typed status on failure): `git -C C:\Users\copilot\yamlgraph worktree add --detach $worktreePath $LocalSha`. On failure emit `WORKTREE_ADD_FAIL` + typed error.
6. **remote_sha capture** (R-1): `git -C $worktreePath rev-parse HEAD` → `$remoteSha`. Assert `$remoteSha -eq $LocalSha` in the emitted result.
7. **Output dir** (typed status): `New-Item -ItemType Directory -Path "$worktreePath\.delegate-out"`. On failure `OUTPUT_DIR_CREATE_FAIL`.
8. **Wrapper-owned deadline** (R-2, core):
   ```powershell
   $env:GH_TOKEN = $Token
   $env:COPILOT_ALLOW_ALL = '1'
   $env:YAMLGRAPH_LAN_DELEGATED = '1'   # recursive-delegation marker (R-5)
   $proc = Start-Process 'C:\Program Files\nodejs\copilot.cmd' `
       -ArgumentList @('-p', $Prompt, '--allow-all-tools', '--add-dir', $worktreePath) `
       -RedirectStandardOutput $stdout `
       -RedirectStandardError  $stderr `
       -NoNewWindow -PassThru
   $ok = $proc.WaitForExit($TimeoutS * 1000)
   if (-not $ok) {
       # Kill the FULL process tree, not just copilot.cmd.
       Get-CimInstance Win32_Process -Filter "ParentProcessId=$($proc.Id)" | ForEach-Object {
           try { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } catch {}
       }
       try { Stop-Process -Id $proc.Id -Force -EA SilentlyContinue } catch {}
       $status = 'TIMEOUT'; $timedOut = $true
   } else {
       $status = if ($proc.ExitCode -eq 0) { 'OK' } else { 'COPILOT_NONZERO' }
       $timedOut = $false
   }
   ```
9. **Byte-level token scan on artifacts** (R-4): for every file rooted beneath `$worktreePath\.delegate-out`, read raw bytes; if `$Token` byte sequence is present, do NOT copy, record `TOKEN_LEAK_DETECTED` + the file path, mark overall status `TOKEN_LEAK_DETECTED` and CLI non-zero.
10. **Redact stdout/stderr** before persistence: literal `$Token` bytes removed from both streams before write to `$stdout`/`$stderr` log files.
11. **Copy clean artifacts** ONLY from `$worktreePath\.delegate-out`; enumerate the SMB destination (never a global mtime diff).
12. **Cleanup** (typed status on failure): `git -C C:\Users\copilot\yamlgraph worktree remove --force $worktreePath`. On failure `WORKTREE_CLEANUP_FAIL`.
13. Emit one JSON summary (redacted). `finally` clears `$env:GH_TOKEN`.

**Truthful containment language** (R-4): `--allow-all-tools` allows any child tool spawned by Copilot to act with `copilot`-user privileges. Omitting `--allow-all-paths` restricts Copilot's OWN file access to the `--add-dir` root, but a tool it spawns (shell, git, node) can access anything under `copilot`'s account. The `.delegate-out` scope means only files rooted there are **eligible for copying and result attribution**; it is not a filesystem sandbox. Transformed/encoded token exfiltration is not prevented; byte-scan defends against literal-value leaks only. Dated human safety decision (below) acknowledges this envelope.

### 6. Schema tables (R-1 complete)

`ToolInfo`:

| Field | Type | Notes |
|---|---|---|
| `present` | `bool` | `Get-Command <tool>` returned a value |
| `path` | `str \| None` | absolute path, or None if absent |
| `version` | `str \| None` | parsed version string, or None |
| `error` | `FieldError \| None` | typed error if probe failed |

`RepoInfo`:

| Field | Type | Notes |
|---|---|---|
| `path` | `str` | `C:\Users\copilot\yamlgraph` |
| `exists` | `bool` | directory + `.git` present |
| `contains_sha` | `bool \| None` | `git cat-file -e <local_sha>` result, or None if `exists=False` |
| `error` | `FieldError \| None` | typed error if probe failed |

`RemoteCopilotPrerequisites`:

| Field | Type | Notes |
|---|---|---|
| `git` | `ToolInfo` | must be present |
| `node` | `ToolInfo` | version major ≥ 22 |
| `copilot` | `ToolInfo` | path under `C:\Program Files\nodejs\copilot.cmd` |
| `canonical_clone` | `RepoInfo` | `contains_sha` must be True |
| `run_worktree_free` | `bool` | `Test-Path $worktreePath` is False |
| `smb_destination_free` | `bool` | `Test-Path $smbDest` is False |
| `errors` | `list[FieldError]` | any typed errors from probes |

`FieldError`:

| Field | Type | Notes |
|---|---|---|
| `field` | `str` | dotted path in the containing object |
| `message` | `str` | human-readable |
| `error_type` | `Literal["absent","malformed","version_too_low","path_taken","access_denied","probe_timeout","unknown"]` | closed enum |

`DelegationPolicyStatus` (closed enum, R-3):

`OK`, `PREFLIGHT_FAIL`, `WORKTREE_ADD_FAIL`, `OUTPUT_DIR_CREATE_FAIL`, `WRAPPER_EXEC_FAIL`, `COPILOT_NONZERO`, `TIMEOUT`, `CREDIT_FAIL_HIGH`, `CREDIT_FAIL_UNPARSEABLE`, `WRAPPER_JSON_MALFORMED`, `ARTIFACT_COPY_FAIL`, `WORKTREE_CLEANUP_FAIL`, `TOKEN_LEAK_DETECTED`, `SMB_DEST_EXISTS`.

**Precedence on multiple failures** (R-3): `TOKEN_LEAK_DETECTED` > `WRAPPER_JSON_MALFORMED` > `TIMEOUT` > `WORKTREE_ADD_FAIL` > `OUTPUT_DIR_CREATE_FAIL` > `WRAPPER_EXEC_FAIL` > `SMB_DEST_EXISTS` > `COPILOT_NONZERO` > `CREDIT_FAIL_HIGH` > `CREDIT_FAIL_UNPARSEABLE` > `ARTIFACT_COPY_FAIL` > `WORKTREE_CLEANUP_FAIL` > `OK`. The highest-severity status observed is the recorded `delegation_policy_status`; others surface in `errors`.

`LanDelegationRequest`:

| Field | Type | Notes |
|---|---|---|
| `host` | `str` | mDNS name; matched to receipt |
| `prompt_file` | `Path` | validated locally |
| `run_id` | `str` | slug |
| `max_reported_credits` | `float` | default 60 |
| `timeout_s` | `int` | wrapper deadline (default 300) |
| `local_sha` | `str` | frozen at request time |
| `local_clean` | `bool` | must be True |

`LanDelegationResult` (produced only if WinRM connection was attempted; pre-launch typed exceptions produce **no** result):

| Field | Type | Notes |
|---|---|---|
| `request` | `LanDelegationRequest` | echo |
| `host_resolved_address` | `IPvAnyAddress` | from FR-945 receipt |
| `remote_computer_name` | `str` | from FR-945 receipt |
| `prerequisites` | `RemoteCopilotPrerequisites \| None` | **None only if `delegation_policy_status == WRAPPER_JSON_MALFORMED`** — otherwise required (R-1) |
| `local_sha` | `str` | echo |
| `remote_sha` | `str \| None` | `git rev-parse HEAD` in run worktree; None if worktree never created |
| `sha_matched` | `bool` | `remote_sha == local_sha` — must be True for `delegation_policy_status == OK` |
| `remote_worktree` | `str \| None` | run worktree path; None if never created |
| `copilot_exit_code` | `int \| None` | None if Copilot never invoked |
| `delegation_policy_status` | `DelegationPolicyStatus` | required, closed enum |
| `timed_out` | `bool` | required |
| `elapsed_s` | `float` | required (wall clock: WinRM connect → summary emit) |
| `credits_reported` | `float \| None` | parsed |
| `credit_status` | `Literal["OK","FAIL_HIGH","FAIL_UNPARSEABLE","NOT_APPLICABLE"]` | required |
| `tokens_up` | `int \| None` | parsed |
| `tokens_down` | `int \| None` | parsed |
| `artifacts` | `list[Path]` | files that passed byte-scan and were copied to SMB drop |
| `stdout_path` | `Path` | redacted UTF-8 log |
| `stderr_path` | `Path` | redacted UTF-8 log |
| `errors` | `list[FieldError]` | all typed errors observed across phases |

### 7. Test list (offline; no real DNS, socket, WinRM, SMB, or Copilot)

`tests/unit/test_lan_delegate.py` covers:

- All pre-launch exception classes (§ 4), each with actionable stderr + CLI non-zero.
- Client construction: `auth="negotiate"`, `encryption="always"`, `ssl=False`, `port=5985`, pinned resolved address, `operation_timeout == timeout_s + WSMAN_CLEANUP_MARGIN_S`.
- Prompt-passing: WinRM script text captured; prompt string absent from literal, present only in `param` binding.
- Copilot invocation flags: `--allow-all-tools --add-dir <run-worktree>` (root), NO `--allow-all-paths`, `YAMLGRAPH_LAN_DELEGATED=1` in child env.
- Each `RemoteCopilotPrerequisites` field: git absent / node major < 22 / copilot absent / canonical clone missing / `contains_sha=False` / worktree path taken / SMB destination taken → typed refusal.
- Every `DelegationPolicyStatus` value has a mocked witness. Precedence rule: multi-failure fixture asserts the highest-severity status wins.
- Wrapper contains no install/fetch/clone/SSH/WSL/service/policy/firewall/group mutation (regex scan on committed `wrapper.ps1`).
- `remote_sha` capture + `sha_matched` assertion; mismatch fixture → `sha_matched=False` and status non-`OK`.
- Byte-scan: fixture with token bytes appearing in an artifact → not copied, `TOKEN_LEAK_DETECTED`.
- Redaction: stdout/stderr fixture containing token bytes → written logs contain zero token-byte occurrences.
- Recursive-delegation guard: mock `YAMLGRAPH_LAN_DELEGATED=1` in test env → `RecursiveDelegationError` before receipt loading or WinRM.
- Two mocked concurrent runs with distinct `run-id`s → each attributes only its own artifacts (isolation invariant).
- Argparse: `--resume` sent → argparse error.

### 8. Live witnesses (R-2 + R-5)

Two real Huutokauppakone runs recorded in this FR body once implementation lands. No credential material.

**AC-18 timeout witness**: `delegate.py --host Huutokauppakone.local --prompt-file tmp/hang.md --run-id timeout-<utc>-<sha> --timeout 5` where `tmp/hang.md` contains a prompt that would run for well over 5 s (e.g. "sleep 60 then reply"). Records: CLI non-zero, `timed_out=True`, `delegation_policy_status=TIMEOUT`, `remote_sha=local_sha` (worktree WAS created before deadline), no surviving `copilot.exe` process on remote (verified via a follow-up WinRM query), no surviving run worktree, no literal token in `stdout_path`/`stderr_path`/`artifacts`.

**AC-19 skill-loading witness**: `delegate.py --host Huutokauppakone.local --prompt-file tmp/analyze.md --run-id analyze-<utc>-<sha>` where `tmp/analyze.md` invokes the repository's [run-code-analysis skill](../.github/skills/run-code-analysis/SKILL.md) via natural language ("Use the run-code-analysis skill to produce a bounded code-quality summary of yamlgraph/utils/llm_factory.py and drop the result to .delegate-out/analysis.md"). Records: matched `local_sha == remote_sha`, `delegation_policy_status=OK`, credit report parsed, observable Copilot output naming the selected skill (parsed from stdout), artifact `.delegate-out/analysis.md` shape specific to `run-code-analysis` (not just a shell command echo). Proves the `--add-dir` skill-loading path that the spike did not exercise.

### 9. Governance (§ R-6 from prior fold, retained; scope frozen to D-1..D-8 per judgement)

- New `capabilities/CAP-257-lan-copilot-delegation.yaml` + new `REQ-YG-636`. Registers all D-1 surfaces. Strict `req_coverage` passes. Generated `ARCHITECTURE.md` section committed.
- Two changelog fragments: `changelog/unreleased/fr-948-lan-copilot-delegation.md` (feat) and `changelog/unreleased/fr-948-retire-fr947.md` (removal).
- Diary reflection `docs/diary/2026-09-XX-fr948-copilot-delegation.md` covering the empirical-spike-drives-design pattern, the FR-945 pypsrp-pin composition catch, the WinRM-operation-timeout misconception (`operation_timeout ≠ process termination`), and the recursive-delegation-guard insight.
- `reference/development-operations.md` gains LAN Copilot delegation subsection.
- `.env.sample` gains commented `GH_TOKEN=`.
- FR-947 supersession header retained (added in commit `9c579924`).
- **Not modified**: CAP-30, YAMLGraph Copilot node, hooks, CI, judge/review doctrine, Chaplain, FR-945 schema/implementation.

## Dated human decisions (2026-09-01, retained from prior fold)

**Q1 safety — R-4 in prior fold**: authorize `--allow-all-tools` + live `GH_TOKEN` on Huutokauppakone constrained to disposable per-run worktree with the token's minimum permissions / scope / rotation / revocation in the FR?

**Answered 2026-09-01: YES ("yolo").** Constraint envelope: per-run disposable git worktree, non-admin `copilot` account, WinRM Negotiate mandatory-encryption, home LAN, single physical operator. Token: whatever `gh auth token` on mac returns. No formal expiry/rotation policy for v1; revocation = GitHub Settings → Developer settings then re-run `gh auth login`. The `--allow-all-tools` boundary IS understood to mean: any tool Copilot spawns runs with `copilot`-user privileges and can read `$env:GH_TOKEN` until the wrapper's `finally` clears it. Byte-scan on artifacts + redaction of stdout/stderr are defense in depth, NOT proof of impossibility. **Transformed/encoded token exfiltration is not prevented** (explicit acknowledgement per judgement R-4).

**Q2 spend — R-5 in prior fold**: accept post-run-only spend detection; no hard credit cap?

**Answered 2026-09-01: YES (acceptable). "We'll operate this via copilot nodes / yamlgraph — timeout is the cap."** The preventive cap is the **wrapper-owned process-tree deadline** (§ 5 step 8). Wall-clock exhaustion terminates the tracked process and its children on the remote (proven by AC-18 witness against Huutokauppakone). Reported credits are diagnostic evidence, not a preventive budget. FR-948 does not add graph-level spend gating; that's a future capability yamlgraph copilot nodes can provide on top.

## Acceptance Criteria (20, per judge's revised list)

- [ ] **AC-01** FR retains 5 solution classes (§ R-1) with preserved disagreement; every retrieval hit dispositioned in "Prior art"; the reconciled "not a graph; consumed by graphs" answer; **contrib/example** strategic classification recorded.
- [ ] **AC-02** Every spike-attributed claim is bounded by `FR-948-spike-evidence.md:79-99`. FR does NOT attribute repository workload, timeout termination, Python provisioning, or `--add-dir` skill loading to the spike.
- [ ] **AC-03** FR-945 is a precondition ONLY; consumes committed receipt fields; reuses `pypsrp>=0.9,<1.0`; does not modify FR-945.
- [ ] **AC-04** `LanDelegationRequest`, `ToolInfo`, `RepoInfo`, `RemoteCopilotPrerequisites`, `LanDelegationResult`, `FieldError`, `DelegationPolicyStatus`, and all named pre-launch exception classes (§ 4) are completely specified and Pydantic-implemented; no untyped boundary.
- [ ] **AC-05** Local validation refuses missing/stale/disqualifying receipt, missing `GH_TOKEN`, dirty tree, invalid host/run ID, unsafe/colliding local paths, missing/non-UTF-8/oversized prompt BEFORE DNS/WinRM/file write.
- [ ] **AC-06** Remote preflight verifies git present, node major ≥ 22, copilot CLI + version parseable, canonical clone `contains_sha=True`, `run_worktree_free=True`, `smb_destination_free=True` — before worktree create or Copilot invocation.
- [ ] **AC-07** Successful run records `local_sha` and independently reads `remote_sha` from the detached run worktree; Pydantic model + tests require exact equality (`sha_matched=True`) for `delegation_policy_status=OK`.
- [ ] **AC-08** Client construction uses FR-945 pinned address with exact `auth="negotiate"`, `encryption="always"`, `ssl=False`, `port=5985`, finite `connection_timeout`, and `operation_timeout == timeout_s + WSMAN_CLEANUP_MARGIN_S`. Basic + CredSSP + downstream DNS re-resolution are absent.
- [ ] **AC-09** Prompt + token cross WinRM only through bound parameters; absent from script literals. Copilot invoked with `--allow-all-tools --add-dir <run-worktree>`; `--allow-all-paths` absent.
- [ ] **AC-10** Wrapper owns a process deadline shorter than the outer WSMan timeout, kills the tracked process tree on expiry, executes cleanup (worktree remove + token clear), returns validated `TIMEOUT` result.
- [ ] **AC-11** Only files rooted beneath the new run's `.delegate-out` are eligible for SMB copy; SMB destination must be absent before launch; two concurrent runs + a stale-destination case prove exact attribution.
- [ ] **AC-12** Byte-level scan of every candidate artifact for exact `GH_TOKEN` bytes; on match: skip, record typed `TOKEN_LEAK_DETECTED`, non-zero CLI. stdout/stderr redacted BEFORE persistence. FR retains dated human acknowledgement that transformed/encoded exfiltration is not prevented.
- [ ] **AC-13** Every post-WinRM failure phase has a typed `DelegationPolicyStatus`, deterministic precedence (§ 6), non-zero CLI, validated `LanDelegationResult`; malformed wrapper output alone permits `prerequisites=None`.
- [ ] **AC-14** Reported credits are post-run diagnostics only; missing/malformed/over-threshold → policy fail while preserving non-secret artifacts; no hard-cap or bounded-cost claim.
- [ ] **AC-15** v1 has NO `--resume`, source transfer, fetch, clone, installation, service/policy/firewall/group mutation, fleet abstraction, local fallback, or graph-level budget. Committed-source regex scan enforces the forbidden wrapper operations.
- [ ] **AC-16** Wrapper propagates `YAMLGRAPH_LAN_DELEGATED=1` in Copilot child env; both `delegate.py` and `SKILL.md` refuse recursive LAN delegation; offline tests prove refusal occurs before receipt loading or WinRM.
- [ ] **AC-17** Offline tests cover ALL input, transport, preflight, lifecycle, status-precedence, redaction, timeout, collision, concurrency, cleanup, and recursion seams — without real DNS, socket, WinRM, SMB, or Copilot.
- [ ] **AC-18** Real short-timeout Huutokauppakone run proves process-tree termination, no remaining run worktree, validated `TIMEOUT`, non-zero CLI, literal-token non-persistence. Command + result recorded in FR body.
- [ ] **AC-19** Real success run loads the named `run-code-analysis` skill through `--add-dir <run-worktree>`, executes a bounded representative static-analysis workload, returns skill-specific artifact shape, records observable skill selection, matched local/remote SHAs, run/worktree IDs, exit/policy/credit states, elapsed, exact artifact list. Command + result recorded in FR body.
- [ ] **AC-20** CAP-257/REQ-YG-636 + strict `req_coverage` + generated `ARCHITECTURE.md` + SKILL.md frontmatter + `reference/development-operations.md` + `.env.sample` + two changelog fragments + FR-947 supersession + implementation status + diary reflection all committed. **No file outside D-1..D-8 changes.**

## Alternatives Considered

Table above (§ R-1). Every retrieved prior-art hit dispositioned above.

## Related

- Depends on: [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) (recon precondition, read-only).
- Retires: [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md).
- Sanitized spike: [FR-948-spike-evidence.md](FR-948-spike-evidence.md).
- Research artifact (persona-shaped, superseded by § R-1): [FR-948.research.md](FR-948.research.md).
- Brief: [research-briefs/copilot-cli-remote-delegation-brief.md](research-briefs/copilot-cli-remote-delegation-brief.md).
- Orthogonal: [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md).
- Precedent (**NOT modified**): CAP-30 Copilot Node.

## Judgement (second draft rendered 2026-09-01)

Draft: `tmp/draft-judgement.md`. Verdict: **APPROVED WITH REVISIONS** (R-1..R-5). This revision folds all five and adds AC-18 + AC-19 witnesses. Re-judgement to run before enforcement authority activates.
