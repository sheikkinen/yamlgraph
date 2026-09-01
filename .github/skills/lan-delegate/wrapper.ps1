# FR-948 lan-delegate remote wrapper (REQ-YG-636).
#
# Fixed committed artifact. Pure ASCII (PS 5.1 codepage constraint).
# No caller-controlled interpolation into the script body.
#
# Contract (per feature-requests/FR-948-lan-copilot-delegation.md sect 5):
#   - Parameters bound by pypsrp.add_parameter, NEVER interpolated.
#   - Non-LLM preflight before Copilot invocation (git, node major>=22,
#     copilot CLI, canonical clone contains $LocalSha, worktree free,
#     SMB dest free).
#   - Create disposable detached git worktree.
#   - Start Copilot via Start-Job so $Prompt survives as ONE argv value
#     and stdout/stderr capture stays in memory (never redirected to
#     filesystem via -RedirectStandardOutput).
#   - Enforce wrapper-owned wall-clock deadline. On expiry, taskkill /T /F
#     the tracked process tree; typed PROCESS_TREE_KILL_FAIL if the kill
#     command itself fails.
#   - Redact literal $Token bytes from captured output IN MEMORY before
#     any filesystem write.
#   - Byte-scan every candidate artifact for the token before copying to
#     the SMB drop; skip token-matching files with TOKEN_LEAK_DETECTED.
#   - Cleanup (worktree remove, env clear) always runs in an outer finally.
#   - Emit exactly one JSON summary matching WrapperJsonSummary.
#
# NOT authorized: git clone, git fetch, package install, service mutation,
# firewall / group mutation, WSL install, source upload from mac, resume.

param(
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][string]$Prompt,
    [Parameter(Mandatory=$true)][string]$RunId,
    [Parameter(Mandatory=$true)][int]$TimeoutS,
    [Parameter(Mandatory=$true)][string]$LocalSha,
    [Parameter(Mandatory=$true)][double]$MaxReportedCredits
)

# --- constants ---------------------------------------------------------------
chcp 65001 | Out-Null
Set-ExecutionPolicy Bypass -Scope Process -Force
$ErrorActionPreference = 'Continue'   # explicit handling per phase

$MAX_CAPTURE_BYTES = 4 * 1024 * 1024
$CANONICAL_CLONE   = 'C:\Users\copilot\yamlgraph'
$WORKTREE_ROOT     = 'C:\Users\copilot\yamlgraph-runs'
$SMB_DROP_ROOT     = 'C:\Images\yamlgraph-delegations'
$COPILOT_CMD       = 'C:\Program Files\nodejs\copilot.ps1'

$worktreePath = Join-Path $WORKTREE_ROOT $RunId
$smbDest      = Join-Path $SMB_DROP_ROOT $RunId
$deletedOut   = 'delegate-out'   # ASCII, no leading dot; matches AC-11 relative-path expectation

# --- helpers -----------------------------------------------------------------
function New-FieldError($field, $message, $type) {
    return @{ field = $field; message = $message; error_type = $type }
}

function Test-ToolInfo($cmdName, [scriptblock]$versionFn) {
    $cmd = Get-Command $cmdName -EA SilentlyContinue
    if ($null -eq $cmd) {
        return @{
            present = $false; path = $null; version = $null;
            error   = (New-FieldError $cmdName "$cmdName not on PATH" 'absent')
        }
    }
    $ver = $null
    try { $ver = (& $versionFn 2>&1 | Select-Object -First 1) } catch { $ver = $null }
    return @{
        present = $true; path = $cmd.Source;
        version = if ($null -eq $ver) { $null } else { [string]$ver };
        error   = $null
    }
}

