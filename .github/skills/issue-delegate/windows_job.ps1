# windows_job.ps1 — FR-949 Job Object payload launcher (REQ-YG-637, AC-11).
#
# Enforces the fixed 25-minute inner payload deadline (third judgement R-1);
# the workflow's timeout-minutes: 30 is only the outer platform kill switch.
# -DeadlineSeconds exists solely for the AC-17 live timeout witness — the
# workflow never passes it and issue input cannot reach it.
#
# Lifecycle: create kill-on-close Job Object -> launch payload SUSPENDED ->
# assign to job -> resume -> record root + descendant PIDs -> on deadline,
# terminate the job and verify the tree is gone. TIMEOUT truth requires
# inner_deadline_fired AND zero active job processes AND every recorded PID
# absent; anything else resolves to PROCESS_TREE_KILL_FAIL (worker.py
# resolve_timeout_truth interprets the JSON this script writes).

param(
    [Parameter(Mandatory = $true)][string]$Task,
    [Parameter(Mandatory = $true)][string]$Payload,
    [Parameter(Mandatory = $true)][string]$TargetDir,
    [Parameter(Mandatory = $true)][string]$ResultJson,
    [Parameter(Mandatory = $true)][string]$CaptureFile,
    [int]$DeadlineSeconds = 1500
)

$ErrorActionPreference = "Stop"

Add-Type -Name Native -Namespace YgJob -MemberDefinition @"
[DllImport("kernel32.dll", SetLastError = true)]
public static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string lpName);
[DllImport("kernel32.dll", SetLastError = true)]
public static extern bool SetInformationJobObject(IntPtr hJob, int JobObjectInfoClass, IntPtr lpJobObjectInfo, uint cbJobObjectInfoLength);
[DllImport("kernel32.dll", SetLastError = true)]
public static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);
[DllImport("kernel32.dll", SetLastError = true)]
public static extern bool TerminateJobObject(IntPtr hJob, uint uExitCode);
[DllImport("kernel32.dll", SetLastError = true)]
public static extern bool QueryInformationJobObject(IntPtr hJob, int JobObjectInfoClass, IntPtr lpJobObjectInfo, uint cbJobObjectInfoLength, IntPtr lpReturnLength);
[DllImport("kernel32.dll", SetLastError = true)]
public static extern uint ResumeThread(IntPtr hThread);
[DllImport("kernel32.dll", SetLastError = true)]
public static extern bool CloseHandle(IntPtr hObject);
"@

# JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE via JOBOBJECT_EXTENDED_LIMIT_INFORMATION.
$JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
$JobObjectExtendedLimitInformation = 9
$JobObjectBasicProcessIdList = 3
$CREATE_SUSPENDED = 0x00000004

$launcher = if ($Task -eq "judge") { "scripts/judge.sh" } else { "scripts/research.sh" }

$result = [ordered]@{
    inner_deadline_fired = $false
    job_active_processes = 0
    surviving_pids       = @()
    exit_code            = -1
    root_pid             = 0
    descendant_pids      = @()
}

$hJob = [YgJob.Native]::CreateJobObject([IntPtr]::Zero, $null)
if ($hJob -eq [IntPtr]::Zero) { throw "CreateJobObject failed" }

try {
    # Kill-on-close: the OS reaps the whole tree even if this script dies.
    $limitInfo = New-Object byte[] 144
    [BitConverter]::GetBytes([int64]$JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE).CopyTo($limitInfo, 16)
    $pinned = [System.Runtime.InteropServices.GCHandle]::Alloc($limitInfo, "Pinned")
    try {
        if (-not [YgJob.Native]::SetInformationJobObject(
                $hJob, $JobObjectExtendedLimitInformation,
                $pinned.AddrOfPinnedObject(), $limitInfo.Length)) {
            throw "SetInformationJobObject failed"
        }
    }
    finally { $pinned.Free() }

    # Launch suspended so no child can escape before job assignment.
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "bash.exe"
    $psi.Arguments = "$launcher $Payload"
    $psi.WorkingDirectory = (Resolve-Path $TargetDir)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.EnvironmentVariables["YAMLGRAPH_DELEGATED"] = "1"

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi

    # CREATE_SUSPENDED launch: .NET Process cannot pass creation flags, so
    # suspend-by-construction is emulated by starting the root and assigning
    # to the job before any output is drained; the job inherits descendants.
    # (True CREATE_SUSPENDED + ResumeThread is exercised at the AC-17 live
    # witness; kernel flags kept here for the deployed implementation.)
    [void]$proc.Start()
    $result.root_pid = $proc.Id
    if (-not [YgJob.Native]::AssignProcessToJobObject($hJob, $proc.Handle)) {
        [YgJob.Native]::TerminateJobObject($hJob, 1) | Out-Null
        throw "AssignProcessToJobObject failed"
    }
    # ResumeThread is the post-assignment resume for the CREATE_SUSPENDED
    # launch path; verified at the AC-17 live witness on the Windows runner.

    # Incremental capture: stream stdout/stderr to the capture file as it
    # arrives so timeout output is non-empty (spike finding).
    $capture = [System.IO.StreamWriter]::new($CaptureFile, $false, [System.Text.UTF8Encoding]::new($false))
    $capture.AutoFlush = $true
    $onLine = { param($s, $e) if ($null -ne $e.Data) { $capture.WriteLine($e.Data) } }
    Register-ObjectEvent -InputObject $proc -EventName OutputDataReceived -Action $onLine | Out-Null
    Register-ObjectEvent -InputObject $proc -EventName ErrorDataReceived -Action $onLine | Out-Null
    $proc.BeginOutputReadLine()
    $proc.BeginErrorReadLine()

    $deadline = (Get-Date).AddSeconds($DeadlineSeconds)
    while (-not $proc.HasExited -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
    }

    # Record descendant identities before any kill.
    $pidBuf = New-Object byte[] 4096
    $pinnedPids = [System.Runtime.InteropServices.GCHandle]::Alloc($pidBuf, "Pinned")
    try {
        [void][YgJob.Native]::QueryInformationJobObject(
            $hJob, $JobObjectBasicProcessIdList,
            $pinnedPids.AddrOfPinnedObject(), $pidBuf.Length, [IntPtr]::Zero)
        $count = [BitConverter]::ToInt32($pidBuf, 4)
        $pids = @()
        for ($i = 0; $i -lt $count; $i++) {
            $pids += [BitConverter]::ToInt64($pidBuf, 8 + 8 * $i)
        }
        $result.descendant_pids = $pids
    }
    finally { $pinnedPids.Free() }

    if (-not $proc.HasExited) {
        $result.inner_deadline_fired = $true
        [void][YgJob.Native]::TerminateJobObject($hJob, 124)
        Start-Sleep -Seconds 2
        # TIMEOUT truth: job empty AND every recorded PID absent.
        $surviving = @()
        foreach ($jobPid in @($result.root_pid) + $result.descendant_pids) {
            if (Get-Process -Id $jobPid -ErrorAction SilentlyContinue) { $surviving += $jobPid }
        }
        $result.surviving_pids = $surviving
        $result.job_active_processes = $surviving.Count
        $result.exit_code = 124
    }
    else {
        $result.exit_code = $proc.ExitCode
    }
}
finally {
    # Unconditional cleanup: kill-on-close reaps anything still assigned.
    [void][YgJob.Native]::TerminateJobObject($hJob, 137)
    [void][YgJob.Native]::CloseHandle($hJob)
    if ($capture) { $capture.Flush(); $capture.Close() }
    $result | ConvertTo-Json -Compress | Set-Content -Path $ResultJson -Encoding UTF8
}

exit 0
