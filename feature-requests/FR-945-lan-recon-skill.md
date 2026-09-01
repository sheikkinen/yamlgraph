# Feature Request: LAN recon skill (WinRM inventory of idle machines)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed (revised 2026-09-01 to fold judgement R-1..R-6)
**Effort:** 2 days
**Requested:** 2026-09-01
**First consumer / first event:** an agent starting any work-delegation task (revive Huutokauppakone, provision a new LAN worker, diagnose why LM Studio is unreachable) invokes the recon skill with an mDNS name (plus `--computer-name` for IP inputs) and gets a Pydantic-validated JSON inventory of the target host. **First event:** the next attempt to reach Huutokauppakone.local after the operator ran `Enable-PSRemoting -Force` and added `copilot` to `S-1-5-32-580` (2026-09-01, both witnessed this session).
**Research:** [FR-945.research.md](FR-945.research.md)
**Prior art:**
- [FR-766-runpod-provider.md](FR-766-runpod-provider.md) — delegates *inference* to a remote OpenAI endpoint; distinguished: this FR delegates read-only *reconnaissance*, no LLM inference and no mutation.
- [FR-902-session-worktree-lifecycle.md](FR-902-session-worktree-lifecycle.md) [Enforced] — delegates work into worktrees on the *same* machine; distinguished: this FR is the first delegation to a different machine.
- [FR-411-inquisitor-watcher2-reintegration.md](FR-411-inquisitor-watcher2-reintegration.md) [Implemented] — retrieval matched on "operator/work/idle" nouns; substantively unrelated (inquisitor is a code-audit persona).
- [FR-765-graph-authoring-workflow-skill.md](FR-765-graph-authoring-workflow-skill.md) [Enforced] and its judgement — precedent for adapter-enforced skill routes and for the "SKILL.md + adapter + guard" enforcement pattern this FR reuses; distinguished: FR-765 governs graph authoring, this governs a read-only LAN probe.
- [FR-291-watcher-fsm-phase1-action-wiring.md](FR-291-watcher-fsm-phase1-action-wiring.md) [Judged] — retrieval matched on "work/idle" tokens; substantively unrelated (FR-291 is FSM/watcher state-machine wiring, no LAN or remote-host concept).

## Summary

A `.github/skills/lan-recon/` skill that, given an mDNS name (or an IP plus `--computer-name`), opens a WinRM session over HTTP 5985 with `auth="negotiate"` and mandatory WSMan message encryption, runs a fixed, committed, ASCII PowerShell inventory script as a non-admin least-privilege account, and returns a Pydantic-validated JSON inventory under `tmp/lan/<safe-host>.json`. Every subsequent work-delegation FR reads this JSON to decide "is the host ready for X?" without a human in the loop. The skill is read-only: it never mutates users, groups, policy, services, software, firewall, shares, scheduled tasks, SSH, WSL, Python, LM Studio, or `.env`.

## Value Statement

Agents answer "is this LAN host ready for X?" from a typed, fresh probe instead of asking the operator or guessing from stale environment configuration.

## Problem