function Redact-Bytes([byte[]]$haystack, [byte[]]$needle, [byte[]]$replacement) {
    if ($null -eq $needle -or $needle.Length -eq 0) { return $haystack }
    $hLen = $haystack.Length; $nLen = $needle.Length
    if ($hLen -lt $nLen) { return $haystack }
    $result = New-Object 'System.Collections.Generic.List[byte]'
    $i = 0
    while ($i -le ($hLen - $nLen)) {
        $match = $true
        for ($j = 0; $j -lt $nLen; $j++) {
            if ($haystack[$i + $j] -ne $needle[$j]) { $match = $false; break }
        }
        if ($match) {
            $result.AddRange([byte[]]$replacement)
            $i += $nLen
        } else {
            $result.Add($haystack[$i]); $i++
        }
    }
    for (; $i -lt $hLen; $i++) { $result.Add($haystack[$i]) }
    return $result.ToArray()
}

# --- state -------------------------------------------------------------------
$startedAt   = Get-Date
$errors      = @()
$statuses    = @()
$prereqs     = $null
$remoteSha   = $null
$copilotExit = $null
$timedOut    = $false
$credits     = $null
$tokensUp    = $null
$tokensDown  = $null
$artifacts   = @()
$artifactRoot = $null

$tokenBytes    = [System.Text.Encoding]::UTF8.GetBytes($Token)
$replacement   = [System.Text.Encoding]::UTF8.GetBytes('<TOKEN>')

