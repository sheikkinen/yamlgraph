---
name: lan-recon
description: "Read-only WinRM inventory of an idle LAN Windows host. Use when: an FR/task needs to know 'is this LAN host ready for X?' before delegating tests, LLM inference, or agent work to it; or before FR-946/FR-947 mutation scripts run against Huutokauppakone (or a future LAN worker). Not a general remote-execution API; not a fleet manager; not a mutation surface."
argument-hint: "target hostname/IP (plus --computer-name for IP inputs), e.g. `Huutokauppakone.local` or `192.168.50.172 --computer-name HUUTOKAUPPAKONE`"
---

# LAN recon skill (FR-945, REQ-YG-635)

Read-only WinRM inventory of a single LAN Windows host. Emits a
Pydantic-validated `LanHostInventory` JSON document at
`tmp/lan/<safe-slug>.json`.

## Scope contract (frozen by FR-945 judgement C-1..C-7)

- **Read-only.** The skill never mutates users, groups, policy, services,
  software, firewall, shares, scheduled tasks, SSH, WSL, Python, LM
  Studio, or `.env`. Mutation belongs to FR-946 / FR-947.
- **Non-admin.** The probing account must NOT be a local administrator;
  a returned `admin=true` raises `AdminNotAllowedError`.
- **LAN targets only.** RFC1918 / CGN 100.64.0.0/10 / IPv4 link-local /
  IPv6 ULA / IPv6 link-local. Public/loopback/multicast targets refused.
- **Pinned resolution.** DNS is consulted once; the resolved address is
  used verbatim for the WinRM handshake and never re-resolved.
- **Transport Option A (per FR-945 § 4).** HTTP 5985 + `auth="negotiate"`
  + `encryption="always"` + explicit finite timeouts. Basic and CredSSP
  auth are structurally absent from the code path.
- **Safe output.** `tmp/lan/<safe-slug>.json`; slug cannot escape the
  directory; JSON is Pydantic-validated before atomic write.

## Invocation

```bash
# DNS/mDNS target — computer name derived from leftmost label
python .github/skills/lan-recon/recon.py Huutokauppakone.local

# IP literal target — --computer-name required
python .github/skills/lan-recon/recon.py 192.168.50.172 \
    --computer-name HUUTOKAUPPAKONE
```

## Prerequisites

- `pip install -e ".[dev]"` (pypsrp is in the dev extra).
- Environment variables (set in `.env`, never committed):
  - `LAN_RECON_USER` — bare local Windows username (e.g. `copilot`).
    Recon qualifies it as `<COMPUTERNAME>\<user>` before the handshake.
    Already-qualified values are refused; domain accounts are out of scope in v1.
  - `LAN_RECON_PASS` — Windows account password.
- Target Windows host:
  - WinRM listener on TCP 5985 (`Enable-PSRemoting -Force`).
  - Account is a member of SID `S-1-5-32-580` ("Remote Management
    Users"; locale-dependent name — Finnish install: "Etähallinnan
    käyttäjät"). Always reference this group by SID, never by
    localized string.

## Refusal contract (12 typed errors)

1. `MissingCredentialError` — `LAN_RECON_USER` or `LAN_RECON_PASS` unset.
2. `MissingCredentialError` — same, for the other var.
3. `UnsafeTargetError` — target resolves to a public address.
4. `UnsafeTargetError` — target resolves to loopback/multicast/unspecified.
5. `UnresolvableTargetError` — DNS returns NXDOMAIN or empty.
6. `MissingComputerNameError` — IP literal without `--computer-name`, or
   a DNS name whose leftmost label isn't a valid Windows COMPUTERNAME.
7. `ComputerNameMismatchError` — post-handshake `$env:COMPUTERNAME`
   differs from the selected name.
8. `WinRMAuthError` — authentication failed; message names credentials
   and `S-1-5-32-580` membership as the two likely causes. Password is
   scrubbed from the message and captured logs.
9. `WinRMTimeoutError` — connect or operation timeout.
10. `InventoryParseError` — `inventory.ps1` emitted non-JSON.
11. `InventoryParseError` — JSON did not validate against
    `LanHostInventory`.
12. `UnsafeSlugError` — output slug would escape `tmp/lan/`.

Plus: `AdminNotAllowedError` — the probing account returned `admin=True`
(least-privilege contract).

## Output

Successful invocation prints two lines to stdout:

```
tmp/lan/huutokauppakone.local.json
host=HUUTOKAUPPAKONE admin=False rmu=True cpu=AMD Ryzen 7 5800X 8-Core Processor ram_gb=23
```

The full validated `LanHostInventory` is at the path shown on line 1.
`tmp/lan/**` is git-ignored (line 2 is a human sanity check).

## What this skill is NOT

- Not a general remote-execution API (see FR-946/FR-947).
- Not a service manager or bootstrap tool (FR-946 mutates LM Studio;
  FR-947 installs OpenSSH + WSL2).
- Not an SMB/file-drop channel (deferred to a future FR-948).
- Not a multi-host fleet inventory. It probes ONE host per invocation.
