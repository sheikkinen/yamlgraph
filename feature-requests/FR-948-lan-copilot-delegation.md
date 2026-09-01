# Feature Request: LAN Copilot-CLI delegation channel (supersedes FR-947)

**Priority:** HIGH
**Type:** Feature (with subtractionist scope: retires FR-947)
**Status:** Proposed (revised 2026-09-01 to fold judgement R-1..R-7)
**Effort:** 3 days
**Requested:** 2026-09-01
**First consumer / first event:** an agent that has just verified via FR-945 recon (with `admin=False` and `remote_management_users_member=True`) invokes `.github/skills/lan-delegate/` with a local prompt file and a clean-committed local SHA, and gets back a validated diagnostic result recording exit code, delegation-policy status, timeout state, parsed reported credits, source SHA, run ID, artifact root, and typed errors. **First event:** the next attempt to run heavy work (representative repository workload, e.g. a targeted pytest subset) that would otherwise saturate the iMac. Sanitized spike record: [FR-948-spike-evidence.md](FR-948-spike-evidence.md).
**Research:** [FR-948.research.md](FR-948.research.md) (persona-shaped record; the substantive alternatives table below in § R-1 is the FR-body disposition the judge requires.)
**Prior art:**
- [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) [Proposed, superseded by this FR] — SSH+WSL2+pytest-xdist design premised on the remote box needing full Python environment provisioning. The empirical spike disproved that premise. This FR retires FR-947 in the same commit as lifecycle bookkeeping, not adjacent creation.
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) [Proposed] — the read-only WinRM inventory foundation this FR consumes as a precondition. FR-948 validates FR-945's actual emitted fields (see § 5); no schema amendment under FR-948 authority.
- [FR-945.research.md](FR-945.research.md) — retrieval hit. Substantively unrelated to FR-948's channel design; distinguished (research artifact for a different FR).
- [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md) [Proposed] — delegates LLM inference to LM Studio via a different tool and auth path. Orthogonal.
- [FR-766-runpod-provider.md](FR-766-runpod-provider.md) [Judged] — remote-inference delegation to cloud. Distinguished: FR-948 is LAN-scoped, non-cloud, uses WinRM not HTTPS-inference.
- [FR-899-org-repo-census-azure.md](FR-899-org-repo-census-azure.md) [Implemented] and [FR-899-org-repo-census-azure.judgement.md](FR-899-org-repo-census-azure.judgement.md) — retrieval hits on `remote / delegation / brief` nouns. Substantively unrelated (Azure DevOps census). Dismissed.
- [CAP-30-copilot-node.yaml](../capabilities/CAP-30-copilot-node.yaml) — precedent for the "yamlgraph invokes Copilot CLI locally" pattern. FR-948 extends the same tool across the WinRM boundary but does **not** modify CAP-30 or the YAMLGraph Copilot node (out of scope per judgement C-8).
- [CAP-249-tool-slot-binding.yaml](../capabilities/CAP-249-tool-slot-binding.yaml) — the research artifact cited it; it is unrelated to this delegation channel. Dismissed as retrieval-vocabulary noise.

## Summary

A `.github/skills/lan-delegate/` skill that, given (a) a fresh `LanHostInventory` from FR-945's `tmp/lan/<host>.json` and (b) a local prompt file plus a clean-committed local SHA that the pre-provisioned remote canonical clone already contains, opens a WinRM session (Option A: HTTP 5985, `auth="negotiate"`, `encryption="always"`) to Huutokauppakone, runs a fixed non-LLM `RemoteCopilotPrerequisites` preflight (git present, node major ≥ 22, copilot CLI present, versions captured), creates a disposable `git worktree add` under `C:\Users\copilot\yamlgraph-runs\<run-id>`, invokes `copilot -p <bound-prompt-param> --allow-all-tools --add-dir <run-worktree>` (never `--allow-all-paths`) as the non-admin `copilot` account with `GH_TOKEN` injected via WinRM parameter, captures diagnostics into a Pydantic-typed `LanDelegationResult`, copies only the run-owned output directory to `\\<host>\Images\yamlgraph-delegations\<run-id>\`, and returns. **v1 is stateless**: no `--resume`, no source upload, no `git fetch`, no cloning, no remote runtime installation. **Wall-clock timeout is the only pre-completion cap**; reported credits are diagnostic evidence, not a preventive budget.