try {
    # --- preflight -----------------------------------------------------------
    $gitInfo     = Test-ToolInfo 'git'     { git --version }
    $nodeInfo    = Test-ToolInfo 'node'    { node --version }
    $copilotInfo = Test-ToolInfo 'copilot' { & $COPILOT_CMD --version }

    $nodeMajor = 0
    if ($nodeInfo.present -and $nodeInfo.version -match 'v(\d+)') {
        $nodeMajor = [int]$Matches[1]
    }
    if ($nodeInfo.present -and $nodeMajor -lt 22) {
        $nodeInfo.error = (New-FieldError 'node' "node major $nodeMajor < 22" 'version_too_low')
    }

    $cloneExists  = Test-Path (Join-Path $CANONICAL_CLONE '.git')
    $containsSha  = $null
    if ($cloneExists) {
        & git -C $CANONICAL_CLONE cat-file -e $LocalSha 2>&1 | Out-Null
        $containsSha = ($LASTEXITCODE -eq 0)
    }
    $repoInfo = @{
        path = $CANONICAL_CLONE; exists = $cloneExists;
        contains_sha = $containsSha; error = $null
    }
    if (-not $cloneExists) {
        $repoInfo.error = (New-FieldError 'canonical_clone' "no .git at $CANONICAL_CLONE" 'absent')
    } elseif ($containsSha -ne $true) {
        $repoInfo.error = (New-FieldError 'canonical_clone' "sha $LocalSha not present; run git fetch --all" 'malformed')
    }

    $worktreeFree = -not (Test-Path $worktreePath)
    $smbFree      = -not (Test-Path $smbDest)

    $prereqs = @{
        git = $gitInfo; node = $nodeInfo; copilot = $copilotInfo;
        canonical_clone = $repoInfo;
        run_worktree_free = $worktreeFree;
        smb_destination_free = $smbFree;
        errors = @()
    }
    foreach ($t in @($gitInfo, $nodeInfo, $copilotInfo)) {
        if ($null -ne $t.error) { $prereqs.errors += $t.error }
    }
    if ($null -ne $repoInfo.error) { $prereqs.errors += $repoInfo.error }
    if (-not $worktreeFree) { $prereqs.errors += (New-FieldError 'run_worktree_free' "$worktreePath already exists" 'path_taken') }
    if (-not $smbFree)      { $prereqs.errors += (New-FieldError 'smb_destination_free' "$smbDest already exists" 'path_taken') }

    if ($prereqs.errors.Count -gt 0) {
        $statuses += 'PREFLIGHT_FAIL'
        return
    }

    # --- worktree create -----------------------------------------------------
    New-Item -ItemType Directory -Path $WORKTREE_ROOT -Force -EA SilentlyContinue | Out-Null
    & git -C $CANONICAL_CLONE worktree add --detach $worktreePath $LocalSha 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $statuses += 'WORKTREE_ADD_FAIL'
        $errors += (New-FieldError 'worktree_add' "git worktree add exit=$LASTEXITCODE" 'unknown')
        return
    }
    $remoteSha = (& git -C $worktreePath rev-parse HEAD 2>&1 | Select-Object -First 1)

    # --- output directory ----------------------------------------------------
    $outDir = Join-Path $worktreePath $deletedOut
    try {
        New-Item -ItemType Directory -Path $outDir -Force -EA Stop | Out-Null
    } catch {
        $statuses += 'OUTPUT_DIR_CREATE_FAIL'
        $errors += (New-FieldError 'output_dir' $_.Exception.Message 'access_denied')
        return
    }

    # --- write prompt to a file inside the worktree ------------------------
    # Windows argv splits multi-line strings across whitespace boundaries even
    # with quoting; the CLI's `-p <text>` cannot receive newlines reliably.
    # Solution: land the full prompt as a file in the delegated tree and pass a
    # one-line pointer as -p. cwd=$worktreePath (below) makes the relative
    # path resolve.
    $promptDir = Join-Path $worktreePath '.lan-delegate'
    New-Item -ItemType Directory -Path $promptDir -Force -EA SilentlyContinue | Out-Null
    $promptFile = Join-Path $promptDir 'prompt.md'
    [System.IO.File]::WriteAllBytes($promptFile, [System.Text.Encoding]::UTF8.GetBytes($Prompt))
    $pointerPrompt = 'Read .lan-delegate/prompt.md relative to your current working directory and follow its instructions exactly. Do not restate or summarise the instructions.'

    # --- start copilot in a Job (in-memory capture, argv preserved) ---------
    $job = Start-Job -ArgumentList $Token, $pointerPrompt, $worktreePath -ScriptBlock {
        param($T, $P, $W)
        $env:GH_TOKEN = $T
        $env:COPILOT_ALLOW_ALL = '1'
        $env:YAMLGRAPH_LAN_DELEGATED = '1'
        # cwd=$W so `.github/skills/*/SKILL.md` and `.lan-delegate/prompt.md` resolve;
        # --add-dir alone grants access, not cwd.
        Set-Location -Path $W
        # Single-line ASCII prompt: argv-safe on Windows.
        & 'C:\Program Files\nodejs\copilot.ps1' -p $P --allow-all-tools --add-dir $W 2>&1
        "COPILOT_EXIT_CODE=$LASTEXITCODE"
    }

    $completed = Wait-Job -Job $job -Timeout $TimeoutS
    $captured  = @()

    if ($null -eq $completed) {
        # --- deadline hit: taskkill /T /F on every process spawned after startedAt ---
        $timedOut = $true
        $victims = Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object {
            $_.Name -match '^(node|copilot|powershell|cmd)\.exe$' -and
            $_.CreationDate -gt $startedAt
        }
        $killOk = $true
        foreach ($v in $victims) {
            & taskkill /PID $v.ProcessId /T /F 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) { $killOk = $false }
        }
        Stop-Job -Job $job -EA SilentlyContinue
        if ($killOk) {
            $statuses += 'TIMEOUT'
        } else {
            $statuses += 'PROCESS_TREE_KILL_FAIL'
            $errors += (New-FieldError 'taskkill' "one or more taskkill invocations returned non-zero" 'unknown')
        }
        $captured = Receive-Job -Job $job -Keep -EA SilentlyContinue
    } else {
        $captured = Receive-Job -Job $job -EA SilentlyContinue
    }
    Remove-Job -Job $job -Force -EA SilentlyContinue

    # --- capture size enforcement -------------------------------------------
    $capturedText = ($captured -join "`n")
    $capturedBytes = [System.Text.Encoding]::UTF8.GetBytes($capturedText)
    if ($capturedBytes.Length -gt $MAX_CAPTURE_BYTES) {
        # oversized capture; kill anything still alive, mark status.
        $victims2 = Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object {
            $_.Name -match '^(node|copilot)\.exe$' -and $_.CreationDate -gt $startedAt
        }
        foreach ($v in $victims2) { & taskkill /PID $v.ProcessId /T /F 2>&1 | Out-Null }
        $statuses += 'OUTPUT_CAPTURE_FAIL'
        $capturedText = $capturedText.Substring(0, [Math]::Min($capturedText.Length, $MAX_CAPTURE_BYTES))
        $capturedBytes = [System.Text.Encoding]::UTF8.GetBytes($capturedText)
    }

    # --- redact token bytes IN MEMORY before ANY filesystem write -----------
    $redactedBytes = Redact-Bytes -haystack $capturedBytes -needle $tokenBytes -replacement $replacement
    $redactedText  = [System.Text.Encoding]::UTF8.GetString($redactedBytes)

    # --- parse exit code, credits, tokens from redacted text ----------------
    $exitMatch = [regex]::Match($redactedText, 'COPILOT_EXIT_CODE=(-?\d+)')
    if ($exitMatch.Success) { $copilotExit = [int]$exitMatch.Groups[1].Value }
    if (($copilotExit -ne 0) -and ($copilotExit -ne $null) -and (-not $timedOut)) {
        $statuses += 'COPILOT_NONZERO'
    }

    $creditMatch = [regex]::Match($redactedText, 'AI Credits\s+(\d+(?:\.\d+)?)')
    if ($creditMatch.Success) {
        $credits = [double]$creditMatch.Groups[1].Value
        if ($credits -gt $MaxReportedCredits) { $statuses += 'CREDIT_FAIL_HIGH' }
    } elseif (-not $timedOut) {
        # Only flag unparseable credits on a successful run; timeouts didn't get to emit them.
        $statuses += 'CREDIT_FAIL_UNPARSEABLE'
    }

    $tokUpMatch = [regex]::Match($redactedText, 'Tokens\s+.\s+([\d.]+)k')
    if ($tokUpMatch.Success) {
        $tokensUp = [int]([double]$tokUpMatch.Groups[1].Value * 1000)
    }
    $tokDownMatch = [regex]::Match($redactedText, 'Tokens\s+.\s+[\d.]+k[^|]+.[\s]+(\d+)')
    if ($tokDownMatch.Success) {
        $tokensDown = [int]$tokDownMatch.Groups[1].Value
    }

    # --- byte-scan artifacts + copy to SMB ---------------------------------
    New-Item -ItemType Directory -Path $smbDest -Force -EA SilentlyContinue | Out-Null
    $artifactRoot = "\\$env:COMPUTERNAME\Images\yamlgraph-delegations\$RunId"
    $candidates = Get-ChildItem -Path $outDir -Recurse -File -EA SilentlyContinue
    foreach ($f in $candidates) {
        $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
        # byte-scan (naive but exact)
        $tainted = $false
        if ($bytes.Length -ge $tokenBytes.Length) {
            for ($i = 0; $i -le ($bytes.Length - $tokenBytes.Length); $i++) {
                $m = $true
                for ($j = 0; $j -lt $tokenBytes.Length; $j++) {
                    if ($bytes[$i + $j] -ne $tokenBytes[$j]) { $m = $false; break }
                }
                if ($m) { $tainted = $true; break }
            }
        }
        if ($tainted) {
            $statuses += 'TOKEN_LEAK_DETECTED'
            $rel = $f.FullName.Substring($outDir.Length).TrimStart('\','/').Replace('\','/')
            $errors += (New-FieldError "artifact:$rel" "literal GH_TOKEN bytes detected; not copied" 'unknown')
            continue
        }
        $rel = $f.FullName.Substring($outDir.Length).TrimStart('\','/')
        $dst = Join-Path $smbDest $rel
        $dstDir = Split-Path -Parent $dst
        if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force -EA SilentlyContinue | Out-Null }
        try {
            Copy-Item -Path $f.FullName -Destination $dst -Force -EA Stop
            $artifacts += ($rel -replace '\\','/')
        } catch {
            $statuses += 'ARTIFACT_COPY_FAIL'
            $errors += (New-FieldError "artifact_copy:$rel" $_.Exception.Message 'unknown')
        }
    }

    # --- write redacted stdout/stderr next to artifacts ----------------------
    $redactedLog = Join-Path $smbDest 'stdout.log'
    [System.IO.File]::WriteAllBytes($redactedLog, $redactedBytes)
    # We captured stdout+stderr merged (`2>&1`); provide an empty stderr placeholder
    # for schema symmetry (delegate.py's LanDelegationResult expects both).
    [System.IO.File]::WriteAllBytes((Join-Path $smbDest 'stderr.log'), (New-Object byte[] 0))

} finally {
    # --- cleanup: worktree remove, env clear -------------------------------
    if (Test-Path $worktreePath) {
        & git -C $CANONICAL_CLONE worktree remove --force $worktreePath 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0 -and (Test-Path $worktreePath)) {
            $statuses += 'WORKTREE_CLEANUP_FAIL'
            $errors += (New-FieldError 'worktree_cleanup' "worktree remove exit=$LASTEXITCODE" 'unknown')
            # Belt-and-braces: force-delete the tree if git left it behind.
            Remove-Item -Path $worktreePath -Recurse -Force -EA SilentlyContinue
        }
    }
    Remove-Item Env:GH_TOKEN -EA SilentlyContinue
    Remove-Item Env:COPILOT_ALLOW_ALL -EA SilentlyContinue
    Remove-Item Env:YAMLGRAPH_LAN_DELEGATED -EA SilentlyContinue
}