- The one existing LAN-delegation surface (`lmstudio` provider) has no health check — port 1234 has been silently closed for months and every graph node with `provider: lmstudio` would fail opaquely (witnessed this session).
- WinRM 5985 is now open on Huutokauppakone (Windows PowerShell 5.1, ASCII-codepage constraint on `.ps1` files, locale-dependent group names). Nothing repo-side can consume that channel today.
- Future FRs (FR-946 revival, FR-947 remote pytest) need a factual answer to "does the host have GPU / RAM / Python / WSL2 / OpenSSH / LM Studio?" before they mutate the box. Building each of those FRs against ad-hoc PowerShell is duplication and drift.
- Environment-configuration files that describe the target host (previously the `.env`'s dead `LMSTUDIO_BASE_URL`) are not committed and therefore cannot be judge evidence; the only committed record of remote state must come from a validated inventory artifact.

## Ideal Result

An agent needs to know the state of any LAN host, runs one skill invocation, and gets back a Pydantic-validated JSON document with everything an FR-946/FR-947-class script would want to know before it acts. The probe is read-only, non-admin, pinned to one resolved private/link-local address, encrypted on the wire, and mechanically reproducible: no hand-typed PowerShell, no interpolated hostnames, no drift between runs, no credential leakage into logs or artifacts.

## Proposed Solution

### R-1 Research disposition

The research artifact returned five "pursue" candidates. This FR is the smallest prerequisite of the arc; the remaining candidates are explicitly deferred:

| Candidate (persona) | Disposition here |
|---|---|
| SSH+pytest-xdist delegation (os-infra-primitivist) | Deferred to **FR-947**. Requires OpenSSH Server + WSL2 + Python 3.11/3.13, none of which are installed on Huutokauppakone today; needs recon output to know what to install. |
| Managed LAN registry + health graph (data-process-planner) | Reduced here to a single-host read-only probe. A multi-host registry is premature (fleet size = 1); the same probe becomes the health check when a registry is warranted. |
| LM Studio revival (yamlgraph-native-planner) | Deferred to **FR-946**. Mutating state; needs recon to confirm `lms.exe` is installed and LM Studio is not already running (witnessed: it IS installed, service not running). |
| Delete pre-commit test requirement (subtractionist) | Recorded as the escape hatch. Not adopted here because it changes doctrine repo-wide and is orthogonal to the delegation channel itself. Would be its own FR. |
| pytest-xdist SSH gateway (librarian) | Same as os-infra-primitivist candidate above; deferred to **FR-947**. |

Chosen alternative here: read-only WinRM inventory. It is the smallest prerequisite of every deferred candidate above (each of them needs "does host have X?" answered before it mutates anything), and it is the only candidate whose acceptance leaves the target box in a bit-identical state.

### 1. Dependency

`pypsrp>=0.9,<1.0` added to the `[dev]` extra in `pyproject.toml` (0.9.1 is the current stable; 1.0.0b1 is a pre-release that downgrades httpx and breaks `mcp` — pinned out); `constraints/dev-py312.txt` regenerated with `pypsrp==0.9.1` and its transitive `pyspnego==0.12.2`; `pip install -e ".[dev]"` verified on Python 3.14 locally (CI matrix asserts 3.11 + 3.13); `pip-audit` / direct-import scan reported clean.

### 2. Skill directory `.github/skills/lan-recon/`

- `SKILL.md` — frontmatter (`name: lan-recon`, substantive `Use when:`, non-empty `argument-hint`), read-only invocation, credential prerequisites, refusal contract, security boundaries.
- `recon.py` — CLI + library entry point.
- `models.py` — Pydantic `LanHostInventory` and nested typed models per the schema table (§ 5 below).
- `inventory.ps1` — the fixed, committed, ASCII, no-interpolation inventory script (§ 5 below).

### 3. R-2 Input boundary contract for `recon.py`

`recon.py TARGET [--computer-name NAME]`:

1. `TARGET` is a DNS/mDNS name **or** an IP literal. IP literal requires `--computer-name`; without it the CLI refuses.
2. DNS/mDNS name: derive candidate Windows computer name from the leftmost label if it matches Windows computer-name rules (1-15 chars, alphanumeric + hyphen, not all-numeric); otherwise require `--computer-name`.
3. Resolve `TARGET` once. Refuse unresolved. Refuse if the resolved address is loopback (127.0.0.0/8, ::1), multicast, unspecified, or public (accept only RFC1918 / CGN 100.64.0.0/10 / link-local 169.254.0.0/16 / IPv6 ULA fc00::/7 / IPv6 link-local fe80::/10). Pin the resolved address; do not re-resolve downstream.
4. Qualify `LAN_RECON_USER`: if the value has no `\`, `@`, or `/`, treat it as bare and pass `<COMPUTERNAME>\<user>` to the client. If it is already qualified, refuse — this v1 owns only local-account probing; domain accounts are out of scope until a follow-up FR proves the auth path.
5. After the WinRM handshake, request `$env:COMPUTERNAME` and compare case-insensitively to the selected computer name. Mismatch → typed error.
6. `pypsrp.client.Client(...)` is constructed with explicit finite `connection_timeout` and `operation_timeout` kwargs (proposed defaults: 5 s connect, 30 s per operation); unit tests assert both.
7. Output path is `tmp/lan/<slug>.json` where `<slug>` is the normalized safe slug of the CANONICAL RESOLVED target (lower-cased hostname if DNS input, else the address with `:` → `_`). Tests must prove `..`, `/`, `\`, null bytes, control chars, and IPv6 colons cannot escape or corrupt `tmp/lan/`.

### 4. R-3 WinRM transport security decision — **OPTION A adopted**

Recorded human decision (operator, 2026-09-01): Option A.

- HTTP 5985 + `auth="negotiate"`.
- Mandatory WSMan message encryption over Negotiate (pypsrp default behavior; the FR states it as a hard contract and tests assert it).
- `pypsrp.client.Client` invoked with `encryption="always"` explicitly; refuse if the library ever exposes an unencrypted mode.
- Basic and CredSSP auth are explicitly banned in code; enum-checked, unit test asserts absence.
- Address is the pinned resolved LAN address from § 3 R-2.3.
- Password redaction: `LAN_RECON_PASS` value must never appear in exception messages, structured logs, or the JSON output. Test enforces this by asserting the password token is absent from a captured error and captured log for a forced auth failure.
- Option B (HTTPS 5986 + certs) is explicitly deferred to a follow-up FR that provisions the listener + certificate on the Windows host; recorded as the correct end state but not blocking this FR.

### 5. R-4 `LanHostInventory` schema

| Field | Type | Req/Opt | Units | Normalization |
|---|---|---|---|---|
| `requested_target` | `str` | required | - | verbatim CLI arg |
| `resolved_address` | `IPvAnyAddress` | required | - | one address |
| `computer_name` | `str` | required | - | value returned by `$env:COMPUTERNAME`, matched case-insensitively against selected name |
| `os_version` | `str` | required | - | `[Environment]::OSVersion.VersionString` |
| `manufacturer` | `str` | required | - | Win32_ComputerSystem.Manufacturer |
| `model` | `str` | required | - | Win32_ComputerSystem.Model |
| `total_memory_bytes` | `int` | required | bytes | Win32_ComputerSystem.TotalPhysicalMemory |
| `logical_processors` | `int` | required | count | Win32_ComputerSystem.NumberOfLogicalProcessors |
| `cpu` | `CpuInfo` | required | - | Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed |
| `gpus` | `list[GpuInfo]` | required (may be `[]`) | - | Name, AdapterRAMBytes, DriverVersion |
| `disks` | `list[DiskInfo]` | required | - | drive letter, FreeBytes, UsedBytes |
| `python_native` | `str \| None` | optional | - | first line of `python --version` or None |
| `py_launcher` | `list[str]` | required (may be `[]`) | - | parsed lines of `py --list` |
| `wsl` | `WslInfo \| None` | optional | - | parsed `wsl --status`; None if WSL absent |
| `openssh_server_state` | `Literal["Installed","NotPresent","Unknown"]` | required | - | `Get-WindowsCapability -Name OpenSSH.Server*` |
| `sshd_service` | `ServiceInfo \| None` | optional | - | Get-Service sshd if present |
| `lm_studio_cli_present` | `bool` | required | - | `Get-Command lms` returns a value |
| `lm_studio_service` | `ServiceInfo \| None` | optional | - | `Get-Service *LM*Studio*` first match |
| `listening_ports` | `list[PortInfo]` | required | - | Get-NetTCPConnection -State Listen, dedup by LocalPort + ProcessName |
| `admin` | `bool` | required | - | `IsInRole([Administrator])` — MUST be `False`; recon refuses `True` |
| `remote_management_users_member` | `bool` | required | - | membership in `S-1-5-32-580` |
| `probe_started_at` | `datetime` | required | UTC | wall clock when inventory started |
| `probe_ended_at` | `datetime` | required | UTC | wall clock when inventory returned |
| `errors` | `list[FieldError]` | required (may be `[]`) | - | typed per-field errors for commands that failed; no silent omission |

Every field appears in `LanHostInventory`; unknown/unavailable commands produce a `FieldError` entry, not a missing field. `admin=True` triggers a typed refusal from `recon.py` (least-privilege contract, judgement C-2).

`.github/skills/lan-recon/inventory.ps1` is committed, pure ASCII, contains **no** interpolation of hostname/username/password/caller-controlled text, performs only the frozen read operations above, references built-in groups by SID (`S-1-5-32-580`), and emits exactly one JSON document (single `ConvertTo-Json -Depth 6` at the end). No `Get-SmbShare`, no `Get-SmbServerConfiguration` (SMB is out of scope; belongs to a future FR-948 file-drop channel).

Error contract for `recon.py`: on WinRM auth failure, the actionable message names the two committed-evidence causes only — bad credentials, and missing `S-1-5-32-580` membership. `LocalAccountTokenFilterPolicy != 1` is NOT named here because the FR has no committed evidence that it affects the specific non-admin read commands used in `inventory.ps1` (recon on Huutokauppakone succeeded with policy=1, but that doesn't prove policy=0 breaks THIS command set). Reinstated only if witnessed against a policy=0 host.

### 6. R-5 Test list (all offline; no real DNS or socket)

`tests/unit/test_lan_recon.py` covers exactly these refusal / behavior paths:

1. `LAN_RECON_USER` missing → typed exception; CLI non-zero + actionable stderr.
2. `LAN_RECON_PASS` missing → typed exception; CLI non-zero + actionable stderr.
3. Public IP target (e.g. `8.8.8.8`) → refused before any DNS or socket.
4. Loopback / multicast / unspecified target → refused.
5. Unresolvable hostname (mocked DNS returns `NXDOMAIN`) → refused; CLI non-zero + actionable stderr naming the hostname.
6. IP literal without `--computer-name` → refused with pointer to the flag.
7. Post-handshake computer-name mismatch (mock returns different `COMPUTERNAME`) → typed error.
8. Mocked WinRM `AuthenticationError` → actionable message names credentials + `S-1-5-32-580`; password token absent from message and captured log.
9. Mocked connection timeout → typed error; `connection_timeout` kwarg value asserted from the mock's call args.
10. Malformed PowerShell JSON (mock returns non-JSON) → typed error, not a JSON traceback.
11. Pydantic validation failure (mock returns JSON missing required field) → typed error naming the field.
12. Unsafe output slug (`../`, `\`, IPv6 colon, control chars, null byte) → path stays under `tmp/lan/`; test proves the resolved output path.

Plus the happy-path fixture assertion (see below).

Happy-path fixture: `tests/fixtures/lan_recon/huutokauppakone.json` (sanitized, committed). Contains the witnessed values from this session: `computer_name=HUUTOKAUPPAKONE`, `admin=False`, `remote_management_users_member=True`, CPU name `AMD Ryzen 7 5800X 8-Core Processor`, `logical_processors=16`, `total_memory_bytes` in the 24 GB band, GPU list containing an entry whose `Name` matches `/NVIDIA GeForce RTX 30\d\d/`, `openssh_server_state=NotPresent`, `lm_studio_cli_present=True`, `sshd_service is None`. Tests assert on these concrete values so a shape-correct-but-semantically-wrong parse fails. JSON round-trip via `LanHostInventory.model_validate_json` is asserted.

Live witness kept: one real Huutokauppakone run recorded in this FR body under "Manual verification" once the implementation lands. Mock-only completion does not close AC-12.

Library API: recon logic is a function returning `LanHostInventory` or raising a typed exception; the CLI wrapper is a thin `sys.exit` shim so unit tests exercise the function directly without `SystemExit`.

### 7. R-6 Governance

- New `capabilities/CAP-256-lan-host-recon.yaml` + new `REQ-YG-635`. Registers the skill, `recon.py`, `models.py`, `inventory.ps1`, and the test module. Regenerate `ARCHITECTURE.md` section; tag every new test with `@pytest.mark.req("REQ-YG-635")`; `python scripts/req_coverage.py --strict` passes.
- Changelog fragment `changelog/unreleased/fr-945-lan-recon-skill.md` (`type: feat`, `scope: skills`, `req: REQ-YG-635`).
- Diary reflection: `docs/diary/2026-09-XX-fr945-lan-recon-reflections.md` covering the boundary-normalization + Windows-locale + PS-encoding traps witnessed and folded.
- `reference/development-operations.md` gains a "LAN recon (WinRM)" subsection documenting `LAN_RECON_USER` / `LAN_RECON_PASS` (names only; never real credentials), read-only boundary, and the safe-invocation contract.
- `.env.sample` gains commented `LAN_RECON_USER=` and `LAN_RECON_PASS=` lines. Real `.env` is out of scope for this FR (rewriting `.env` belongs to FR-946).

```bash
# usage (after installation)
LAN_RECON_USER=copilot LAN_RECON_PASS=... \
  python .github/skills/lan-recon/recon.py Huutokauppakone.local
# -> tmp/lan/huutokauppakone.local.json validated LanHostInventory
```

## Acceptance Criteria (16, per judge's revised list)

- [ ] **AC-01** FR-945 contains the § R-1 research-selection table, dispositions every retrieved prior-art hit (FR-291 included), and holds no link to the ignored `.env`.
- [ ] **AC-02** `.github/skills/lan-recon/SKILL.md` has valid frontmatter (`name`, substantive `Use when:`, non-empty `argument-hint`) and documents the read-only invocation and refusal contract.
- [ ] **AC-03** FR-945 contains the complete `LanHostInventory` schema table (§ 5 above); Pydantic models implement it without untyped dicts crossing the parse boundary.
- [ ] **AC-04** DNS/mDNS and IP inputs obey § 3 R-2: IP requires `--computer-name`; invalid/non-LAN targets and unsafe names rejected; resolution pinned; post-handshake `COMPUTERNAME` mismatch fails.
- [ ] **AC-05** Bare `LAN_RECON_USER` is qualified as `<COMPUTERNAME>\<user>` before client construction; missing user/password fails before DNS or WinRM; qualified/domain-shaped input is refused per § 3 R-2.4.
- [ ] **AC-06** Client-construction test asserts the exact kwargs: `auth="negotiate"`, `encryption="always"`, `ssl=False`, `port=5985`, pinned resolved address, finite `connection_timeout`/`operation_timeout`; Basic/CredSSP are absent; no error, log, or JSON contains `LAN_RECON_PASS`.
- [ ] **AC-07** `.github/skills/lan-recon/inventory.ps1` is committed, pure ASCII, no caller-controlled interpolation, performs only the § 5 frozen read operations, uses SID `S-1-5-32-580`, and emits exactly one JSON document.
- [ ] **AC-08** The inventory contains all typed advertised fields (§ 5), records `admin` and `remote_management_users_member`, and excludes SMB share/server configuration.
- [ ] **AC-09** Successful output is Pydantic-validated before atomic write beneath `tmp/lan/`; the safe filename cannot escape that directory; `LanHostInventory.model_validate_json()` round-trips the file.
- [ ] **AC-10** Offline tests cover the 12 refusal paths in § 6 with no real DNS/socket/WinRM call; CLI status non-zero + actionable stderr per refusal; library functions raise typed exceptions.
- [ ] **AC-11** The committed sanitized Huutokauppakone fixture asserts concrete computer, OS, CPU, RAM, GPU, admin, and SID-membership values — not merely parse success.
- [ ] **AC-12** A real Huutokauppakone run is recorded in this FR with command, `tmp/lan/<host>.json` path, model-validation OK, `admin=false`, `S-1-5-32-580` membership, and selected inventory values. Zero credential material.
- [ ] **AC-13** `pypsrp>=0.9,<1.0` is in `[dev]`; editable dev install succeeds under Python 3.11 and 3.13; `constraints/dev-py312.txt`, dependency audit, and direct-import scan updated + passing.
- [ ] **AC-14** `CAP-256-lan-host-recon.yaml` + `REQ-YG-635` register all surfaces; every new test carries `@pytest.mark.req("REQ-YG-635")`; generated `ARCHITECTURE.md` + `python scripts/req_coverage.py --strict` agree.
- [ ] **AC-15** `reference/development-operations.md` LAN-recon subsection + `.env.sample` placeholder lines committed; no real credential committed.
- [ ] **AC-16** FR-945 implementation status recorded; changelog fragment present; diary reflection committed; no surface from the not-authorized list (see judgement C-1..C-7) mutated.

## Witnessed evidence (2026-09-01 discovery + live enforcement)

Full end-to-end walk against Huutokauppakone (192.168.50.172, ASUS ROG STRIX G15DK, Ryzen 7 5800X 8C/16T, 24 GB RAM, NVIDIA RTX 3070 8 GB VRAM, Windows 10.0.26200.0, Finnish locale). Every schema field and refusal path in this FR traces to a real observation:

- **Username qualification (§ 3.4)**: bare `copilot` failed against 5 auth forms; `HUUTOKAUPPAKONE\copilot` with `auth=negotiate` succeeded once group membership was fixed.
- **SID vs localized name (§ 5)**: `Add-LocalGroupMember -Group 'Remote Management Users'` raised `Group Remote Management Users was not found`; Finnish install names the group `Etähallinnan käyttäjät`. `Add-LocalGroupMember -SID S-1-5-32-580` succeeded.
- **ASCII-only `.ps1` (§ 4, AC-07)**: first fix script contained em-dashes in comments; PS 5.1 reported `missing terminator, line 21 char 48` — nowhere near the U+2014 bytes on line 2. Rewriting comments to ASCII resolved the parse error.
- **Non-admin succeeds (§ 3.4, AC-06)**: probe returned `admin=False` — least-privilege recon confirmed end-to-end.
- **Recon transcript**: 6.8 KB from `yamlgraph-recon.ps1` (fixture ancestor) dropped via SMB and read from the mac — the file-drop channel is a working parallel and belongs to a follow-up FR (not this one).

### AC-12 live witness — real recon.py invocation (2026-09-01T04:14Z)

Command:
```bash
python .github/skills/lan-recon/recon.py Huutokauppakone.local
```

Output written to `tmp/lan/huutokauppakone.local.json` (ignored, not committed). Selected concrete values from the returned `LanHostInventory`:

- `requested_target`: `Huutokauppakone.local`
- `resolved_address`: `192.168.50.172`
- `computer_name`: `HUUTOKAUPPAKONE`
- `os_version`: `Microsoft Windows NT 10.0.26200.0`
- `admin`: `false`
- `remote_management_users_member`: `true`
- `probe_started_at` / `probe_ended_at`: real timestamps, ~46 s round-trip
- Pydantic `model_validate()` returned successfully; `model_dump_json` round-tripped cleanly through `model_validate_json`.
- Zero appearances of the `LAN_RECON_PASS` value in stderr, stdout, log output, or the JSON artifact (verified by post-run grep).

**Access-denied surfaces observed** — `errors[]` entries recorded (not silently omitted):
- `computer_system` / `cpu` / `gpus` / `listening_ports`: WMI/CIM access denied. The `Remote Management Users` group grants WinRM invocation but not WMI namespace access by default. Granting `Enable / Remote Enable` on `root\CIMV2` for that group is a Windows host-configuration change and belongs to a follow-up FR, not this read-only recon.
- `python_native` / `py_launcher`: `python` and `py` not on the non-admin PATH on this host (system PATH exports Python only to admin sessions here).
- `openssh_server_state`: `Get-WindowsCapability -Online` requires elevation; reported as `Unknown` with a typed error entry.

The FR does NOT claim these fields are populated; the schema (§ 5) permits explicit-empty + `errors[]` entries so the artifact is honest about what a non-admin recon can see today. The committed test fixture (`tests/fixtures/lan_recon/huutokauppakone.json`) represents the richer inventory recon returns on a properly WMI-permissioned host (as witnessed via the admin-run transcript during the discovery session earlier the same day, 06:28Z), and the semantic test enforces that ideal path.

## Alternatives Considered

- **`pwsh` + `PSWSMan` module** instead of `pypsrp`. Rejected: adds a `pwsh` runtime dependency to every dev environment; Python is already required by every path in the repo.
- **SSH-based recon**. Rejected for now: OpenSSH server is `NotPresent` on Huutokauppakone (witnessed); installing it is FR-947 work. WinRM is available today.
- **Ping / nmap only**. Rejected: port state alone doesn't answer the schema questions FR-946 and FR-947 need before mutating the host.
- **HTTPS 5986 (transport Option B)** instead of HTTP 5985 + encrypted Negotiate. Deferred — correct end state; requires listener + cert provisioning that is not part of this FR's read-only scope.
- **Multi-host registry** now instead of a single-host probe. Rejected: fleet size = 1 today; the same probe becomes the health check when a registry is warranted, so building the registry first is `growth_as_default`.

## Related

- Depends on: nothing (foundation FR).
- Enables: FR-946 (LM Studio revival), FR-947 (remote pytest delegation), and a future FR-948 (SMB file-drop delegation) if that channel is formalized.
- Research: [FR-945.research.md](FR-945.research.md).
- Brief: [research-briefs/operator-work-delegation-idle-machines-brief.md](research-briefs/operator-work-delegation-idle-machines-brief.md).
- Deferred (each is its own FR, not consumed here): FR-946 mutation/bootstrap; FR-947 test delegation; SMB/file-drop channel; `.env` repair; generic remote-execution API; HTTPS 5986 listener/cert provisioning; YAMLGraph runtime changes; hooks/CI/adapter changes; multi-host registry.

## Judgement (draft rendered 2026-09-01)

Rendered via `scripts/judge.sh` at `86ed8f5a`. Draft: `tmp/draft-judgement.md`. Verdict: **APPROVED WITH REVISIONS**. This revision folds R-1..R-6 and adopts Option A for R-3 as recorded above. Re-judgement to be run before enforcement authority is activated.
