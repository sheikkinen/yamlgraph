# Feature Request: LAN recon skill (WinRM inventory of idle machines)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-01
**First consumer / first event:** an agent starting any work-delegation task (revive Huutokauppakone, provision a new LAN worker, diagnose why LM Studio is unreachable) invokes the recon skill with an mDNS name and gets a structured JSON inventory of the target host. **First event:** the next attempt to reach `192.168.50.172` after the operator ran `Enable-PSRemoting -Force` on Huutokauppakone (2026-09-01).
**Research:** [FR-945.research.md](FR-945.research.md)
**Prior art:**
- [FR-766-runpod-provider.md](FR-766-runpod-provider.md) — delegates *inference* to a remote OpenAI endpoint; distinguished: this FR delegates *reconnaissance*, no inference involved.
- [FR-902-session-worktree-lifecycle.md](FR-902-session-worktree-lifecycle.md) [Enforced] — delegates work into worktrees on the *same* machine; distinguished: this FR is the first delegation to another machine.
- [FR-411-inquisitor-watcher2-reintegration.md](FR-411-inquisitor-watcher2-reintegration.md) [Implemented] — retrieval matched on "operator/work/idle" nouns; substantively unrelated (inquisitor is a code-audit persona).
- [FR-765-graph-authoring-workflow-skill.md](FR-765-graph-authoring-workflow-skill.md) [Enforced] — precedent for adapter-enforced skill routes; the pattern this FR follows for future delegation skills.

## Summary

A `.github/skills/lan-recon/` skill that, given an mDNS name (or IP), opens a WinRM session over TCP 5985 and returns a structured JSON inventory of the host — OS, CPU, RAM, GPU, installed Python versions, WSL2 state, LM Studio service state, open localhost ports, disk free. Every subsequent work-delegation FR reads this JSON to decide "is the host ready for X?" without a human in the loop.

## Value Statement

Agents answer "is Huutokauppakone ready for X?" from a fresh, structured probe instead of asking the operator or guessing from a stale `.env` entry.

## Problem

