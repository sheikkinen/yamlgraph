# FR-948 Phase 2 spike evidence (sanitized, 2026-09-01)

Committed excerpts of the empirical spike that motivates FR-948. The
full raw log lived at `tmp/copilot-spike-phase2f.log` (untracked); every
claim in FR-948 that traces to the spike must trace to this file
instead. No credential material appears here.

## Environment

- Host: `Huutokauppakone.local` (192.168.50.172, ASUS ROG STRIX G15DK,
  AMD Ryzen 7 5800X 8C/16T, 24 GB RAM, NVIDIA RTX 3070, Windows 10.0.26200.0,
  Finnish locale).
- Remote runtime: Node.js v24.19.0 LTS (upgraded from 18.16.1 in this
  session via `winget install OpenJS.NodeJS.LTS --scope machine`), npm
  11.17.0, `@github/copilot` installed system-wide to
  `C:\Program Files\nodejs`.
- WinRM: HTTP 5985, `auth="negotiate"`, encryption mandatory,
  `HUUTOKAUPPAKONE\copilot` account (non-admin, `S-1-5-32-580` member).
- Auth: `GH_TOKEN` env-var, injected as a WinRM `param([string]$Token)`
  binding — never interpolated into script text.

## WinRM invocation shape (redacted)

```powershell
# Passed as pypsrp powershell.add_parameter("Token", ...), never in script literal.
param([Parameter(Mandatory=$true)][string]$Token, [string]$Stamp)
Set-ExecutionPolicy Bypass -Scope Process -Force
$env:GH_TOKEN = $Token
$env:COPILOT_ALLOW_ALL = '1'
$target = "C:\Images\phase2f-$Stamp.txt"
$prompt = "Use the shell to write the exact text 'ok $Stamp' to a new " +
          "file at $target. Only that. Then stop."
& 'C:\Program Files\nodejs\copilot.cmd' `
    -p $prompt `
    --allow-all-tools `
    --allow-all-paths           # <- REMOVED in the folded FR (R-4)
    2>&1
```

## Copilot CLI output tail (verbatim, no redaction needed)

```
● Create file with exact text (shell)
  │ New-Item -ItemType Directory -Force -Path C:\Images | Out-Null;
  │ Set-Content -Path 'C:\Images\phase2f-20260901T042852Z.txt'
  │ -Value 'ok 20260901T042852Z' -NoNewline
  └ 1 line…

Done — created C:\Images\phase2f-20260901T042852Z.txt with the text
`ok 20260901T042852Z`.

AI Credits 7.17 (7s)
Tokens     ↑ 51.4k (25.6k cached, 25.8k written) • ↓ 204
Resume     copilot --resume=0645de30-52dd-4dbb-b50e-066e625ae4e0
```

## Measurements

- **Copilot exit code**: 0
- **Wall-clock elapsed**: 11.0 s (WinRM connect to result received)
- **LLM inference time (reported by Copilot)**: 7 s
- **AI Credits (reported by Copilot)**: 7.17
- **Prompt tokens**: 51,400 (25,600 cached, 25,800 fresh)
- **Completion tokens**: 204
- **Resume ID captured** (unused in v1 per FR-948 R-3, retained here as
  historical evidence): `0645de30-52dd-4dbb-b50e-066e625ae4e0`

## Artifact content (verbatim)

Path: `\\HUUTOKAUPPAKONE\Images\phase2f-20260901T042852Z.txt` (mounted on
mac as `/Volumes/Images/phase2f-20260901T042852Z.txt`).

```
ok 20260901T042852Z
```

19 bytes. No newline. Contents match the prompt request exactly.

## What this spike proved (and did NOT prove)

**Proved**:
- WinRM + `param`-bound token + `copilot -p "..." --allow-all-tools`
  reaches the remote model, executes a shell tool, writes to the
  filesystem, exits cleanly.
- SMB `\\<host>\Images\` is a viable artifact-return channel.
- `GH_TOKEN` env-var auth survives WinRM's NETWORK logon session (the
  device-flow token stored in the interactive user profile did NOT — see
  earlier attempts in the same session).

**Did NOT prove** (and therefore not claimable in FR-948 without further
witness):
- Python or dependency self-provisioning on the remote (not exercised —
  the spike used only PowerShell built-in tools).
- Running an actual repository workload (a trivial file write is not a
  pytest run; the AC-17 live witness must exercise a real workload).
- Session `--resume` reuse across runs (captured, not exercised).
- Cost model for a heavier prompt (7.17 credits for 51k prompt tokens is
  cache-heavy; a fresh session with a real workload will cost more).
- `--add-dir` skill loading behavior (not exercised; belongs in AC-17).

## Session context

The spike ran in this exact conversation on 2026-09-01. Preceding
diagnostic steps: `Enable-PSRemoting` on remote, `copilot` local user +
`S-1-5-32-580` membership fix, Node 18 -> Node 24 upgrade, npm 9.5.1 ->
npm 11.17.0 upgrade (older npm couldn't resolve `@github/copilot` platform
optional deps), execution-policy bypass at process scope, argument-shape
fix (`&` operator instead of `Start-Process -ArgumentList`), env-var
auth after device-flow token failed on WinRM network logon.

All of the above are FR-945 (recon skill) or FR-948 (this FR) concerns.
None of the remediation steps involve mutating the yamlgraph repository
on either side.
