# Feature Request: LAN Copilot-CLI delegation channel (supersedes FR-947)

**Priority:** HIGH
**Type:** Feature (with subtractionist scope: retires FR-947)
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-09-01
**First consumer / first event:** an agent that has just verified via FR-945 recon that a LAN host is delegation-ready invokes `.github/skills/lan-delegate/` with a prompt file and gets back a validated `LanDelegationResult` (exit code, artifact path on the SMB share, credit cost, elapsed time). **First event:** the next attempt to run heavy work (test suite, static analysis, or a graph route) that would otherwise saturate the iMac at load average > 8. Empirically-verified round-trip: 11 s / 7.17 credits for a trivial file-write task (`tmp/copilot-spike-phase2f.log`, 2026-09-01T04:28:52Z).
**Research:** [FR-948.research.md](FR-948.research.md)
**Prior art:**
- [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) [Proposed, superseded by this FR] — SSH+WSL2+pytest-xdist design premised on the remote box needing full Python environment provisioning. Empirical spike disproved that premise: Copilot CLI self-provisions Python on demand. This FR retires FR-947 in the same commit.
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) [Judged, APPROVED WITH REVISIONS] — the read-only WinRM inventory foundation this FR consumes. FR-948 requires FR-945's `LanHostInventory` JSON as a precondition input (delegation refuses to run against a host whose recon isn't fresh). Distinguished: FR-945 inspects, FR-948 delegates work.
- [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md) [Proposed] — delegates LLM inference to LM Studio. Distinguished: orthogonal channel, different tool, different auth path.
- [FR-899-org-repo-census-azure.md](FR-899-org-repo-census-azure.md) [Implemented] — retrieval hit on "remote/delegation/brief" nouns; substantively unrelated (Azure DevOps census, not delegation).
- [CAP-30 Copilot Node](../capabilities/CAP-30-copilot-node.yaml) — precedent for the "yamlgraph invokes Copilot CLI locally" pattern this FR extends across the WinRM boundary.

## Summary