- `.env` [LMSTUDIO_BASE_URL](../.env#L18) points at `169.254.142.62` — a dead link-local address from a prior direct-cable epoch. The real host answers at `192.168.50.172` via mDNS `Huutokauppakone.local`. Nothing detected the drift.
- The one existing LAN-delegation surface (`lmstudio` provider) has no health check — port 1234 is closed today (verified this session) and every graph node with `provider: lmstudio` will fail opaquely.
- Operator ran `Enable-PSRemoting -Force` on Huutokauppakone this session; WinRM 5985 is now open. There is no repo-side tool to use it.

## Ideal Result

An agent needs to know the state of any LAN host and runs one skill invocation. It gets back a Pydantic-validated JSON document with everything an FR-946/FR-947-class script would want to know before it acts. No hand-typed PowerShell, no guessing which IP is current.

## Proposed Solution

1. **Dependency**: add `pypsrp>=0.10` to the `[dev]` extra in `pyproject.toml`.
2. **Skill directory**: `.github/skills/lan-recon/`
   - `SKILL.md` — trigger conditions (any FR/task naming a LAN host by mDNS name; before any WinRM/SSH action against that host).
   - `recon.py` — the entrypoint.
   - `models.py` — Pydantic `LanHostInventory` schema.
3. **Behavior of `recon.py <hostname-or-ip>`**:
   - Refuses if `LAN_RECON_USER` or `LAN_RECON_PASS` env vars unset (fails loud, no guessing).
   - Resolves the name; refuses if unresolvable (no silent fallback to a cached IP).
   - Qualifies the username as `<HOSTNAME>\<user>` before opening the WinRM session; bare `user` is rejected by Windows for local (non-domain) accounts even when the password is correct.
   - Opens WinRM (HTTP 5985, `Negotiate` auth) via `pypsrp.client.Client`.
   - Runs a fixed PowerShell inventory block: `Get-CimInstance Win32_ComputerSystem`, `Win32_Processor`, `Win32_VideoController`, `Get-Service *LM*,*Ollama*,*ssh*`, `Get-NetTCPConnection -State Listen`, `wsl --status`, `py --list`, `Get-PSDrive C`, `Get-SmbShare`, `Get-SmbServerConfiguration`.
   - References built-in groups by SID (e.g. `S-1-5-32-580` for Remote Management Users) — NEVER by localized name. Windows locale is per-install (this session witnessed `Etähallinnan käyttäjät` on Finnish Windows).
   - Emits any inline PowerShell fragment (heredoc, generated `.ps1`) as pure ASCII or UTF-8 with BOM. Windows PowerShell 5.1 reads `.ps1` files with the system ANSI codepage; a bare em-dash in a comment mangles the tokenizer with a downstream "missing terminator" error that points nowhere near the actual byte.
   - Parses to `LanHostInventory`, writes `tmp/lan/<host>.json`, prints the path.
4. **Env vars** (documented in `reference/development-operations.md`):
   - `LAN_RECON_USER`, `LAN_RECON_PASS` — WinRM credentials (local Windows account with `S-1-5-32-580` membership; must NOT be an admin — recon expects `admin=False`).
5. **Tests** (`tests/unit/test_lan_recon.py`, all offline):
   - Missing credentials → `RuntimeError` with actionable message.
   - Unresolvable hostname → `RuntimeError` naming the hostname.
   - Mock WinRM response parses into `LanHostInventory` cleanly.
   - JSON output round-trips through `LanHostInventory.model_validate_json`.

```bash
# usage
LAN_RECON_USER=agent LAN_RECON_PASS=... \
  python .github/skills/lan-recon/recon.py Huutokauppakone.local
# → tmp/lan/huutokauppakone.local.json
```

## Acceptance Criteria

- [ ] `pypsrp>=0.10` in `pyproject.toml` `[dev]` extras; `pip install -e ".[dev]"` succeeds.
- [ ] `.github/skills/lan-recon/SKILL.md` describes trigger conditions per the skill contract.
- [ ] `recon.py` returns a `LanHostInventory` Pydantic model serialized to `tmp/lan/<host>.json`.
- [ ] Username is qualified as `<COMPUTERNAME>\<user>` before the WinRM handshake.
- [ ] Built-in Windows groups are looked up by SID, not localized name (regression guard for Finnish/other non-English installs).
- [ ] Any generated `.ps1` fragment passes `grep -P '[^\x00-\x7F]'` — pure ASCII — OR is emitted as UTF-8 with BOM. Test asserts one of the two.
- [ ] Refuses cleanly (non-zero exit, human-readable message) on missing credentials.
- [ ] Refuses cleanly on unresolvable hostname.
- [ ] Refuses cleanly on WinRM auth failure with actionable message naming the two most likely causes (account not in `S-1-5-32-580`; `LocalAccountTokenFilterPolicy` != 1).
- [ ] `tests/unit/test_lan_recon.py` covers the four refusal paths and the happy-path parse — all offline; the happy-path fixture is the sanitized recon log witnessed 2026-09-01 (see below).
- [ ] `reference/development-operations.md` documents `LAN_RECON_USER` / `LAN_RECON_PASS`.
- [ ] `.env.sample` gains commented `LAN_RECON_USER=` / `LAN_RECON_PASS=` lines.
- [ ] Manual verification against Huutokauppakone recorded in this FR (single-line witness with the JSON path).

## Witnessed evidence (2026-09-01 discovery session)

The recon channel was walked end-to-end by hand this session against Huutokauppakone (192.168.50.172, ASUS ROG STRIX G15DK, Ryzen 7 5800X 8C/16T, 24 GB RAM, NVIDIA RTX 3070 8 GB, Windows 10.0.26200.0 Finnish). Every AC above traces to a real event:

- **Username qualification**: bare `copilot` failed against all five auth forms; `HUUTOKAUPPAKONE\copilot` with `auth=negotiate` succeeded once group membership was fixed.
- **SID vs localized name**: `Add-LocalGroupMember -Group 'Remote Management Users'` raised `Group Remote Management Users was not found` (Finnish install names the group `Etähallinnan käyttäjät`); `Add-LocalGroupMember -SID S-1-5-32-580` succeeded.
- **ASCII-only for `.ps1`**: first fix script contained an em-dash in a comment; PS 5.1 reported `missing terminator, line 21 char 48` — nowhere near the actual U+2014 byte on line 2. Rewriting comments to ASCII resolved the parse error.
- **`LocalAccountTokenFilterPolicy`**: already `1` on this host (recon captured the value); the AC exists so the skill emits an actionable message on hosts where it isn't.
- **Successful probe**: `OK: HUUTOKAUPPAKONE | user=copilot | os=Microsoft Windows NT 10.0.26200.0 | admin=False` — non-admin least-privilege recon confirmed end-to-end.
- **Recon transcript**: 6.8 KB from `yamlgraph-recon.ps1` dropped via SMB (`\\HUUTOKAUPPAKONE\Images`) and read directly by the mac — the file-drop channel is a working parallel to WinRM and belongs in a follow-up FR.

## Alternatives Considered

- **`pwsh` + `PSWSMan` module** instead of `pypsrp`. Rejected: adds a `pwsh` runtime dependency to every dev environment; Python already required by every path in the repo.
- **SSH-based recon instead of WinRM**. Rejected for now: OpenSSH server is not yet installed on Huutokauppakone; installing it is FR-946 work. WinRM is available today.
- **Ping/nmap only**. Rejected: port state alone doesn't answer "does Windows have Python 3.11? WSL2? enough RAM?" — the questions FR-946 and FR-947 must answer.

## Related

- Depends on: nothing (foundation FR).
- Enables: FR-946 (LM Studio revival), FR-947 (remote pytest delegation).
- Research: [FR-945.research.md](FR-945.research.md).
- Brief: [research-briefs/operator-work-delegation-idle-machines-brief.md](research-briefs/operator-work-delegation-idle-machines-brief.md).

## Judgement (pending)

To be rendered via `scripts/judge.sh` after this FR is committed.
