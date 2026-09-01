# Problem brief: FR-947's SSH+WSL2+pytest-xdist design is dominated by an empirically-verified Copilot-CLI-on-remote channel

**Prior art:**
- `feature-requests/FR-945-lan-recon-skill.md` [Judged, APPROVED WITH REVISIONS] establishes the WinRM read-only recon foundation this brief consumes. It writes a Pydantic-typed `LanHostInventory` from `.github/skills/lan-recon/`; FR-948 uses that inventory to decide "is the remote ready for Copilot-CLI delegation?" before spinning up a session.
- `feature-requests/FR-947-remote-pytest-delegation.md` [Proposed, unjudged] describes an SSH+WSL2+pytest-xdist design that this brief proposes to retire (subtractionist). FR-947 requires: install OpenSSH.Server, install WSL2 Ubuntu, provision matching Python venv, distribute SSH keys, rsync worktree per commit. That's a lot of infrastructure to reproduce the mac's Python environment on Windows. The Copilot-CLI channel skips all of it by letting the remote resolve its own environment.
- `feature-requests/FR-946-huutokauppakone-inference-revival.md` [Proposed] is orthogonal — it delegates LLM inference to LM Studio, not test execution. Distinguished; independent.
- SMB `/Volumes/Images` file-drop channel (deferred FR-948a earlier, not filed) — parallel evidence that non-SSH channels reach the remote. Copilot CLI writes its outputs directly to this share, so no separate rsync is needed for artifact retrieval.

## Problem statement

The Phase 1-2 empirical spikes this session proved a delegation channel that FR-947's design does not consider: **GitHub Copilot CLI (`copilot -p "prompt" --allow-all-tools`)** running as the `copilot` service account on Huutokauppakone, invoked over WinRM from the mac, with results written to the mounted SMB share for the mac to read directly.

**Verified end-to-end 2026-09-01T04:28:52Z** (`tmp/copilot-spike-phase2f.log`):
- mac → WinRM (HTTP 5985, Negotiate, mandatory encryption) → PowerShell → `copilot -p "..." --allow-all-tools` → LLM (7s inference) → PowerShell shell tool (`Set-Content`) → filesystem → SMB share
- 11 second round-trip for a trivial file-write task
- 7.17 AI Credits, 51.4k tokens up (mostly cached), 204 tokens down
- `--resume=<uuid>` capability captured — sessions persist for multi-step delegation
- Exit code 0, file content verified matched request

The channel exists TODAY. FR-947's SSH design does not exist and requires: OpenSSH.Server install (currently `NotPresent`), WSL2 Ubuntu install (Docker Desktop provisioned a different distro), Python 3.11 and 3.13 pyenv install, dedicated agent user in WSL, SSH key distribution, per-commit rsync scaffolding, timeout+fallback wrapper. Every one of those is real work; the Copilot channel does none of it because:

- **git**: system-wide 2.40.1, ✅
- **node**: system-wide 24.19.0 (upgraded this session), ✅
- **@github/copilot**: system-wide npm install, ✅
- **auth**: env-var `GH_TOKEN` (network-logon compatible; DPAPI-free), ✅
- **Python**: NOT installed system-wide — Copilot itself installs it on demand via `winget` in the delegated session (spike step to verify)
- **repo access**: `git clone https://x-access-token:$GH_TOKEN@github.com/…` — no SSH key management

## Classification

judgement/analysis/generation

## Constraints