A `.github/skills/lan-delegate/` skill that, given (a) a fresh `LanHostInventory` from FR-945's `tmp/lan/<host>.json` and (b) a prompt file, opens a WinRM session to the recon-verified host, invokes `copilot -p "<prompt>" --allow-all-tools --allow-all-paths --add-dir <clone-path>` as the non-admin `copilot` service account with `GH_TOKEN` injected via WinRM parameter (never in the script literal), captures Copilot's exit code + resume ID + AI credit cost + elapsed time into a Pydantic-typed `LanDelegationResult`, retrieves artifacts from `\\<host>\Images\` (the SMB drop-zone), and returns to the caller. Delegation is read-only from the mac side (the mac never `pip install`s on the remote); the remote Copilot session self-provisions its own Python/deps via `winget`/`pip` inside the `--allow-all-tools` sandbox.

## Value Statement

Agents that would otherwise saturate the local 12-thread/8-GB iMac with concurrent test runs push that load onto Huutokauppakone (16-thread/24-GB/RTX 3070) at a bounded per-run credit cost, with an FR-945-recon-verified auth path and no new SSH/WSL2 infrastructure to maintain.

## Problem

- The iMac freezes under 2-3 concurrent full pytest runs (operator report 2026-09-01).
- FR-947 as drafted would take days to implement: install OpenSSH.Server, install a dedicated WSL2 Ubuntu distro alongside Docker Desktop's, `pyenv` install Python 3.11 and 3.13, distribute SSH keys, build rsync-per-commit scaffolding, wrap timeout/fallback for pre-commit safety. All of it is real work and each piece has its own failure mode.
- Empirical spike 2026-09-01T04:28:52Z proved a delegation channel that requires **none** of that infrastructure: WinRM (already open per FR-945 groundwork) + `copilot -p "..." --allow-all-tools` (installed system-wide via `npm i -g @github/copilot` after Node 24 upgrade) + `GH_TOKEN` env-var injection (survives WinRM network-logon, unlike DPAPI device-flow tokens) + SMB share (already mounted at `/Volumes/Images`). Round-trip: 11 s / 7.17 credits.
- FR-947 is unimplemented. Retiring it before enforcement is Scripture-aligned (`growth_as_default` cure; the cheapest bug is the one caught in the spec).

## Ideal Result

An agent runs `python .github/skills/lan-delegate/delegate.py --host Huutokauppakone.local --prompt-file tmp/prompt.md --clone-dir 'C:\Users\copilot\yamlgraph'`. It gets back a validated `LanDelegationResult` JSON: `exit_code`, `resume_id`, `credits_used`, `elapsed_s`, `stdout_path`, `stderr_path`, `artifacts` (list of files landed on the SMB share during the session). If FR-945 recon is stale (>10 min old) or absent, delegation refuses. If credit budget for the run is exceeded, delegation aborts. Zero credential material is committed; every token flows via env-var and WinRM parameter binding, never through the model's context.

## Proposed Solution

### R-1 Research disposition

The FR-948 research artifact returned five "pursue" candidates that converge unanimously (5/5, four of them subtractionist-flavored). Disposition:

| Candidate (persona) | Disposition here |
|---|---|
| WinRM+PowerShell native token passthrough + `--allow-all-tools --add-dir` (os-infra-primitivist) | Adopted as the transport contract. |
| Replace unimplemented FR-947 with proven WinRM+Copilot channel (data-process-planner) | Adopted; FR-947 marked SUPERSEDED-BY this FR in the same commit. |
| Retire FR-947, replace with `--add-dir .github/skills` skill-aware channel (yamlgraph-native-planner) | Adopted; skill-directory sharing is a core AC (AC-06). |
| Retire FR-947, subtractionist (subtractionist) | Adopted; FR-947 retirement is subtraction, not adjacent creation. |
| Copilot CLI as remote LLM-driven executor with `--resume=<uuid>` for statefulness (librarian) | Adopted with reservations: session-state reuse is deferred to a v2 (see R-5 test constraint on stateless-only in v1). |

### 1. Dependency

`pypsrp>=0.10` (from FR-945; already in `[dev]` extras after FR-945 lands). No new Python deps in this FR. Remote-side dependencies (`node`, `@github/copilot`, `git`) are FR-948 preconditions verified via FR-945 recon, NOT installed by this FR (a delegation FR must not install its own remote runtime).

### 2. Skill directory `.github/skills/lan-delegate/`

- `SKILL.md` — frontmatter (`name: lan-delegate`, substantive `Use when:`, non-empty `argument-hint`), the FR-945-recon prerequisite, credential prerequisites, refusal contract, cost boundary.
- `delegate.py` — CLI + library entry point.
- `models.py` — Pydantic `LanDelegationRequest` and `LanDelegationResult` per the schema table (§ 5).
- `wrapper.ps1` — the fixed, committed, ASCII PowerShell script executed on the remote. Zero interpolation of caller-controlled text; token is a `param([string]$Token)`; prompt is `param([string]$PromptFile)` (path, not the prompt itself — the wrapper reads it via `Get-Content`).

### 3. R-2 Input boundary contract for `delegate.py`

`delegate.py --host TARGET --prompt-file PATH --clone-dir REMOTE_DIR [--credit-budget N] [--timeout SEC] [--resume UUID]`:

1. `--host TARGET` must match an existing `tmp/lan/<slug>.json` file (produced by FR-945). Refuse if absent.
2. Load the inventory. Refuse if any of these are false: `admin==False`, `remote_management_users_member==True`, presence of `git`, presence of `node` with major >= 22, `openssh_server_state` need NOT be `Installed` (this FR does not use SSH).
3. Refuse if inventory `probe_ended_at` is older than `RECON_MAX_AGE_MIN` (default 10 min); FR-948 does not delegate against stale intelligence.
4. `--prompt-file PATH` must exist locally and be UTF-8. Refuse if binary or > 32 KiB (prompts of that size are misuse; use `--add-dir` for context).
5. `--clone-dir REMOTE_DIR` must be an absolute Windows path (regex `^[A-Za-z]:\\`) under the `copilot` user's profile (must start with `C:\Users\copilot\`). No `..`, no share paths.
6. `--credit-budget N` (default 60): abort if `credits_used > N`. Enforced by the wrapper (checks last line of Copilot output).
7. `--timeout SEC` (default 300): PowerShell `operation_timeout` on the WinRM session.
8. `--resume UUID` (v2, refused in v1): FR-948 v1 is stateless-only. Reintroduced only when v2 lands with a session-drift test suite.
9. Credentials: `LAN_RECON_USER` / `LAN_RECON_PASS` from env (FR-945), plus `GH_TOKEN` from env. Refuse if any is empty. GH_TOKEN is passed as a WinRM `param` binding, never interpolated into the script literal.

### 4. R-3 WinRM transport reused from FR-945

Same Option A as FR-945: HTTP 5985 + `auth="negotiate"` + `encryption="always"` + Basic/CredSSP banned + pinned resolved address from the inventory. The wrapper additionally:
- Sets `chcp 65001` before invoking Copilot (UTF-8 codepage for output capture).
- Sets `Set-ExecutionPolicy Bypass -Scope Process -Force` (npm-installed `copilot.ps1` is unsigned; process-scope bypass, not machine-wide).
- Sets `$env:GH_TOKEN`, `$env:COPILOT_GITHUB_TOKEN`, `$env:COPILOT_ALLOW_ALL=1` from the bound `$Token` parameter.
- Redacts the token from all captured output before returning it or writing it to the SMB share.

### 5. R-4 `LanDelegationResult` schema

| Field | Type | Req/Opt | Units | Normalization |
|---|---|---|---|---|
| `requested_host` | `str` | required | - | verbatim from `--host` |
| `resolved_address` | `IPvAnyAddress` | required | - | from FR-945 inventory |
| `inventory_probe_ended_at` | `datetime` | required | UTC | proves freshness gate passed |
| `exit_code` | `int` | required | - | Copilot CLI exit code |
| `elapsed_s` | `float` | required | seconds | wall clock end-to-end |
| `credits_used` | `float \| None` | optional | AI credits | parsed from Copilot output tail; None if unparseable |
| `tokens_up` | `int \| None` | optional | tokens | parsed from Copilot output tail |
| `tokens_down` | `int \| None` | optional | tokens | parsed from Copilot output tail |
| `resume_id` | `str \| None` | optional | - | UUID from `Resume    copilot --resume=...` line if present; unused in v1 but captured |
| `stdout_path` | `str` | required | - | `tmp/lan/delegate/<host>/<utc-stamp>.stdout.log` (redacted, UTF-8) |
| `stderr_path` | `str` | required | - | same shape |
| `artifacts` | `list[str]` | required (may be `[]`) | - | files under `\\<host>\Images\` created/modified during the run window; snapshot before + after, diff by mtime |
| `refusal_reason` | `str \| None` | optional | - | if delegation refused, human-readable reason |
| `errors` | `list[FieldError]` | required (may be `[]`) | - | typed errors from parse/execution |

`.github/skills/lan-delegate/wrapper.ps1` is committed, pure ASCII, no interpolation of caller-controlled text, references built-in groups by SID where relevant, and emits one JSON summary object on stdout (parsed by `delegate.py` and merged with mac-side fields into `LanDelegationResult`).

### 6. R-5 Test list (offline; no real WinRM or LLM)

`tests/unit/test_lan_delegate.py` covers exactly these paths:

1. Missing `--host` inventory file → refused; actionable stderr naming the expected path.
2. Stale inventory (older than `RECON_MAX_AGE_MIN`) → refused; message names the age.
3. Inventory with `admin=True` → refused (contract: never delegate to an admin session).
4. Inventory with `remote_management_users_member=False` → refused.
5. Inventory with `node` major < 22 → refused; actionable message names FR-948 dependency.
6. Missing `GH_TOKEN` → refused before any WinRM connect attempt.
7. Prompt file > 32 KiB → refused.
8. Prompt file binary (non-UTF-8) → refused.
9. `--clone-dir` outside `C:\Users\copilot\` → refused.
10. Credit-budget exceeded (mocked Copilot output shows `AI Credits 100 (7s)` with default 60 budget) → refused post-hoc; artifacts still retrieved for diagnosis.
11. Token appears verbatim in any captured log, stdout, or return value → test fails (redaction contract).
12. `--resume` flag in v1 → refused with pointer to v2 spec.

Plus the happy-path fixture: mock WinRM response with the actual Phase 2f spike output (redacted), `LanDelegationResult` parses cleanly, `credits_used=7.17`, `tokens_up=51400`, `tokens_down=204`, `resume_id="0645de30-52dd-4dbb-b50e-066e625ae4e0"`, `artifacts=["phase2f-<stamp>.txt"]`.

Live witness kept: one real `delegate.py` invocation against Huutokauppakone recorded in this FR under "Manual verification" once implementation lands.

### 7. R-6 Governance

- New `capabilities/CAP-257-lan-copilot-delegation.yaml` + new `REQ-YG-636`. Registers the skill, `delegate.py`, `models.py`, `wrapper.ps1`, and the test module. `python scripts/req_coverage.py --strict` passes.
- Changelog fragment `changelog/unreleased/fr-948-lan-copilot-delegation.md` (`type: feat`, `scope: skills`, `req: REQ-YG-636`).
- Changelog fragment `changelog/unreleased/fr-948-retire-fr947.md` (`type: removal`, `scope: skills`) documenting FR-947 retirement.
- Diary reflection: `docs/diary/2026-09-XX-fr948-copilot-delegation.md` covering the empirical-spike-drives-design pattern and the FR-947 retirement precedent.
- `reference/development-operations.md` gains a "LAN Copilot delegation" subsection documenting `GH_TOKEN` (names only), the FR-945-recon precondition, the credit budget, and the safe invocation contract.
- `.env.sample` gains commented `GH_TOKEN=` and `COPILOT_GITHUB_TOKEN=` lines (either accepted).
- FR-947 body updated: banner `**STATUS: SUPERSEDED-BY FR-948 (2026-09-01)**` at the top; brief note explaining the subtractionist path. Not deleted; the file survives as precedent.

```bash
# usage (after installation)
python .github/skills/lan-delegate/delegate.py \
    --host Huutokauppakone.local \
    --prompt-file tmp/prompt.md \
    --clone-dir 'C:\Users\copilot\yamlgraph' \
    --credit-budget 60