## Value Statement

Agents move heavy workloads (representative repository tasks like targeted pytest runs, static analysis, or graph routes) off the saturated iMac and onto Huutokauppakone via an empirically-verified, cost-diagnosed, code-identity-frozen channel — one that reuses FR-945's transport and the yamlgraph skill contract instead of adding a second SSH/WSL2/pyenv stack.

## Problem

- The iMac freezes under concurrent full pytest runs (operator report 2026-09-01).
- FR-947 as drafted would take days to implement and remain fragile: OpenSSH.Server install, dedicated WSL2 Ubuntu alongside Docker Desktop's, `pyenv` for Python 3.11/3.13, SSH key distribution, rsync-per-commit scaffolding, timeout/fallback wrapping.
- Empirical spike 2026-09-01T04:28:52Z (sanitized in [FR-948-spike-evidence.md](FR-948-spike-evidence.md)) proved a delegation channel with none of that infrastructure: WinRM (already open per FR-945 groundwork) + `copilot -p "..." --allow-all-tools` + `GH_TOKEN` via WinRM `param` binding + SMB artifact return. Round-trip: 11 s / 7.17 credits / exit 0 / file written and verified.
- FR-947 is unimplemented; retirement before enforcement is Scripture-aligned (`growth_as_default`).

## Ideal Result