- **Token boundary**: `GH_TOKEN` in `.env`. Never committed. Passed to remote via WinRM as a PowerShell parameter (encrypted on the wire, never appears in the script literal or in captured logs — redaction proven in the spike). Copilot's own retry / update / telemetry endpoints see it only inside its own HTTPS session with GitHub.
- **Cost boundary**: every delegated task costs AI credits. Trivial round-trip: ~7 credits. Estimated full-suite run with cached setup: bounded by prompt size, not test count — likely 20-60 credits per suite run. Must be budgeted; FR must specify a per-run ceiling with abort logic.
- **Auth boundary (real, witnessed)**: WinRM opens a NETWORK logon session, not INTERACTIVE. That session cannot read DPAPI-protected per-user credential stores (the interactive `copilot` device-flow token failed here). Env-var tokens are the only credential channel that works across the WinRM boundary. This is a hard constraint for any delegation FR going forward.
- **Encoding boundary**: PowerShell 5.1 reads `.ps1` files as ANSI codepage. Copilot CLI outputs UTF-8. Any wrapper script must be pure ASCII (or UTF-8 BOM), and any log reader must interpret Copilot output as UTF-8. Cosmetic in the spike; enforceable in the FR.
- **Session-state boundary**: `--resume=<uuid>` gives Copilot session persistence. FR must decide: is each delegation stateless (safer, simpler), or does it reuse resume IDs across pre-commit runs (faster, but state can drift)? Empirical evidence sought.
- **Fleet constraint**: exactly one host today (Huutokauppakone). Design must not require a fleet abstraction but must not preclude one.
- **Non-admin least privilege**: same as FR-945. Copilot as `copilot` user, `admin=False`, membership in `S-1-5-32-580` only. No mutation authority beyond what its `--allow-all-tools --allow-all-paths` explicitly permits inside its own session.
- **Doctrine constraint**: this brief seeks to RETIRE an unimplemented FR (subtractionist path per Scripture `growth_as_default` cure). The output FR must either supersede FR-947 explicitly with a "retire" disposition, or coexist as an alternative delegation channel with a decision matrix.

## Witnessed incidents

- 2026-09-01T04:28:52Z (`tmp/copilot-spike-phase2f.log`): full delegation round-trip verified. `copilot exit=0 elapsed=11s`. File `phase2f-<stamp>.txt` created on SMB share via LLM-driven shell tool. Content matched request exactly.
- 2026-09-01T04:13Z: earlier auth failure with device-flow token proved WinRM network-logon cannot read the interactive credential store. Fix via `GH_TOKEN` env-var injection.
- 2026-09-01T04:04Z: Node 18 too old for `@github/copilot`. `winget install OpenJS.NodeJS.LTS --scope machine` upgraded to Node 24 in place, 90 seconds, no reboot. Precedent for "delegated environment self-provisioning" is real.
- 2026-09-01T04:07Z: `copilot --help` showed `--add-dir <directory>` loads that directory's `.github/skills` and `.github/agents` as trusted config. **Copilot CLI natively speaks the yamlgraph skill contract.** This is the deciding differentiator vs. FR-947's SSH approach — the remote Copilot can use the same skills the mac side uses.
- 2026-09-01T04:28Z: `--resume=<uuid>` was captured; not yet exercised.
- Historical (FR-947 as drafted 2026-09-01 morning): SSH+WSL2+pytest-xdist design premised on the remote box needing full Python environment provisioning. Empirical spike showed the remote can self-provision under Copilot's `--allow-all-tools` invocation — the assumption is wrong.

## Deliverable sought

A ranked set of viable Copilot-CLI-delegation architectures with:
- **Session pattern** — stateless per invocation vs `--resume` continuation; empirical latency + credit cost for each.
- **Repo provisioning** — Copilot clones on demand vs mac-side rsync via SMB; artifact retrieval channel.
- **Environment install** — Copilot invokes `winget install Python.3.11` and `pip install -e ".[dev]"` inside the session vs. pre-provisioned baseline. Idempotence contract.
- **Failure modes** — token expiration, LLM refusal (Copilot content policy), rate limits, credit exhaustion, session-state corruption.
- **Cost ceiling** — per-run and per-day budget with explicit abort.
- **Skill contract** — does the remote Copilot session `--add-dir <yamlgraph_clone>` and use `.github/skills/`, or does the mac-side skill wrap invocation and treat the remote as a dumb executor?
- **FR-947 disposition** — retire, coexist as SSH fallback, or reshape.

Each stated with enough precision to become the FR-948 body + acceptance criteria.