# --- summary emit ------------------------------------------------------------
if ($statuses.Count -eq 0) { $statuses += 'OK' }

# Precedence resolution matches models.py _PRECEDENCE (delegate.py verifies).
$precedence = @(
    'TOKEN_LEAK_DETECTED','PROCESS_TREE_KILL_FAIL','WRAPPER_JSON_MALFORMED',
    'OUTPUT_CAPTURE_FAIL','TIMEOUT','WORKTREE_ADD_FAIL','OUTPUT_DIR_CREATE_FAIL',
    'WRAPPER_EXEC_FAIL','WINRM_AUTH_FAIL','WINRM_CONNECT_FAIL',
    'WINRM_TRANSPORT_TIMEOUT','PREFLIGHT_FAIL','SMB_DEST_EXISTS','COPILOT_NONZERO',
    'CREDIT_FAIL_HIGH','CREDIT_FAIL_UNPARSEABLE','ARTIFACT_COPY_FAIL',
    'WORKTREE_CLEANUP_FAIL','OK'
)
$statusRank = @{}
for ($i = 0; $i -lt $precedence.Length; $i++) { $statusRank[$precedence[$i]] = $i }
$finalStatus = ($statuses | Sort-Object { $statusRank[$_] } | Select-Object -First 1)

$elapsedS = ((Get-Date) - $startedAt).TotalSeconds

$summary = [ordered]@{
    prerequisites = $prereqs
    remote_sha    = $remoteSha
    remote_worktree = $worktreePath
    copilot_exit_code = $copilotExit
    delegation_policy_status = $finalStatus
    timed_out = $timedOut
    elapsed_s = [Math]::Round($elapsedS, 3)
    credits_reported = $credits
    tokens_up = $tokensUp
    tokens_down = $tokensDown
    artifacts = $artifacts
    artifact_root = $artifactRoot
    errors = $errors
}

# Emit exactly one JSON document on stdout for delegate.py to parse.
$summary | ConvertTo-Json -Depth 6 -Compress