An agent runs `python .github/skills/lan-delegate/delegate.py --host Huutokauppakone.local --prompt-file tmp/prompt.md --run-id 20260901T090000Z-<sha>` against a clean-committed local tree. The delegate refuses non-zero and actionable if: the local tree is dirty; FR-945 recon is missing, stale, or shows a disqualifying value; the pre-provisioned remote clone doesn't contain the local HEAD SHA; `GH_TOKEN` is unset; or any input path is unsafe. On success, one Copilot session runs against a disposable per-run worktree on the remote and drops its outputs into that worktree's `.delegate-out/` directory. The fixed PowerShell wrapper (never the model) copies only that directory to `\\<host>\Images\yamlgraph-delegations\<run-id>\`. `LanDelegationResult` records the two SHAs (matched), the run ID/worktree, Copilot exit + delegation-policy + timeout + parsed-credits statuses, elapsed time, artifact paths, and typed errors. `GH_TOKEN` appears nowhere in scripts, arguments, logs, results, or artifacts across success and every failure path.

## Proposed Solution

### R-1 Alternatives evaluated in the FR body

The `FR-948.research.md` graph output was persona-shaped duplicate rows of the same proposal — insufficient as an alternatives record. The judge required 4-6 genuine solution classes with preserved disagreement. Substantive comparison:

| # | Solution class | Verdict | Rationale (retained disagreement in the last column) |
|---|---|---|---|
| A | **WinRM + Copilot CLI, stateless per-run, disposable worktree** | **Chosen (v1)** | Reuses FR-945's already-hardened transport; Copilot CLI natively speaks `.github/skills` via `--add-dir <root>`; token env-var survives WinRM network logon; empirical spike proved end-to-end (see spike evidence). Cost is bounded by wall-clock timeout (chosen enforcement mechanism per operator, 2026-09-01), reported credits are diagnostic. |
| B | WinRM + deterministic PowerShell remote command execution (no LLM) | Rejected | Would work for a known-shape workload (e.g. rigid `pytest --junitxml=...`) but does not scale to the operator's broader delegation intent ("delegate the heavy load", spanning research, judgement, analysis). Loses the yamlgraph skill contract Copilot CLI provides. Retain as a fallback consideration if Copilot CLI availability degrades. |
| C | FR-947: SSH+WSL2+pytest-xdist over the LAN | Rejected (retired same commit) | Unimplemented; requires days of infrastructure (OpenSSH server, WSL2 Ubuntu, pyenv Python 3.11/3.13, SSH key distribution, rsync scaffolding). Every step is real work and the empirical spike proved the assumption "remote needs full Python env" is false — Copilot in v2 could self-provision if needed. Subtractionist retirement. Preserves precedent for a future SSH-based fallback FR if Copilot CLI becomes unusable. |
| D | Self-hosted GitHub Actions runner on Huutokauppakone | Rejected (v1) | Would move the whole test matrix off the iMac cleanly, but registering a self-hosted runner puts every repo secret on a home-LAN Windows box — a materially wider trust boundary than FR-948's per-run token injection. Revisit if FR-948 fails to reach 90% delegation-success rate in the first month or if credit spend proves unsustainable. |
| E | CI-only / no LAN delegation (subtractionist counterpart) | Rejected (documented as escape) | The cheapest cure: remove local test pre-commit hook, trust the GitHub Actions matrix, tolerate cloud round-trip latency. Rejected because the operator explicitly rejected optimising away the local workflow at the outset; retained as an escape hatch if FR-948 v1 hits a hard obstacle. |

### 2. Dependency

`pypsrp>=0.9,<1.0` (matching FR-945's actual pin in [pyproject.toml](../pyproject.toml)). No new Python deps in this FR. Remote-side dependencies (git, node ≥ 22, `@github/copilot`) are FR-948 **preconditions verified by the § 5 preflight, not installed by this FR**.

### 3. Skill directory `.github/skills/lan-delegate/`

- `SKILL.md` — frontmatter (`name: lan-delegate`, substantive `Use when:`, non-empty `argument-hint`), FR-945-recon prerequisite, credential prerequisites, refusal contract, credit-diagnostic (not cap) semantics, dated human safety and spend decisions.
- `delegate.py` — CLI + library entry point.
- `models.py` — Pydantic `LanDelegationRequest`, `RemoteCopilotPrerequisites`, `LanDelegationResult`, `FieldError`, `DelegationPolicyStatus` per the § 5 tables.
- `wrapper.ps1` — the fixed, committed, ASCII PowerShell script executed on the remote. Zero interpolation of caller-controlled text; `param([string]$Token, [string]$Prompt, [string]$RunId, ...)`.

### 4. R-2 & R-3 Input boundary contract for `delegate.py`

`delegate.py --host TARGET --prompt-file PATH --run-id RUN_ID [--max-reported-credits N] [--timeout SEC]`:

1. **Local-tree freeze**: refuse if `git status --porcelain` on the caller's cwd is non-empty. Record the caller's HEAD SHA (`git rev-parse HEAD`).
2. **Repository identity**: record the remote-tracking upstream URL and the SHA-256 of the current repo's `.git/HEAD` resolved commit. FR-948 does not detect repo identity by name; it uses the SHA and asserts the remote canonical clone contains that SHA.
3. **FR-945 receipt validation**: load `tmp/lan/<slug>.json` for `--host`. Refuse if absent or `probe_ended_at` is older than `RECON_MAX_AGE_MIN` (default 10 min). Validate ONLY the fields FR-945's `LanHostInventory` actually emits: `resolved_address`, `computer_name`, `probe_started_at`, `probe_ended_at`, `admin==False`, `remote_management_users_member==True`, and any typed `errors` marking those fields. Do NOT expect `git`/`node`/`openssh_server_state`/`lm_studio_cli_present`/`listening_ports` — those are not in FR-945's schema (verified against `FR-945-lan-recon-skill.md`).
4. **Prompt boundary**: `--prompt-file PATH` must exist locally, be UTF-8, and be ≤ 32 KiB. Read locally; pass content as WinRM `param([string]$Prompt)` binding — never interpolate into script literal.
5. **Run ID**: `--run-id` must match `^[A-Za-z0-9._-]+$` and be ≤ 64 chars. Rejects `..`, `/`, `\`, colons, whitespace, control chars.
6. **Remote paths** (derived, not caller-supplied): canonical clone `C:\Users\copilot\yamlgraph`; per-run worktree `C:\Users\copilot\yamlgraph-runs\<run-id>`; artifact drop `\\<host>\Images\yamlgraph-delegations\<run-id>\`; local result JSON `tmp/lan/delegate/<host-slug>/<run-id>.result.json`. All are ignored by `.gitignore`.
7. **Credential**: `GH_TOKEN` from env. Single canonical name (no `COPILOT_GITHUB_TOKEN` alias). Passed as `param([string]$Token)`. Redacted from every captured stream; cleared from `$env:GH_TOKEN` in the wrapper's `finally` path.
8. **`--timeout SEC` (default 300)**: PowerShell `operation_timeout` on the WinRM session. **This is the one and only preventive cap** (operator decision, 2026-09-01).
9. **`--max-reported-credits N` (default 60)**: post-run acceptance threshold. If Copilot's tail reports > N credits, or reports no parseable value, the delegation-policy status becomes non-zero and `LanDelegationResult` records `credit_status=FAIL_HIGH` or `FAIL_UNPARSEABLE`. Artifacts are still retrieved for diagnosis.
10. **No `--resume`** in the v1 CLI at all (not just refused with a pointer).
11. **No source upload, no `git fetch`, no `git clone` in v1**: the FR-945 recon and § 5 preflight together determine whether the pre-provisioned remote canonical clone contains the local HEAD SHA. If not, refuse; do not attempt to reconcile. Bootstrapping the remote canonical clone is out of scope for this FR.

### 5. R-4 & R-5 & R-6 WinRM transport, remote preflight, and schemas

Transport (reused from FR-945):

- HTTP 5985 + `auth="negotiate"` + `encryption="always"` (asserted in tests).
- Basic and CredSSP auth explicitly banned; enum-checked.
- Pinned resolved address from FR-945's inventory (no re-resolution).
- `chcp 65001` before invoking Copilot (UTF-8 codepage for output capture).
- `Set-ExecutionPolicy Bypass -Scope Process -Force` (process scope only).
- `$env:GH_TOKEN` set from `$Token` param, `$env:COPILOT_ALLOW_ALL=1`.
- `finally { Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue }` — token cleared from process env at end.

Fixed non-LLM `RemoteCopilotPrerequisites` preflight (before Copilot invocation):

| Field | Type | Check |
|---|---|---|
| `git` | `ToolInfo` | `Get-Command git` present, `git --version` parses |
| `node` | `ToolInfo` | `Get-Command node` present, `node --version` major ≥ 22 |
| `copilot` | `ToolInfo` | `Get-Command copilot.cmd` present under `C:\Program Files\nodejs\`, `copilot.cmd --version` parses (version captured) |
| `canonical_clone` | `RepoInfo` | `C:\Users\copilot\yamlgraph` exists, is a git repo, `git -C <path> cat-file -e <local-sha>` succeeds |
| `run_worktree_available` | `bool` | `C:\Users\copilot\yamlgraph-runs\<run-id>` does not exist |
| `errors` | `list[FieldError]` | typed per-field errors |

Each missing/malformed prerequisite has a typed refusal with actionable message. If any prerequisite fails, delegation stops before `copilot -p` is invoked.

Copilot invocation (only if preflight OK):

```powershell
git -C C:\Users\copilot\yamlgraph worktree add --detach `
    "C:\Users\copilot\yamlgraph-runs\$RunId" $LocalSha
$runRoot = "C:\Users\copilot\yamlgraph-runs\$RunId"
$outDir  = "$runRoot\.delegate-out"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
& 'C:\Program Files\nodejs\copilot.cmd' `
    -p $Prompt `
    --allow-all-tools `
    --add-dir $runRoot          # ROOT, so Copilot loads $runRoot/.github/skills
                                # and $runRoot/.github/agents (per Copilot CLI docs).