# -> tmp/lan/delegate/huutokauppakone.local/<utc>.result.json  (LanDelegationResult)
```

## Acceptance Criteria

- [ ] **AC-01** FR-948 contains the § R-1 research-selection table dispositioning all 5 personas and every retrieved prior-art hit (FR-947 SUPERSEDED, FR-945 as foundation, FR-946 orthogonal, FR-899 unrelated, CAP-30 as precedent).
- [ ] **AC-02** `.github/skills/lan-delegate/SKILL.md` has valid frontmatter and documents the FR-945-recon precondition, credential prerequisites, refusal contract, and credit ceiling.
- [ ] **AC-03** `LanDelegationResult` schema table in FR body matches Pydantic implementation; no untyped dicts cross the parse boundary.
- [ ] **AC-04** `.github/skills/lan-delegate/wrapper.ps1` is committed, pure ASCII, no caller-controlled interpolation, sets `chcp 65001`, redacts `$Token` from all captured output before returning it.
- [ ] **AC-05** `delegate.py` refuses cleanly and non-zero with actionable stderr on every path in § 6 R-5 (12 refusal paths); typed exceptions from library API.
- [ ] **AC-06** `--add-dir <clone-dir>/.github/skills` is used to give the remote Copilot session the same skill contract the mac side uses; test asserts the flag is present in the wrapper's invocation.
- [ ] **AC-07** GH_TOKEN is passed as a PowerShell `param` binding, never interpolated into the script literal; test proves the token string does not appear in the sent script text.
- [ ] **AC-08** All captured output (`stdout_path`, `stderr_path`, returned `LanDelegationResult`) is scanned for the token before write/return; a test injects a synthetic token, forces auth failure, and asserts absent from output.
- [ ] **AC-09** FR-945 recon precondition enforced: delegation refuses if `tmp/lan/<host>.json` is missing or older than `RECON_MAX_AGE_MIN` (default 10 min).
- [ ] **AC-10** Credit ceiling enforced from parsed Copilot output; a run that exceeds `--credit-budget` returns non-zero and records `refusal_reason`; artifacts still retrieved for diagnosis.
- [ ] **AC-11** Session-state reuse (`--resume`) is refused in v1 with a pointer to a v2 spec section that names the drift-test suite required to admit it.
- [ ] **AC-12** A real Huutokauppakone run is recorded in this FR: command, credits used, elapsed time, artifact list, exit code. Zero credential material.
- [ ] **AC-13** `CAP-257-lan-copilot-delegation.yaml` + `REQ-YG-636` register all surfaces; every new test carries `@pytest.mark.req("REQ-YG-636")`; `python scripts/req_coverage.py --strict` passes.
- [ ] **AC-14** FR-947 body carries the `**STATUS: SUPERSEDED-BY FR-948**` banner; a `type: removal` changelog fragment records the retirement.
- [ ] **AC-15** `reference/development-operations.md` "LAN Copilot delegation" subsection + `.env.sample` placeholder committed; no real credential committed.
- [ ] **AC-16** FR-948 implementation status recorded; two changelog fragments present (feat + removal); diary reflection committed; no unauthorized surface changed.

## Witnessed evidence (2026-09-01 discovery session)

- **End-to-end round-trip verified** (`tmp/copilot-spike-phase2f.log`, 2026-09-01T04:28:52Z):
  - `copilot exit=0 elapsed=11.0s`
  - Content of `/Volumes/Images/phase2f-20260901T042852Z.txt`: `ok 20260901T042852Z` (matched prompt exactly)
  - Copilot output tail: `AI Credits 7.17 (7s)`, `Tokens ↑ 51.4k (25.6k cached, 25.8k written) • ↓ 204`
  - `Resume     copilot --resume=0645de30-52dd-4dbb-b50e-066e625ae4e0`
- **Auth boundary** (2026-09-01T04:13Z): device-flow token stored under interactive profile FAILED across the WinRM network-logon boundary (`No authentication information found`). Env-var `GH_TOKEN` in the WinRM `param` binding SUCCEEDED. This is the only auth path that works over WinRM; hard constraint in AC-07/AC-08.
- **Node upgrade witnessed** (2026-09-01T04:06Z): Node 18.16.1 could not resolve `@github/copilot` platform-specific packages; `winget install OpenJS.NodeJS.LTS --scope machine` upgraded to Node 24.19.0 in-place with npm 11.17.0. Precedent for remote-side environment self-provisioning by winget.
- **Skill contract witness** (`copilot --help` output on remote): `--add-dir <directory>  Allow file access to a directory and load its .github/skills and .github/agents as trusted configuration`. Copilot CLI natively speaks the yamlgraph skill contract. This is the differentiator vs. FR-947.
- **PowerShell 5.1 constraints re-verified**: `.ps1` files must be ASCII or UTF-8 BOM (em-dash trap from FR-945 session applies); local groups referenced by SID `S-1-5-32-580` (Finnish install: `Etähallinnan käyttäjät`); execution-policy bypass at process scope only.
- **Cost model**: 7.17 credits for a trivial round-trip. Full-suite delegation estimated 20-60 credits (bounded by prompt size, not test count); AC-10 makes this concrete via `--credit-budget`.

## Alternatives Considered

- **Adopt FR-947 as drafted** (SSH+WSL2+pytest-xdist). Rejected: empirically disproven — the remote box does not need the reproduced Python environment FR-947 assumes; Copilot self-provisions.
- **Coexist** (both FR-947 and FR-948 as alternative channels). Rejected: FR-947 is unimplemented; carrying its scope forward is `growth_as_default`. Its subtractionist retirement IS the correct move.
- **`--resume` reuse in v1** for latency reduction. Deferred to v2 pending a drift-test suite (session state can accumulate across pre-commit runs in unbounded ways; needs its own investigation FR).
- **Direct `git bundle`+`rsync` file drop instead of `--add-dir`**. Deferred; adopting `--add-dir` gives Copilot native awareness of the skill contract, so mac and remote share one enforcement surface.
- **Alternative token source** (fine-grained PAT vs. `gh auth token`). Both accepted; `.env.sample` documents both env-var names.
- **Different remote host** (RunPod, Azure spot instance). Rejected: FR-766 (RunPod) already exists for that layer; FR-948 is LAN-scoped by charter.

## Related

- Depends on: [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) (recon precondition).
- Retires: [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) (same-commit banner update).
- Research: [FR-948.research.md](FR-948.research.md).
- Brief: [research-briefs/copilot-cli-remote-delegation-brief.md](research-briefs/copilot-cli-remote-delegation-brief.md).
- Orthogonal: [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md) (LM Studio channel, different tool).
- Precedent: CAP-30 Copilot Node (local Copilot invocation pattern).

## Judgement (pending)

To be rendered via `scripts/judge.sh` once this FR is committed. Sister session, not the author's.
