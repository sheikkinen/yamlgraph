---
type: feat
scope: skills
req: REQ-YG-635
---
- **FR-945 LAN recon skill**: New `.github/skills/lan-recon/` — read-only WinRM inventory of a single LAN Windows host (Option A transport: HTTP 5985 + `auth="negotiate"` + `encryption="always"` + banned Basic/CredSSP + pinned resolved LAN address + explicit finite timeouts). Given a DNS/mDNS name or an IP literal + `--computer-name`, opens `pypsrp.client.Client`, runs a fixed pure-ASCII `inventory.ps1` as a non-admin account (SID `S-1-5-32-580` for Remote Management Users — locale-safe against Finnish `Etähallinnan käyttäjät`), and returns a Pydantic `LanHostInventory` under `tmp/lan/<safe-slug>.json`. Refuses admin=True response, non-LAN targets, unqualified IP inputs, unsafe slugs; `LAN_RECON_PASS` scrubbed from every error, log record, and artifact. Foundation FR of the LAN work-delegation arc (FR-946, FR-947). New capability `CAP-256-lan-host-recon` with 12 offline refusal tests + witnessed Huutokauppakone fixture. (REQ-YG-635)