# NOTE: --allow-all-paths intentionally absent (judgement R-4).
```

After Copilot exits (any status), the wrapper (never the model):
- Copies `$outDir\*` to `\\<host>\Images\yamlgraph-delegations\<run-id>\`.
- Enumerates that destination for the `artifacts` list (not a global SMB mtime diff).
- Runs `git -C C:\Users\copilot\yamlgraph worktree remove --force <run-worktree>`.
- Clears `$env:GH_TOKEN`.
- Emits one JSON summary (redacted) on stdout parsed by `delegate.py`.

`LanDelegationRequest` (input to `delegate.py`, typed):

| Field | Type | Notes |
|---|---|---|
| `host` | `str` | mDNS name; must match an inventory in `tmp/lan/` |
| `prompt_file` | `Path` | UTF-8, ≤32 KiB |
| `run_id` | `str` | regex `^[A-Za-z0-9._-]+$`, ≤64 |
| `max_reported_credits` | `float` | default 60 |
| `timeout_s` | `int` | default 300 |
| `local_sha` | `str` | resolved from caller's cwd HEAD |
| `local_clean` | `bool` | `git status --porcelain` empty |

`DelegationPolicyStatus` enum: `OK`, `TIMEOUT`, `COPILOT_NONZERO`, `PREFLIGHT_FAIL`, `CREDIT_FAIL_HIGH`, `CREDIT_FAIL_UNPARSEABLE`, `WRAPPER_JSON_MALFORMED`, `ARTIFACT_COPY_FAIL`.

`LanDelegationResult` (typed diagnostic; produced whenever a run launched; pre-launch refusals raise typed exceptions and do NOT produce this):

| Field | Type | Notes |
|---|---|---|
| `request` | `LanDelegationRequest` | input echoed |
| `host_resolved_address` | `IPvAnyAddress` | from FR-945 |
| `remote_computer_name` | `str` | from FR-945 |
| `prerequisites` | `RemoteCopilotPrerequisites` | preflight result |
| `local_sha` | `str` | frozen at request time |
| `remote_worktree` | `str` | `C:\Users\copilot\yamlgraph-runs\<run-id>` |
| `copilot_exit_code` | `int \| None` | None if Copilot never invoked (preflight failed) |
| `delegation_policy_status` | `DelegationPolicyStatus` | required |
| `timed_out` | `bool` | required |
| `elapsed_s` | `float` | required |
| `credits_reported` | `float \| None` | parsed; None if unparseable |
| `credit_status` | `Literal["OK","FAIL_HIGH","FAIL_UNPARSEABLE","NOT_APPLICABLE"]` | required |
| `tokens_up` | `int \| None` | parsed |
| `tokens_down` | `int \| None` | parsed |
| `artifacts` | `list[Path]` | files copied to SMB drop |
| `stdout_path` | `Path` | redacted UTF-8 log |
| `stderr_path` | `Path` | redacted UTF-8 log |
| `errors` | `list[FieldError]` | typed |

`FieldError`: `field: str; message: str; error_type: Literal[...]`. Owned by this FR (not FR-945's).

`wrapper.ps1` on the remote emits one JSON document matching the wrapper-side subset (Copilot exit, timed-out, elapsed, artifact list, parsed credits, tokens, wrapper-side errors). `delegate.py` merges that with mac-side fields (request, local_sha, host_resolved_address, delegation_policy_status, stdout/stderr paths).

### 6. R-6 Test list (all offline; no real DNS, socket, WinRM, SMB, or Copilot)

`tests/unit/test_lan_delegate.py` covers, at minimum:

1. Missing FR-945 inventory file → typed exception; CLI non-zero + actionable stderr.
2. Stale FR-945 inventory → typed exception naming age.
3. FR-945 inventory with `admin=True` → refused.
4. FR-945 inventory with `remote_management_users_member=False` → refused.
5. FR-945 inventory with typed error on `resolved_address` → refused.
6. Missing `GH_TOKEN` → refused before any DNS/socket/WinRM.
7. Dirty local tree (mocked `git status --porcelain` non-empty) → refused.
8. `--run-id` collision (mocked path exists) → refused.
9. Unsafe `--run-id` (contains `..`, `/`, `\`, whitespace, control char) → refused.
10. Prompt file > 32 KiB → refused.
11. Prompt file non-UTF-8 → refused.
12. Prompt file missing → refused.
13. Remote preflight: `git` absent → refused; `RemoteCopilotPrerequisites.git.error` populated.
14. Remote preflight: node major < 22 → refused.
15. Remote preflight: copilot absent → refused.
16. Remote preflight: canonical clone does NOT contain local SHA → refused.
17. Remote preflight: run worktree path already exists → refused.
18. Client-construction test: exact kwargs asserted — `auth="negotiate"`, `encryption="always"`, `ssl=False`, `port=5985`, pinned resolved address, finite `connection_timeout`/`operation_timeout`. Basic/CredSSP absent.
19. Prompt-passing test: WinRM script text captured, asserted the prompt string is absent from the script literal and present only via `param` binding.
20. Copilot invocation test: `--add-dir` value is the RUN WORKTREE (not `<clone-dir>/.github/skills`). `--allow-all-paths` is absent. `--allow-all-tools` is present.
21. Token redaction: synthetic token injected, forced auth failure; assert token absent from wrapper stdout, wrapper stderr, `LanDelegationResult`, and all `artifacts` content in the fixture.
22. Timeout: mocked hung Copilot invocation → `timed_out=True`, `delegation_policy_status=TIMEOUT`, CLI non-zero, artifacts (if any) still enumerated.
23. Copilot non-zero exit → `delegation_policy_status=COPILOT_NONZERO`, CLI non-zero.
24. Credit report missing → `credit_status=FAIL_UNPARSEABLE`, CLI non-zero.
25. Credit report exceeds `--max-reported-credits` → `credit_status=FAIL_HIGH`, CLI non-zero, artifacts preserved.
26. Wrapper JSON malformed → `delegation_policy_status=WRAPPER_JSON_MALFORMED`, CLI non-zero.
27. Artifact copy failed on remote → `delegation_policy_status=ARTIFACT_COPY_FAIL`, CLI non-zero, `artifacts=[]` (or partial with typed errors).
28. Two concurrent mocked runs with distinct `--run-id`s → each attributes exactly its own artifacts (isolation invariant).
29. `--resume` flag absent from CLI parse — sending it raises argparse error.
30. Wrapper contains NO install/fetch/clone/SSH/WSL/service/policy/firewall/group mutation (regex scan on committed `wrapper.ps1`).
31. Env cleanup: after a mocked run completes, `$env:GH_TOKEN` is empty (assert wrapper text contains the `finally` clear).

Happy-path fixture: sanitized values from [FR-948-spike-evidence.md](FR-948-spike-evidence.md) plus a synthesized workload run (representative pytest subset stub) with matching local/remote SHA. Test asserts concrete field values, not merely parse success.

### 7. Live witness (R-6) — real representative workload

One real Huutokauppakone run recorded in this FR under "Manual verification" once implementation lands. Must exercise a **named representative repository workload**, not another trivial file write. Candidate: `pytest tests/unit/test_config.py -q --no-cov --junitxml=.delegate-out/junit.xml` (a small deterministic test file). Records: local SHA, remote SHA (from the disposable worktree), run ID, worktree path, `copilot_exit_code`, `delegation_policy_status`, `elapsed_s`, `credits_reported`, `credit_status`, artifact list, matched-SHA assertion. No credential material.

### 8. R-7 Governance

- New `capabilities/CAP-257-lan-copilot-delegation.yaml` + new `REQ-YG-636`. Registers the skill, `delegate.py`, `models.py`, `wrapper.ps1`, and the test module. Every new test carries `@pytest.mark.req("REQ-YG-636")`. `python scripts/req_coverage.py --strict` passes. `ARCHITECTURE.md` section regenerated.
- Changelog fragment `changelog/unreleased/fr-948-lan-copilot-delegation.md` (`type: feat`, `scope: skills`, `req: REQ-YG-636`).
- Changelog fragment `changelog/unreleased/fr-948-retire-fr947.md` (`type: removal`, `scope: skills`).
- Diary reflection: `docs/diary/2026-09-XX-fr948-copilot-delegation.md` covering the empirical-spike-drives-design pattern, the FR-947 retirement precedent, and the pypsrp-pin composition-defect catch (would have hit at enforcement).
- `reference/development-operations.md` gains "LAN Copilot delegation" subsection documenting `GH_TOKEN` name only, the FR-945-recon precondition, the pre-provisioned-runtime rule, the `--allow-all-tools` tool/credential risk, post-run credit semantics, and safe invocation.
- `.env.sample` gains commented `GH_TOKEN=`.
- FR-947 body: `**STATUS: SUPERSEDED-BY FR-948 (2026-09-01)**` banner (already applied in this commit's parent).
- Not modified: CAP-30, YAMLGraph Copilot node, judge/review doctrine, hooks/CI, Chaplain runtime.

## Dated human decisions (2026-09-01)

**Q1 (safety — R-4)**: Does the operator authorize a non-interactive LLM process (`copilot -p`) with `--allow-all-tools` and a live `GH_TOKEN` on Huutokauppakone, constrained to a disposable per-run worktree, with the credential's minimum permissions / repository access / expiry / rotation / revocation policy written in the FR?

**Answered 2026-09-01: YES ("yolo").**
- Constraint envelope acknowledged: per-run disposable git worktree, non-admin `copilot` account (`admin=False`, `S-1-5-32-580` member), WinRM Negotiate mandatory-encryption transport, home-LAN posture, single physical operator.
- Token: whatever `gh auth token` on the mac already returns (present tense). No formal expiry/rotation policy for v1. If leaked, revoke via GitHub Settings → Developer settings and re-run `gh auth login`; this constitutes the "revocation action". The FR does not add rotation ceremony beyond that.
- The `--allow-all-tools` boundary IS understood to mean: any tool Copilot spawns inside its process runs with `copilot`-user privileges and can read `$env:GH_TOKEN` until the wrapper's `finally` clears it. Redaction is defense in depth, not a proof of impossibility.

**Q2 (spend — R-5)**: Does the operator accept that v1 can detect reported overspend only after Copilot exits, and cannot guarantee a hard per-run or per-day credit cap?

**Answered 2026-09-01: YES (acceptable). "We'll operate this via copilot nodes / yamlgraph — timeout is the cap."**
- The preventive cap is the WinRM `operation_timeout` (default 300 s, tunable per invocation). Wall-clock exhaustion aborts the WinRM operation, which terminates the remote `copilot.cmd` process.
- Reported credits are diagnostic evidence, not a preventive budget. Missing or malformed credit reports fail closed (`credit_status=FAIL_UNPARSEABLE`, CLI non-zero).
- Deployment mode: FR-948 is invoked from yamlgraph Copilot nodes and graph orchestration, which enforce their own timeouts and can add a wrapper-level per-graph credit budget across multiple delegations. This FR does not add graph-level spend gating; that's a future capability the graph layer can provide on top.

## Acceptance Criteria (18, per judge's revised list)

- [ ] **AC-01** FR-948 body contains the § R-1 alternatives table (5 solution classes A-E) with preserved disagreement; every retrieval hit (FR-947, FR-945.research.md, FR-899, FR-899.judgement.md, CAP-249) is dispositioned in "Prior art"; one reconciled `is_this_a_graph` answer (this delegation channel is NOT a graph orchestration; the graph *consumes* its output).
- [ ] **AC-02** Sanitized [FR-948-spike-evidence.md](FR-948-spike-evidence.md) is committed and contains exact command shape, exit code, elapsed, credit/token/resume lines, redacted WinRM invocation, artifact content. Every FR-948 feasibility claim traces to a line in that file; unsupported self-provisioning claims removed.
- [ ] **AC-03** FR-948 depends on FR-945 as a precondition; uses `pypsrp>=0.9,<1.0`; validates only fields FR-945's `LanHostInventory` actually emits (§ 4.3); does not alter FR-945.
- [ ] **AC-04** `LanDelegationRequest`, `RemoteCopilotPrerequisites`, `LanDelegationResult`, `FieldError`, `DelegationPolicyStatus` schemas are fully specified in § 5 tables and implemented as Pydantic models; no untyped result dictionary crosses a boundary.
- [ ] **AC-05** Host, prompt, run-id, clone, worktree, log, result, and artifact paths are normalized before use; invalid, escaping, non-UTF-8, oversized, missing, or colliding inputs fail before WinRM or file write.
- [ ] **AC-06** Fixed remote preflight (§ 5) verifies git present, node major ≥ 22, copilot CLI present + version parseable, canonical clone contains local SHA, run worktree free. Each absent/old/malformed/failed prerequisite has an offline refusal test.
- [ ] **AC-07** v1 accepts only a clean committed local tree; records local HEAD SHA; requires that SHA in pre-provisioned remote canonical clone; creates disposable `git worktree add --detach`. Tests prove dirty, absent-SHA, collision, and concurrent-run isolation behavior.
- [ ] **AC-08** Prompt contents cross WinRM only as bound `param([string]$Prompt)`; test asserts prompt string absent from script literal. Copilot invocation uses `--add-dir <run-worktree>` (root), NOT nested `.github/skills`. `--allow-all-paths` absent. `--allow-all-tools` present.
- [ ] **AC-09** Copilot writes only to run-owned `<worktree>\.delegate-out\`; fixed wrapper (never the model) copies only that directory to `\\<host>\Images\yamlgraph-delegations\<run-id>\`. Two mocked concurrent runs prove artifact-isolation invariant.
- [ ] **AC-10** Client construction pins FR-945 resolved address and asserts `auth="negotiate"`, `encryption="always"`, `ssl=False`, `port=5985`, finite `connection_timeout`/`operation_timeout`. Basic/CredSSP absent.
- [ ] **AC-11** Dated human safety decision recorded (§ "Dated human decisions" above, Q1 = YES 2026-09-01). Tests prove `GH_TOKEN` is absent from command arguments, script text, logs, `LanDelegationResult`, and artifact content across success + every failure path. Wrapper `finally` clears `$env:GH_TOKEN`; test asserts the clear is present in committed wrapper source.
- [ ] **AC-12** Pre-run failures raise typed library exceptions and produce no `LanDelegationResult` and non-zero CLI. Launched runs always produce a validated `LanDelegationResult`, with separate `copilot_exit_code` and `delegation_policy_status`. Copilot failure, timeout, parse failure, wrapper-json-malformed, artifact-copy-fail, credit-fail-high, credit-fail-unparseable each make CLI non-zero.
- [ ] **AC-13** `--max-reported-credits` documented and tested as post-run acceptance only. Missing, malformed, or over-threshold credit output → `credit_status` non-`OK`, CLI non-zero, artifacts preserved.
- [ ] **AC-14** Dated human spend decision recorded (§ "Dated human decisions", Q2 = YES 2026-09-01). No hard-cap or bounded-cost claim in the FR body. Wall-clock `--timeout` is the sole preventive cap; documented explicitly.
- [ ] **AC-15** v1 exposes no `--resume` and performs no remote bootstrap/install. Test parses CLI with `--resume` → argparse error. Regex scan on committed `wrapper.ps1` proves no `winget`, `npm i`, `pip install`, `git clone`, `git fetch`, `Add-WindowsCapability`, `wsl --install`, `Set-Service`, `New-NetFirewallRule`, or group-membership mutation.
- [ ] **AC-16** Offline tests cover all R-6 boundaries (30+ items in § 6) without DNS, socket, WinRM, SMB, or Copilot access. Semantic-value assertions on the sanitized happy-path fixture.
- [ ] **AC-17** One real Huutokauppakone run executes a named representative repository workload (e.g. `pytest tests/unit/test_config.py -q --no-cov`); records matching local/remote SHA, run ID/worktree, `copilot_exit_code`, `delegation_policy_status`, `elapsed_s`, `credits_reported`, `credit_status`, artifact list. Recorded in this FR body. Zero credential material.
- [ ] **AC-18** `CAP-257-lan-copilot-delegation.yaml` + `REQ-YG-636` register all surfaces; strict req_coverage passes; generated `ARCHITECTURE.md` section committed; SKILL.md frontmatter valid; `.env.sample` gains `GH_TOKEN=`; `reference/development-operations.md` updated; FR-947 supersession header intact; two changelog fragments (feat + removal) present; diary reflection committed; **no surface outside the frozen D-1..D-8 list (see judgement) is changed**.

## Alternatives Considered

Table above (§ R-1). Full disposition of every retrieved prior art in the "Prior art" line.

## Related

- Depends on: [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) (recon precondition).
- Retires: [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md).
- Sanitized spike: [FR-948-spike-evidence.md](FR-948-spike-evidence.md).
- Research artifact (persona-shaped, superseded by § R-1 table): [FR-948.research.md](FR-948.research.md).
- Brief: [research-briefs/copilot-cli-remote-delegation-brief.md](research-briefs/copilot-cli-remote-delegation-brief.md).
- Orthogonal: [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md).
- Precedent (not modified): CAP-30 Copilot Node.

## Judgement (first draft rendered 2026-09-01)

Draft: `tmp/draft-judgement.md`. Verdict: **APPROVED WITH REVISIONS**. This revision folds R-1..R-7 and records both dated human decisions above. Re-judgement to be run before enforcement authority is activated.
