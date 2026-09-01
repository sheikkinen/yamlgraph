# install-runner.ps1 — FR-949 scripted C-7/C-8 (REQ-YG-637).
#
# Runs ONCE on the Windows worker host under the service account's session
# with a logged-in `gh` (gh auth status must succeed). Everything here is a
# scripted act with that logged-in user — no manual GitHub UI steps:
#   C-7: fetch a runner registration token via the API, download the Actions
#        runner, configure it --unattended --runasservice with the delegate
#        labels, and verify it comes up online.
#   C-8: provision DELEGATE_CHECKOUT_PAT on the comms repo from the
#        logged-in gh token (LAN yolo posture: the token's grant set IS the
#        target authorization boundary per amended O-1).
# The service logon password is typed at the console by Windows when the
# service is configured — never passed on the command line, never stored here.
#
# Usage (from an elevated Git Bash / PowerShell on the host):
#   powershell -ExecutionPolicy Bypass -File install-runner.ps1 `
#     [-CommsRepo sheikkinen/yamlgraph-delegation] [-RunnerDir C:\actions-runner]

param(
    [string]$CommsRepo = "sheikkinen/yamlgraph-delegation",
    [string]$RunnerDir = "C:\actions-runner",
    [string]$RunnerVersion = "2.319.1"
)

$ErrorActionPreference = "Stop"

function Assert-LastExit([string]$What) {
    if ($LASTEXITCODE -ne 0) { throw "$What failed (exit $LASTEXITCODE)" }
}

# --- preconditions -----------------------------------------------------------
gh auth status
Assert-LastExit "gh auth status (log in with 'gh auth login' first)"
git --version | Out-Null
Assert-LastExit "git"
bash --version | Out-Null
Assert-LastExit "Git Bash (required to run scripts/judge.sh and scripts/research.sh)"
copilot --version
Assert-LastExit "Copilot CLI (authenticate for the service account first)"

# --- C-8: provision the checkout credential from the logged-in gh ------------
# gh secret set encrypts client-side (libsodium) against the repo public key;
# the token's repo grant set is the sole target authorization boundary (O-1).
gh auth token | gh secret set DELEGATE_CHECKOUT_PAT --repo $CommsRepo
Assert-LastExit "gh secret set DELEGATE_CHECKOUT_PAT"

# --- C-7: download, register, and install the runner as a service ------------
if (-not (Test-Path $RunnerDir)) { New-Item -ItemType Directory -Path $RunnerDir | Out-Null }
Set-Location $RunnerDir

$archive = "actions-runner-win-x64-$RunnerVersion.zip"
if (-not (Test-Path $archive)) {
    Invoke-WebRequest `
        -Uri "https://github.com/actions/runner/releases/download/v$RunnerVersion/$archive" `
        -OutFile $archive
    Expand-Archive -Path $archive -DestinationPath . -Force
}

# Registration token: short-lived, minted by the logged-in gh — never stored.
$regToken = gh api -X POST "repos/$CommsRepo/actions/runners/registration-token" --jq .token
Assert-LastExit "registration-token API"

# --runasservice installs the Windows service; Windows prompts for the
# service logon at the console (interactive, deliberately not scripted).
.\config.cmd --unattended `
    --url "https://github.com/$CommsRepo" `
    --token $regToken `
    --name "huutokauppakone" `
    --labels "self-hosted,Windows,delegate" `
    --runasservice
Assert-LastExit "config.cmd"

# --- verify -------------------------------------------------------------------
Start-Sleep -Seconds 5
$svc = Get-Service -Name "actions.runner.*" | Select-Object -First 1
if (-not $svc -or $svc.Status -ne "Running") { throw "runner service not running" }

$online = gh api "repos/$CommsRepo/actions/runners" --jq `
    '[.runners[] | select(.status == "online")] | length'
if ([int]$online -lt 1) { throw "runner registered but not online" }

Write-Host "runner service installed and online; DELEGATE_CHECKOUT_PAT provisioned."
Write-Host "Remaining before live use: GATE C-2 comms-diff review, then AC-16/AC-17 witnesses."
