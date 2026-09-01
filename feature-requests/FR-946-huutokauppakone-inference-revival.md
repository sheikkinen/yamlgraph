# Feature Request: Revive Huutokauppakone as a managed LAN inference host

**Priority:** HIGH
**Type:** Feature + Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-01
**First consumer / first event:** the next agent session that reads `LMSTUDIO_BASE_URL` from `.env` and connects to LM Studio for inference. **First event:** the next `lmstudio-*` model in `examples/demos/judge/eval.sh` or any graph node with `provider: lmstudio` — currently broken since the endpoint address rotted.
**Research:** [FR-945.research.md](FR-945.research.md)
**Prior art:**
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) — WinRM foundation this FR uses to run the revival script; distinguished: 945 reads state, this FR changes it.
- [FR-766-runpod-provider.md](FR-766-runpod-provider.md) [Judged] — LAN-vs-cloud precedent: same `ChatOpenAI + base_url` pattern; distinguished: RunPod is billed cloud infrastructure, this is a LAN box the operator owns.
- LM Studio provider `_create_lmstudio_llm` in [yamlgraph/utils/llm_providers.py](../yamlgraph/utils/llm_providers.py) — the client code that has been silently failing; this FR does not change its API, it fixes its runtime and adds a probe.

## Summary

Two problems fixed together, both witnessed this session:

1. `.env` [LMSTUDIO_BASE_URL](../.env#L18) points at `169.254.142.62` — dead. Real host: `Huutokauppakone.local` (192.168.50.172). Repair the pointer.
2. LM Studio on Huutokauppakone is not running at boot; TCP 1234 is closed. Ship a WinRM-installed Scheduled Task that starts `lms server start` at boot, plus a client-side probe so a down endpoint fails loud instead of hanging.

## Value Statement

Agents that write `provider: lmstudio` in a graph get a working endpoint again, and the next drift is caught by a health probe instead of by a puzzled operator months later.

## Problem

- **`.env` address rot** (verified 2026-09-01): `169.254.142.62` is unreachable; `Huutokauppakone.local` resolves to `192.168.50.172` and answers ping.
- **Service not running** (verified 2026-09-01): `nc -z 192.168.50.172 1234` closed. Historical `audit.jsonl` entries from 2026-05-25 show working `lmstudio-gemma4` eval runs, so the service *worked* once and has since died with no auto-restart.
- **No client-side probe**: `_create_lmstudio_llm` in [yamlgraph/utils/llm_providers.py](../yamlgraph/utils/llm_providers.py) hands the URL to `ChatOpenAI` without touching it first; failures surface as opaque LangChain retries in the middle of a graph run.

## Ideal Result

An agent selects `provider: lmstudio`, the client probes `LMSTUDIO_BASE_URL` in <2 s, either uses it or raises a `PipelineError` naming the exact revival command. Huutokauppakone reboots and LM Studio comes back on its own.

## Proposed Solution

1. **`.env` repair** (operator reviews the diff before merge):
   - `LMSTUDIO_BASE_URL=http://169.254.142.62:1234/v1` → `http://Huutokauppakone.local:1234/v1`.
2. **Router-side static DHCP lease** on RT-AX88U for MAC `50:eb:f6:c9:bc:f6` → `192.168.50.172` (operator action; documented here so the record survives).
3. **Bootstrap script** `.github/skills/lan-recon/scripts/revive-lmstudio.ps1` — idempotent PowerShell, delivered via WinRM from FR-945:
   - Verify `lms` (LM Studio CLI) is installed; install via winget if missing. (Witnessed 2026-09-01: `lms.exe` is already on Huutokauppakone's PATH — the install step is a no-op there but must remain for greenfield hosts.)
   - Register Windows Scheduled Task `LMStudioServer`: trigger `AtStartup`, action `lms server start --port 1234 --host 0.0.0.0`, user `NETWORK SERVICE`.
   - Add Windows Firewall inbound rule for TCP 1234 scoped to `192.168.50.0/24` (LAN only). Rule display name must be ASCII (PS 5.1 ANSI-codepage constraint).
   - Start the task immediately.
   - Wait up to 30 s for TCP 1234 to answer; fail loud on timeout.
   - Emitted as pure ASCII; built-in group/account references by SID where present.
4. **Client-side probe** in `_create_lmstudio_llm` (in [yamlgraph/utils/llm_providers.py](../yamlgraph/utils/llm_providers.py)):
   - Before returning the `ChatOpenAI` instance, do a 2 s `socket.create_connection((host, port), 2)`.
   - On failure raise `PipelineError` naming the endpoint and the revival command path.
   - Guarded by `LMSTUDIO_SKIP_PROBE=1` env var for CI/offline unit runs.
5. **Documentation** in `reference/development-operations.md` § "LAN inference": names the mDNS host, the Scheduled Task, and the revival script path.

## Acceptance Criteria

- [ ] `.env` and `.env.sample` updated to `http://Huutokauppakone.local:1234/v1`.
- [ ] Static DHCP lease documented in this FR (operator confirms on router; witness a `dhcp-lease-list` line or router-UI screenshot path).
- [ ] `.github/skills/lan-recon/scripts/revive-lmstudio.ps1` present, idempotent (running twice is a no-op).
- [ ] Manual run against Huutokauppakone recorded here: task registered, port 1234 open, `curl http://Huutokauppakone.local:1234/v1/models` returns JSON.
- [ ] Endpoint survives reboot (operator verifies once; witness in FR body).
- [ ] `_create_lmstudio_llm` performs a 2 s TCP probe; test covers the timeout + actionable-message path.
- [ ] `LMSTUDIO_SKIP_PROBE=1` respected in tests; existing `tests/unit/test_lmstudio_provider.py` still green.
- [ ] `reference/development-operations.md` LAN inference section added.

## Alternatives Considered

- **Reactive-only retry inside the LangChain call** (no upfront probe). Rejected: opaque retry storms are exactly the failure mode witnessed this session.
- **Switch LM Studio for Ollama**. Rejected for this FR: separate decision, and does not solve address rot or service-not-running (would just move both problems to a new stack).
- **Delete the lmstudio provider entirely** (subtractionist option). Rejected: the audit log shows real demand from May 2026, and `lmstudio` is precedent for the `runpod` provider (FR-766) — removing it invalidates a pattern in use.

## Witnessed evidence (2026-09-01 discovery session)

- **Host capacity**: Ryzen 7 5800X (8C/16T), 24 GB RAM, NVIDIA RTX 3070 8 GB VRAM — comfortable ceiling for 7-13B parameter models. This informs `LMSTUDIO_MODEL` defaults and future model-picker heuristics.
- **`lms.exe` already installed** on `PATH` — the CLI install step will be a no-op on this host; the Scheduled-Task registration is the real payload.
- **Windows PowerShell 5.1** is the ambient PS on the host (verified in the recon transcript). All `.ps1` payloads must be authored for PS 5.1: ASCII-only, SID-not-name for groups.
- **`.env` current value** `LMSTUDIO_BASE_URL=http://169.254.142.62:1234/v1` was live at the start of the session and unreachable; the proposed replacement `http://Huutokauppakone.local:1234/v1` resolves cleanly on macOS via mDNS (verified: `ping huutokauppakone.local` → 192.168.50.172).

## Related

- Depends on: FR-945 (WinRM recon skill, uses its `pypsrp` client to deliver the revival script).
- Enables: FR-947 (remote pytest — reuses the same WinRM bootstrap pattern for OpenSSH + WSL2 install).
- Research: [FR-945.research.md](FR-945.research.md).
- Existing provider code: [yamlgraph/utils/llm_providers.py](../yamlgraph/utils/llm_providers.py).

## Judgement (pending)

To be rendered via `scripts/judge.sh` after FR-945 is committed.
